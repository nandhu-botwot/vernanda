"""Fallback STT using OpenAI Whisper API (cloud) for low-confidence local transcriptions."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

OPENAI_MAX_SIZE = 25 * 1024 * 1024  # 25MB


def _compress_audio(audio_path: str) -> str:
    """Compress audio to mono 16kHz MP3 to fit within OpenAI's 25MB limit."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    cmd = [
        "ffmpeg", "-y", "-i", audio_path,
        "-ac", "1", "-ar", "16000", "-b:a", "64k",
        tmp.name,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        os.unlink(tmp.name)
        raise RuntimeError(f"ffmpeg compression failed: {result.stderr[:300]}")
    logger.info(f"Compressed audio: {os.path.getsize(audio_path)} -> {os.path.getsize(tmp.name)} bytes")
    return tmp.name


def transcribe_with_openai_api(audio_path: str) -> dict:
    """
    Use OpenAI's cloud Whisper API as fallback.
    Returns same format as local transcription: {"segments": [...], "language": str, "confidence": float}
    Note: OpenAI API doesn't provide diarization - segments won't have speaker labels.
    """
    client = OpenAI(api_key=settings.openai_api_key)

    # Compress if file exceeds OpenAI's 25MB limit
    compressed_path = None
    file_to_send = audio_path
    if os.path.getsize(audio_path) > OPENAI_MAX_SIZE:
        logger.info(f"Audio file too large ({os.path.getsize(audio_path)} bytes), compressing...")
        compressed_path = _compress_audio(audio_path)
        file_to_send = compressed_path

    try:
        with open(file_to_send, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
    finally:
        if compressed_path:
            os.unlink(compressed_path)

    segments = []
    for seg in response.segments or []:
        segments.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
            "speaker": "UNKNOWN",  # OpenAI API doesn't do diarization
        })

    return {
        "segments": segments,
        "language": response.language or "en",
        "confidence": 0.85,  # OpenAI API is generally high quality
    }
