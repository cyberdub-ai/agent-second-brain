"""Cold large-v3 answered in 112-122 s, the old 120 s ceiling dropped voice (B-11)."""

import asyncio

import httpx

import d_brain.services.transcription as tr


def test_cold_whisper_gets_300_seconds(monkeypatch):
    seen = {}
    real_client = httpx.AsyncClient

    def client(**kwargs):
        seen.update(kwargs)
        reply = httpx.Response(200, json={"text": " привет "})
        transport = httpx.MockTransport(lambda req: reply)
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr(tr.httpx, "AsyncClient", client)
    text = asyncio.run(tr.WhisperTranscriber("http://w/").transcribe(b"ogg"))

    assert text == "привет"
    assert seen["timeout"] == tr.WHISPER_TIMEOUT == 300
