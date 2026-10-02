#!/usr/bin/env python3
"""End-to-end voice pipeline harness. Owner: P1b.

Exercises the real chain — microphone -> /transcribe -> whisper-1 -> /intent ->
/bill-delta — without needing the frontend.

    # no audio: does intent detection work?
    python scripts/test_voice.py --text "how much more for Magenta MAX"
    python scripts/test_voice.py --suite

    # your voice, live. This is the demo path.
    python scripts/test_voice.py --mic          (needs: pip install sounddevice)

    # a recorded file through the same path
    python scripts/test_voice.py --file ~/Desktop/memo.m4a

Needs uvicorn running. Run from the backend/ directory.

Audio is captured as 16 kHz mono PCM and wrapped in WAV using the stdlib
`wave` module. WAV is used rather than WebM because every segment must be a
standalone decodable file — a raw slice out of a WebM stream has no header and
Whisper rejects it.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import queue
import sys
import time
import wave
from pathlib import Path

import httpx
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.example")

API = os.getenv("VITE_API_BASE_URL", "http://localhost:8000")
SAMPLE_RATE = 16000

DIM, BOLD, GREEN, YELLOW, RED, CYAN, RESET = (
    "\033[2m", "\033[1m", "\033[32m", "\033[33m", "\033[31m", "\033[36m", "\033[0m"
)

SUITE = [
    "I was thinking about upgrading to the iPhone 16",
    "how much more would it be if I switch to Magenta MAX",
    "can I add a line for my daughter",
    "what's my trade in worth on this one",
    "and I was — yeah so is that the sixteen or",
    "is there any kind of discount going on right now",
    "why is my bill higher than last month",
    "I want to drop a line actually",
    "so my daughter's birthday is next week",
    "yeah",
    "okay that sounds good",
    "do you validate parking here",
]


# ── output ────────────────────────────────────────────────────────────────────

def _show_intent(result: dict | None) -> None:
    if not result:
        return
    topic = result.get("topic", "none")
    conf = result.get("confidence", 0.0)
    action = result.get("action", "none")
    colour = DIM if topic == "none" else GREEN
    print(f"  {colour}{topic:16}{RESET} conf={conf:<5} action={action}")

    details = result.get("details") or {}
    if details:
        print(f"{DIM}  details: {json.dumps(details)}{RESET}")

    surfaced = result.get("data_to_surface") or {}

    # The demo moment: customer asks the price question, the number appears.
    bill = surfaced.get("bill_delta")
    if bill:
        arrow = "↑" if bill["direction"] == "increase" else "↓" if bill["direction"] == "decrease" else "="
        print(f"  {CYAN}${bill['current_monthly_total']:.2f} -> "
              f"${bill['new_monthly_total']:.2f}  {arrow} ${bill['delta_dollars']:.2f}{RESET}")

        device = bill.get("device")
        if device:
            covered = "  fully covered by trade-in" if device["fully_covered"] else ""
            print(f"  {CYAN}{device['model']}: ${device['retail_price']:,.0f}"
                  f" − ${device['trade_in_value']:,.0f} trade-in"
                  f" − ${device['promo_credit']:,.0f} promo"
                  f"  =  ${device['monthly_payment']:.2f}/mo{covered}{RESET}")

        for promo in bill.get("promos_applied", []):
            cap = " (capped)" if promo.get("capped") else ""
            print(f"{DIM}  promo: {promo['name']} ${promo['applied']:,.2f}{cap}{RESET}")

        print(f"  {CYAN}{bill['explanation']}{RESET}")
    elif surfaced.get("bill_delta_error"):
        print(f"{DIM}  no delta: {surfaced['bill_delta_error'][:70]}{RESET}")

    other = {k: v for k, v in surfaced.items() if not k.startswith("bill_delta")}
    if other:
        keys = ", ".join(f"{k}({len(v) if isinstance(v, (list, dict)) else 1})"
                         for k, v in other.items())
        print(f"{DIM}  surfaced: {keys}{RESET}")


def _post_intent(transcript: str, customer_id: str) -> dict | None:
    try:
        r = httpx.post(f"{API}/intent",
                       json={"transcript": transcript, "customer_id": customer_id},
                       timeout=60)
    except Exception as exc:
        print(f"{RED}  backend unreachable at {API} — is uvicorn running?{RESET}")
        print(f"{DIM}  {exc}{RESET}")
        return None
    if r.status_code != 200:
        print(f"{RED}  {r.status_code} {r.text[:200]}{RESET}")
        return None
    return r.json()


def _post_audio(audio: bytes, filename: str, customer_id: str) -> dict | None:
    try:
        r = httpx.post(
            f"{API}/transcribe",
            files={"file": (filename, audio, "application/octet-stream")},
            data={"customer_id": customer_id},
            timeout=120,
        )
    except Exception as exc:
        print(f"{RED}  backend unreachable at {API}{RESET}\n{DIM}  {exc}{RESET}")
        return None
    if r.status_code != 200:
        print(f"{RED}  {r.status_code} {r.text[:250]}{RESET}")
        return None
    return r.json()


# ── modes ─────────────────────────────────────────────────────────────────────

def run_text(text: str, customer_id: str) -> None:
    print(f"\n{BOLD}{text}{RESET}")
    _show_intent(_post_intent(text, customer_id))


def run_suite(customer_id: str) -> None:
    print(f"{BOLD}Intent detection suite{RESET} {DIM}({len(SUITE)} utterances){RESET}\n")
    hits = 0
    started = time.time()
    for line in SUITE:
        print(f"{BOLD}{line}{RESET}")
        result = _post_intent(line, customer_id)
        if result is None:
            return
        if result.get("topic", "none") != "none":
            hits += 1
        _show_intent(result)
        print()
    elapsed = time.time() - started
    print(f"{BOLD}{hits}/{len(SUITE)} detected{RESET} in {elapsed:.1f}s "
          f"({elapsed / len(SUITE):.2f}s each)")
    print(f"{DIM}The last four are small talk — they SHOULD read 'none'.{RESET}")


def run_file(path: str, customer_id: str) -> None:
    audio = Path(path).expanduser()
    if not audio.exists():
        sys.exit(f"{RED}No such file: {audio}{RESET}")
    print(f"{DIM}Sending {audio.name} to {API}/transcribe...{RESET}\n")
    data = _post_audio(audio.read_bytes(), audio.name, customer_id)
    if not data:
        return
    print(f"{BOLD}{data['text']}{RESET}  {DIM}({data.get('duration_ms', 0)}ms){RESET}")
    _show_intent(data.get("intent"))
    if data.get("intent_error"):
        print(f"{RED}  intent error: {data['intent_error']}{RESET}")


def _to_wav(frames: bytes) -> bytes:
    """Wrap raw 16-bit mono PCM in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(frames)
    return buf.getvalue()


