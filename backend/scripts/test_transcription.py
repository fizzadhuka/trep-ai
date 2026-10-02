#!/usr/bin/env python3
"""Validate the transcription path on the T-Mobile gateway. Owner: P1b.

Deepgram is blocked by the corporate proxy (CATEGORY_DENIED: Generative AI),
and so is HuggingFace, which rules out local Whisper too. The gateway at
llm.t-mobile.com is allowlisted and serves openai/whisper-1, so that becomes
the transcription path.

No microphone or recording needed — this generates speech with the gateway's
TTS model, then transcribes it back, exercising the full audio round trip.

    python scripts/test_transcription.py                 # synthesize + transcribe
    python scripts/test_transcription.py --file a.m4a    # transcribe your own audio
    python scripts/test_transcription.py --probe         # what audio models respond?
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / ".env.example")

KEY = os.getenv("ANTHROPIC_API_KEY", "")
BASE = (os.getenv("ANTHROPIC_BASE_URL") or "https://llm.t-mobile.com").rstrip("/")
STT_MODEL = os.getenv("TRANSCRIPTION_MODEL", "openai/whisper-1")
TTS_MODEL = os.getenv("TTS_MODEL", "openai/tts-1")

BOLD, DIM, GREEN, RED, RESET = "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[0m"
AUTH = {"Authorization": f"Bearer {KEY}"}

# What a customer actually says in a store — the thing intent detection has to catch.
SAMPLE = (
    "Hi, I was thinking about upgrading to the iPhone 16. "
    "How much more would it be per month if I switch to Magenta MAX? "
    "And can I add a line for my daughter?"
)


def synthesize(text: str, out: Path) -> Path:
    print(f"{DIM}Synthesizing speech via {TTS_MODEL}...{RESET}")
    r = httpx.post(
        f"{BASE}/v1/audio/speech",
        headers=AUTH,
        json={"model": TTS_MODEL, "input": text, "voice": "alloy"},
        timeout=90,
    )
    if r.status_code != 200:
        sys.exit(f"{RED}TTS failed {r.status_code}: {r.text[:400]}{RESET}")
    out.write_bytes(r.content)
    print(f"{DIM}  wrote {out} ({len(r.content):,} bytes){RESET}\n")
    return out


def transcribe(path: Path) -> str:
    print(f"{DIM}Transcribing via {STT_MODEL}...{RESET}")
    started = time.time()
    with path.open("rb") as fh:
        r = httpx.post(
            f"{BASE}/v1/audio/transcriptions",
            headers=AUTH,
            files={"file": (path.name, fh, "application/octet-stream")},
            data={"model": STT_MODEL},
            timeout=120,
        )
    elapsed = time.time() - started
    if r.status_code != 200:
        sys.exit(f"{RED}Transcription failed {r.status_code}: {r.text[:400]}{RESET}")
    print(f"{DIM}  {elapsed:.1f}s{RESET}\n")
    try:
        return r.json().get("text", "")
    except Exception:
        return r.text


def probe() -> None:
    """Which audio models actually respond? Tells us if streaming is available."""
    print(f"{BOLD}Probing audio models{RESET}\n")
    r = httpx.get(f"{BASE}/v1/models", headers=AUTH, timeout=20)
    models = [m["id"] for m in r.json().get("data", [])]
    audio = [m for m in models if any(k in m.lower() for k in ("whisper", "tts", "audio", "realtime"))]
    for m in audio:
        print(f"  {m}")
    print(f"\n{DIM}whisper-1 is batch (file in, transcript out).")
    print(f"gpt-realtime-whisper, if wired up, would allow streaming.{RESET}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", help="transcribe an existing audio file")
    p.add_argument("--probe", action="store_true", help="list audio models on the gateway")
    args = p.parse_args()

    if not KEY:
        sys.exit(f"{RED}ANTHROPIC_API_KEY not set — check .env{RESET}")

    print(f"{DIM}gateway: {BASE}{RESET}\n")

    if args.probe:
        probe()
        return

    if args.file:
        audio = Path(args.file).expanduser()
        if not audio.exists():
            sys.exit(f"{RED}No such file: {audio}{RESET}")
    else:
        print(f"{BOLD}Original text{RESET}\n  {SAMPLE}\n")
        audio = synthesize(SAMPLE, Path("/tmp/trep_tts.mp3"))

    text = transcribe(audio)
    print(f"{BOLD}Transcript{RESET}\n  {GREEN}{text}{RESET}\n")

    if not args.file:
        # Rough sanity check that the round trip preserved the key terms.
        expected = ["iphone", "magenta", "line"]
        hits = [w for w in expected if w in text.lower()]
        status = GREEN if len(hits) == len(expected) else RED
        print(f"{status}round trip kept {len(hits)}/{len(expected)} key terms: {hits}{RESET}")


if __name__ == "__main__":
    main()
