"""Local Whisper transcription service (OpenAI-compatible endpoint).

Forked from the upstream Deepgram transcriber: voice stays on our own
faster-whisper container (WHISPER_URL) instead of the Deepgram cloud — no
per-minute billing and no audio leaving the host.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Transcribe audio via a local OpenAI-compatible Whisper endpoint."""

    def __init__(self, whisper_url: str) -> None:
        self.whisper_url = whisper_url.rstrip("/")

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: Audio file content (Telegram voice ogg/opus).

        Returns:
            Transcribed text, or "" if nothing was recognised.
        """
        logger.info("Starting transcription, audio size: %d bytes", len(audio_bytes))

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.whisper_url}/v1/audio/transcriptions",
                files={"file": ("voice.ogg", audio_bytes, "audio/ogg")},
                data={"model": "Systran/faster-whisper-large-v3", "language": "ru"},
            )
            response.raise_for_status()
            transcript = response.json().get("text", "").strip()

        logger.info("Transcription complete: %d chars", len(transcript))
        return transcript