def _rms(frames: bytes) -> float:
    import array

    samples = array.array("h")
    samples.frombytes(frames)
    if not samples:
        return 0.0
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


def run_mic(customer_id: str, threshold: int, max_seconds: float,
            hang_seconds: float = 0.8) -> None:
    """Listen continuously, cutting on pauses rather than on a stopwatch.

    A fixed window is the wrong boundary for speech. "How much more would it be
    if I switch to Magenta MAX" straddles a 4-second cut, so the first segment
    ends at "...Magenta" and prices the wrong plan, while the tail arrives as
    "To Max. Max. Max." — Whisper looping on a fragment with no context.

    So: accumulate while there is sound, and flush once it has been quiet for
    `hang_seconds`. Boundaries land where the speaker actually paused. A hard
    `max_seconds` cap keeps a long monologue from buffering forever.
    """
    try:
        import sounddevice as sd
    except ImportError:
        sys.exit(f"{RED}Mic mode needs sounddevice:{RESET}  pip install sounddevice")

    blocks: queue.Queue[bytes] = queue.Queue()

    def on_audio(indata, _frames, _t, status):
        if status:
            print(f"{YELLOW}  {status}{RESET}")
        blocks.put(bytes(indata))

    BLOCK = 2000                                    # frames -> 125ms at 16kHz
    block_seconds = BLOCK / SAMPLE_RATE
    hang_blocks = max(1, int(hang_seconds / block_seconds))
    # Below roughly a second of actual speech there is not enough signal for a
    # reliable decode, and Whisper fills the gap with caption boilerplate.
    min_speech_blocks = max(1, int(1.0 / block_seconds))

    print(f"{BOLD}Listening.{RESET} {DIM}cutting on pauses -> {API}/transcribe "
          f"-> intent -> bill delta{RESET}")
    print(f'{DIM}Try: "how much more would it be if I switch to Magenta MAX"')
    print(f"Speak naturally, then pause. Ctrl-C to stop.{RESET}\n")

    buffer = bytearray()
    speech_blocks = 0
    quiet_blocks = 0
    armed = False           # have we heard speech since the last flush?
    showed_dots = False

    def flush() -> None:
        nonlocal buffer, speech_blocks, quiet_blocks, armed, showed_dots
        segment = bytes(buffer)
        buffer = bytearray()
        speech_blocks = quiet_blocks = 0
        armed = False

        if showed_dots:
            print()
            showed_dots = False

        started = time.time()
        data = _post_audio(_to_wav(segment), "chunk.wav", customer_id)
        if not data:
            return

        if not data.get("text"):
            # Show what was filtered rather than swallowing it — otherwise a
            # too-high gate looks identical to a broken mic.
            if data.get("discarded"):
                print(f"{DIM}  [{data.get('skipped')}] {data['discarded'][:66]}{RESET}")
            return

        print(f"{BOLD}{data['text']}{RESET}  {DIM}({time.time() - started:.1f}s){RESET}")
        _show_intent(data.get("intent"))
        if data.get("intent_error"):
            print(f"{RED}  intent error: {data['intent_error'][:90]}{RESET}")
        print()

    try:
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK,
                               dtype="int16", channels=1, callback=on_audio):
            while True:
                block = blocks.get()
                loud = _rms(block) >= threshold

                if loud:
                    armed = True
                    speech_blocks += 1
                    quiet_blocks = 0
                    buffer.extend(block)
                elif armed:
                    # Keep trailing quiet in the buffer — trimming it clips
                    # the final consonant, and "MAX" becomes "MA".
                    quiet_blocks += 1
                    buffer.extend(block)
                else:
                    print(f"{DIM}.{RESET}", end="", flush=True)
                    showed_dots = True
                    continue

                ended = armed and quiet_blocks >= hang_blocks and speech_blocks >= min_speech_blocks
                too_long = len(buffer) >= int(SAMPLE_RATE * max_seconds) * 2

                if ended or too_long:
                    if speech_blocks >= min_speech_blocks:
                        flush()
                    else:
                        buffer = bytearray()
                        speech_blocks = quiet_blocks = 0
                        armed = False
    except KeyboardInterrupt:
        print(f"\n{DIM}stopped{RESET}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="send one phrase to /intent")
    g.add_argument("--suite", action="store_true", help="run the built-in utterance set")
    g.add_argument("--file", help="send an audio file through /transcribe")
    g.add_argument("--mic", action="store_true", help="live mic through the full chain")
    p.add_argument("--customer", default="5550192", help="account id (default: Maria)")
    p.add_argument("--threshold", type=int, default=600,
                   help="mic loudness gate; lower if speech is missed, raise if "
                        "room noise triggers hallucinated transcripts")
    p.add_argument("--max-seconds", type=float, default=15.0,
                   help="hard cap on one utterance before forcing a flush")
    args = p.parse_args()

    if args.text:
        run_text(args.text, args.customer)
    elif args.suite:
        run_suite(args.customer)
    elif args.file:
        run_file(args.file, args.customer)
    elif args.mic:
        run_mic(args.customer, args.threshold, args.max_seconds)


if __name__ == "__main__":
    main()
