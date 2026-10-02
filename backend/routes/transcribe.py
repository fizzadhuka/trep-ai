"""POST /transcribe — audio chunk in, transcript (and optionally intent) out.

Owner: P1b.

The frontend records fixed-length chunks and posts them here rather than
talking to a transcription vendor directly, because the only allowlisted route
off this network is the T-Mobile gateway. That also keeps the API key server
side, which is where it belongs anyway.

Passing `customer_id` chains straight into intent detection, so the browser
makes one round trip per chunk instead of two. If intent detection is down the
transcript still comes back — the mic never appears broken because of an LLM
failure.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.transcription_service import (
    RETAIL_PROMPT,
    TranscriptionError,
    TranscriptionService,
)

router = APIRouter()
service = TranscriptionService()


class TranscribeResponse(BaseModel):
    text: str
    duration_ms: int = 0
    # Why this chunk produced nothing: too_short, filler, caption_boilerplate,
    # prompt_echo, or looping.
    skipped: str | None = None
    # What was filtered out. Returned for logging and debugging only — never
    # render it, nobody said it.
    discarded: str | None = None
    intent: dict | None = None
    intent_error: str | None = None


@router.post("", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    customer_id: str | None = Form(None),
    bias: bool = Form(True),
):
    audio = await file.read()

    try:
        result = await service.transcribe(
            audio,
            filename=file.filename or "chunk.webm",
            prompt=RETAIL_PROMPT if bias else None,
        )
    except TranscriptionError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    payload: dict = {
        "text": result["text"],
        "duration_ms": result.get("duration_ms", 0),
        "skipped": result.get("skipped"),
        "discarded": result.get("discarded"),
    }

    if customer_id and result["text"]:
        # Imported lazily so a problem in the intent layer can never stop the
        # transcription endpoint from starting up.
        try:
            from agents.intent_agent import IntentAgent

            payload["intent"] = await IntentAgent().run(result["text"], customer_id)
        except Exception as exc:
            payload["intent_error"] = f"{type(exc).__name__}: {exc}"[:200]

    return payload
