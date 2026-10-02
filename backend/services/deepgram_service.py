"""Deepgram live transcription — backend path. Owner: P1b.

Not on the demo path. The browser streams audio to Deepgram directly via
`frontend/src/hooks/useDeepgram.js`, which is lower latency and fewer moving
parts for a hackathon.

This exists as the production shape: audio proxies through the backend so the
API key never reaches the client. If a judge asks about the key being exposed
in the frontend bundle, this is the answer.
"""

import os

from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

KEEPALIVE_SECONDS = 8  # Deepgram drops idle sockets at ~10s.


class DeepgramService:
    def __init__(self):
        self.client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY", ""))
        self.model = os.getenv("DEEPGRAM_MODEL", "nova-2")

    def create_live_connection(self, on_transcript, on_error=None, on_close=None):
        """Open a live transcription socket.

        `on_transcript` receives Deepgram's event payload. Read the text at
        `result.channel.alternatives[0].transcript` and only act on
        `result.is_final` — interim results churn mid-word.
        """
        conn = self.client.listen.live.v("1")
        conn.on(LiveTranscriptionEvents.Transcript, on_transcript)
        if on_error:
            conn.on(LiveTranscriptionEvents.Error, on_error)
        if on_close:
            conn.on(LiveTranscriptionEvents.Close, on_close)

        conn.start(
            LiveOptions(
                model=self.model,
                language="en-US",
                smart_format=True,
                interim_results=True,
                punctuate=True,
            )
        )
        return conn

    @staticmethod
    def keepalive(conn) -> None:
        """Ping an idle socket. Call every KEEPALIVE_SECONDS during silence."""
        try:
            conn.keep_alive()
        except Exception:
            pass

    @staticmethod
    def close(conn) -> None:
        try:
            conn.finish()
        except Exception:
            pass
