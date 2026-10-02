"""Speech-to-text via the T-Mobile LLM gateway. Owner: P1b.

Replaces the Deepgram path. `api.deepgram.com` is blocked by the corporate
proxy (CATEGORY_DENIED: Generative AI and ML Applications), and huggingface.co
is blocked under the same rule, which also rules out running Whisper locally.

`llm.t-mobile.com` is allowlisted and serves `openai/whisper-1`. Measured round
trip on a ~10s clip is about 1.4s, so 3-5 second chunks transcribe comfortably
faster than they record.

Trade-off vs Deepgram: this is batch, not streaming. There are no interim
results, so the browser records fixed-length chunks and posts each one. The
dashboard lands a beat behind the conversation instead of updating mid-word.
"""

from __future__ import annotations

import os
import re
import time

import httpx

# Chunks below this are almost certainly silence or a click. Transcribing them
# wastes a round trip and tends to return hallucinated filler like "Thank you."
MIN_AUDIO_BYTES = 2_000

# Whisper was trained on YouTube captions, so near-silence makes it emit caption
# boilerplate rather than nothing. These are the well-known offenders — they
# arrive with high confidence and read like real speech, so they have to be
# filtered by content, not by score.
_HALLUCINATIONS = (
    "beadaholique",
    "thanks for watching",
    "thank you for watching",
    "subtitles by",
    "subtitled by",
    "transcription by",
    "amara.org",
    "please subscribe",
    "like and subscribe",
    "see you next time",
    "copyright",
    "©",
    "www.",
    ".com for all of your",
)

# Bare filler that carries no intent. Cheaper to drop here than to spend an LLM
# call discovering it means nothing.
_FILLER = {
    "", "you", "yeah", "yes", "no", "ok", "okay", "mm", "mmhmm", "mhm", "uh",
    "um", "hmm", "so", "bye", "thank you", "thanks", "the", "oh",
}

_WORD = re.compile(r"[a-z0-9']+")


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _is_prompt_echo(text: str, prompt: str | None) -> bool:
    """Detect the model parroting its own bias prompt.

    Given low-content audio and a `prompt`, Whisper sometimes returns the
    prompt itself. It looks exactly like a real utterance — "Plans to upgrade,
    trade-in, add a line, promotion, monthly bill, autopay" — but the customer
    never said it.
    """
    if not prompt:
        return False
    said = set(_tokens(text))
    if len(said) < 3:
        return False
    biased = set(_tokens(prompt))
    return len(said & biased) / len(said) > 0.75


def _is_looping(text: str) -> bool:
    """Detect Whisper stuck in a loop, e.g. "Max. Max. Max. Max."

    Happens on clipped fragments where the model has too little context and
    falls into repeating whatever it last decoded. Consecutive repetition is
    the reliable signal — a low unique-word ratio alone flags short legitimate
    sentences too.
    """
    words = _tokens(text)
    if len(words) < 3:
        return False

    # "no no no, that's not what I meant" is real speech, so a repeated run
    # only counts as a loop when it dominates the utterance.
    run = 1
    longest = 1
    for prev, cur in zip(words, words[1:]):
        run = run + 1 if cur == prev else 1
        longest = max(longest, run)

    if longest >= 3 and longest / len(words) >= 0.5:
        return True

    return len(set(words)) / len(words) < 0.35


def is_hallucination(text: str, prompt: str | None = None) -> str | None:
    """Return a reason to discard this transcript, or None to keep it."""
    stripped = (text or "").strip()
    lowered = stripped.lower().strip(".!? ")

    if lowered in _FILLER:
        return "filler"
    if any(marker in lowered for marker in _HALLUCINATIONS):
        return "caption_boilerplate"
    if _is_prompt_echo(stripped, prompt):
        return "prompt_echo"
    if _is_looping(stripped):
        return "looping"
    return None


class TranscriptionError(RuntimeError):
    pass


class TranscriptionService:
    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = (os.getenv("ANTHROPIC_BASE_URL") or "https://llm.t-mobile.com").rstrip("/")
        self.model = os.getenv("TRANSCRIPTION_MODEL", "openai/whisper-1")

    async def transcribe(
        self,
        audio: bytes,
        filename: str = "chunk.webm",
        *,
        language: str = "en",
        prompt: str | None = None,
    ) -> dict:
        """Transcribe one audio chunk.

        `prompt` biases decoding toward expected vocabulary. Passing plan and
        device names measurably improves accuracy on terms Whisper would
        otherwise mangle — "Magenta MAX" tends to come back as "Magenta Max"
        or "magenta mask" without it.
        """
        if len(audio) < MIN_AUDIO_BYTES:
            return {"text": "", "skipped": "too_short", "duration_ms": 0}

        started = time.perf_counter()
        data = {"model": self.model, "language": language}
        if prompt:
            data["prompt"] = prompt

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": (filename, audio, "application/octet-stream")},
                    data=data,
                )
        except httpx.HTTPError as exc:
            raise TranscriptionError(f"gateway unreachable: {exc}") from exc

        if response.status_code != 200:
            raise TranscriptionError(f"{response.status_code}: {response.text[:300]}")

        try:
            text = response.json().get("text", "")
        except ValueError:
            text = response.text

        text = (text or "").strip()
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        reason = is_hallucination(text, prompt)
        if reason:
            # Return the discarded text so callers can log it, but blank `text`
            # so nothing downstream acts on words nobody said.
            return {"text": "", "skipped": reason, "discarded": text,
                    "duration_ms": elapsed_ms, "model": self.model}

        return {"text": text, "duration_ms": elapsed_ms, "model": self.model}


# Domain vocabulary to bias decoding. Keep in sync with mock/plans.json.
#
# Deliberately short: the longer this is, the more of it Whisper regurgitates
# when the audio is mostly silence. Proper nouns are what actually need the
# help — "Magenta MAX" decodes as "magenta mask" without them — so generic
# topic words have been dropped.
RETAIL_PROMPT = (
    "T-Mobile store. Plans: Essentials, Magenta, Magenta MAX, Go5G Plus. "
    "Devices: iPhone 16 Pro, Galaxy S24."
)
