"""Sarvam AI Speech-to-Text for Indian languages."""

import logging
import os
import subprocess
import tempfile

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

SARVAM_API_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_MAX_DURATION = 25  # seconds per chunk (API limit is 30s, use 25 for safety)

# Indian languages supported by Sarvam
SARVAM_LANGUAGES = {
    "hi": "hi-IN",
    "bn": "bn-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "od": "od-IN",
    "pa": "pa-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "gu": "gu-IN",
    "en": "en-IN",
}


def is_sarvam_supported(language: str | None) -> bool:
    """Check if a language is supported by Sarvam AI."""
    if not language:
        return False
    return language.lower() in SARVAM_LANGUAGES


def transcribe_with_sarvam(audio_path: str, call_language: str | None = None) -> dict:
    """
    Transcribe audio using Sarvam AI API.
    Chunks long audio into 30s pieces and transcribes each.

    Returns same format as other STT: {"segments": [...], "language": str, "confidence": float}
    """
    if not settings.sarvam_api_key:
        raise ValueError("SARVAM_API_KEY not configured")

    # Get audio duration
    duration = _get_duration(audio_path)
    logger.info(f"Sarvam STT: audio duration {duration:.0f}s, language={call_language}")

    # Map language code
    lang_code = SARVAM_LANGUAGES.get(call_language, "unknown") if call_language else "unknown"

    all_segments = []

    if duration <= SARVAM_MAX_DURATION:
        # Single chunk
        result = _transcribe_chunk(audio_path, lang_code)
        if result:
            all_segments.extend(result["segments"])
    else:
        # Split into 30s chunks
        chunk_paths = _split_audio(audio_path, SARVAM_MAX_DURATION)
        try:
            for i, (chunk_path, offset_sec) in enumerate(chunk_paths):
                result = _transcribe_chunk(chunk_path, lang_code)
                if result:
                    for seg in result["segments"]:
                        seg["start"] += offset_sec
                        seg["end"] += offset_sec
                        all_segments.append(seg)
                logger.info(f"Sarvam: transcribed chunk {i + 1}/{len(chunk_paths)}")
        finally:
            # Clean up temp files
            for chunk_path, _ in chunk_paths:
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)

    # Merge consecutive segments from same speaker
    all_segments = _merge_speaker_segments(all_segments)

    detected_lang = call_language or "unknown"
    logger.info(f"Sarvam STT: {len(all_segments)} segments, language={detected_lang}")

    return {
        "segments": all_segments,
        "language": detected_lang,
        "confidence": 0.90,
    }


def _transcribe_chunk(audio_path: str, lang_code: str) -> dict | None:
    """Transcribe a single audio chunk (max 30s) via Sarvam API."""
    headers = {
        "api-subscription-key": settings.sarvam_api_key,
    }

    try:
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            data = {
                "model": "saarika:v2.5",
                "language_code": lang_code,
                "with_timestamps": "true",
            }

            response = httpx.post(
                SARVAM_API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=60,
            )

        if response.status_code != 200:
            logger.warning(f"Sarvam API error {response.status_code}: {response.text[:200]}")
            return None

        result = response.json()
        segments = []

        # Use diarized transcript if available
        diarized = result.get("diarized_transcript")
        if diarized and diarized.get("entries"):
            for entry in diarized["entries"]:
                text = entry.get("transcript", "").strip()
                if text:
                    segments.append({
                        "start": round(entry.get("start_time_seconds", 0), 2),
                        "end": round(entry.get("end_time_seconds", 0), 2),
                        "text": text,
                        "speaker": entry.get("speaker_id", "UNKNOWN"),
                    })
        elif result.get("transcript"):
            # No diarization — use timestamps if available
            timestamps = result.get("timestamps")
            if timestamps and timestamps.get("words"):
                words = timestamps["words"]
                starts = timestamps.get("start_time_seconds", [])
                ends = timestamps.get("end_time_seconds", [])
                # Group words into sentence-like segments
                text = " ".join(words)
                start = starts[0] if starts else 0
                end = ends[-1] if ends else 0
                segments.append({
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "text": text,
                    "speaker": "UNKNOWN",
                })
            else:
                segments.append({
                    "start": 0,
                    "end": 0,
                    "text": result["transcript"],
                    "speaker": "UNKNOWN",
                })

        return {"segments": segments, "language_code": result.get("language_code")}

    except Exception as e:
        logger.error(f"Sarvam transcription failed: {e}")
        return None


def _split_audio(audio_path: str, chunk_duration: int) -> list[tuple[str, float]]:
    """Split audio into chunks of specified duration. Returns [(chunk_path, offset_seconds), ...]"""
    duration = _get_duration(audio_path)
    chunks = []

    for start_sec in range(0, int(duration), chunk_duration):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_sec), "-i", audio_path,
            "-t", str(chunk_duration),
            "-ac", "1", "-ar", "16000", "-b:a", "64k",
            "-avoid_negative_ts", "1",
            tmp.name,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            chunks.append((tmp.name, float(start_sec)))
        else:
            logger.warning(f"ffmpeg chunk failed at {start_sec}s: {result.stderr[:100]}")
            os.unlink(tmp.name)

    return chunks


def _get_duration(audio_path: str) -> float:
    """Get audio duration using ffprobe."""
    import json
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        info = json.loads(result.stdout)
        return float(info.get("format", {}).get("duration", 0))
    return 0


def _merge_speaker_segments(segments: list[dict]) -> list[dict]:
    """Merge consecutive segments from the same speaker."""
    if len(segments) < 2:
        return segments

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        if seg.get("speaker") == prev.get("speaker") and (seg["start"] - prev["end"]) < 1.0:
            prev["end"] = seg["end"]
            prev["text"] = prev["text"] + " " + seg["text"]
        else:
            merged.append(seg.copy())

    return merged
