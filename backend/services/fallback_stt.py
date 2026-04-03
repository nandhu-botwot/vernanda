"""Fallback STT using OpenAI Whisper API (cloud) for low-confidence local transcriptions."""

import logging
from pathlib import Path

from openai import OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


def transcribe_with_openai_api(audio_path: str) -> dict:
    """
    Use OpenAI's cloud Whisper API as fallback.
    Returns same format as local transcription: {"segments": [...], "language": str, "confidence": float}
    Note: OpenAI API doesn't provide diarization - segments won't have speaker labels.
    """
    client = OpenAI(api_key=settings.openai_api_key)

    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

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
