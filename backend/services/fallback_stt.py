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

# Languages supported by OpenAI Whisper API
# https://platform.openai.com/docs/guides/speech-to-text
# Only include languages confirmed to work with OpenAI Whisper API
WHISPER_SUPPORTED_LANGUAGES = {
    "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca",
    "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms",
    "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la",
    "cy", "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn",
    "et", "mk", "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
    "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc", "ka", "be",
    "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo", "ht", "ps", "tk", "nn",
    "mt", "sa", "lb", "my", "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha",
    "ba", "jw", "su",
}  # Note: 'ml' (Malayalam) removed — not supported by Whisper API


def _get_whisper_language(lang_code: str | None) -> str | None:
    """Return language code only if supported by Whisper, else None (auto-detect)."""
    if not lang_code:
        return None
    lang_code = lang_code.lower().strip()
    if lang_code in WHISPER_SUPPORTED_LANGUAGES:
        return lang_code
    return None  # Let Whisper auto-detect


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


def transcribe_with_openai_api(audio_path: str, call_language: str | None = None) -> dict:
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
        file_size = os.path.getsize(file_to_send)
        duration_estimate = file_size / 16000  # rough estimate in seconds

        # For long audio (>10 min), chunk into 10-min pieces to avoid Whisper hallucination
        if duration_estimate > 600:
            logger.info(f"Long audio (~{duration_estimate:.0f}s), chunking for transcription")
            return _transcribe_chunked(client, file_to_send, call_language)
        else:
            return _transcribe_single(client, file_to_send, call_language)
    finally:
        if compressed_path:
            os.unlink(compressed_path)


def _transcribe_single(client, audio_path: str, language: str | None = None) -> dict:
    """Transcribe a single audio file."""
    kwargs = {
        "model": "whisper-1",
        "response_format": "verbose_json",
        "timestamp_granularities": ["segment"],
    }
    whisper_lang = _get_whisper_language(language)
    if whisper_lang:
        kwargs["language"] = whisper_lang

    with open(audio_path, "rb") as f:
        kwargs["file"] = f
        response = client.audio.transcriptions.create(**kwargs)

    segments = []
    for seg in response.segments or []:
        text = seg.text.strip()
        if text:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": text,
                "speaker": "UNKNOWN",
            })

    # Merge very short consecutive segments (reduces fragmentation)
    segments = _merge_short_segments(segments)

    return {
        "segments": segments,
        "language": response.language or "en",
        "confidence": 0.85,
    }


def _merge_short_segments(segments: list[dict], gap_threshold: float = 2.0) -> list[dict]:
    """Merge consecutive segments that are close together to reduce fragmentation."""
    if len(segments) < 2:
        return segments

    merged = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        gap = seg["start"] - prev["end"]
        # Merge if gap is small (same speaker likely)
        if gap < gap_threshold:
            prev["end"] = seg["end"]
            prev["text"] = prev["text"] + " " + seg["text"]
        else:
            merged.append(seg.copy())

    return merged


def _transcribe_chunked(client, audio_path: str, language: str | None = None) -> dict:
    """Split long audio into chunks and transcribe each separately."""
    chunk_duration_ms = 10 * 60 * 1000  # 10 minutes per chunk
    all_segments = []
    detected_language = "en"

    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        total_ms = len(audio)
    except ImportError:
        # No pydub — use ffmpeg to split
        return _transcribe_chunked_ffmpeg(client, audio_path, language)

    chunk_idx = 0
    offset_sec = 0.0

    for start_ms in range(0, total_ms, chunk_duration_ms):
        end_ms = min(start_ms + chunk_duration_ms, total_ms)
        chunk = audio[start_ms:end_ms]

        # Export chunk to temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        chunk.export(tmp.name, format="mp3", parameters=["-ac", "1", "-ar", "16000", "-b:a", "64k"])

        try:
            result = _transcribe_single(client, tmp.name, language)
            detected_language = result["language"]

            # Adjust timestamps by offset
            for seg in result["segments"]:
                seg["start"] += offset_sec
                seg["end"] += offset_sec
                all_segments.append(seg)
        finally:
            os.unlink(tmp.name)

        offset_sec = end_ms / 1000.0
        chunk_idx += 1
        logger.info(f"Transcribed chunk {chunk_idx} ({start_ms // 1000}s - {end_ms // 1000}s)")

    return {
        "segments": all_segments,
        "language": detected_language,
        "confidence": 0.85,
    }


def _transcribe_chunked_ffmpeg(client, audio_path: str, language: str | None = None) -> dict:
    """Split audio using ffmpeg when pydub is not available."""
    chunk_duration = 600  # 10 minutes in seconds
    all_segments = []
    detected_language = "en"

    # Get duration via ffprobe
    probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
    import json as json_mod
    duration = float(json_mod.loads(probe_result.stdout).get("format", {}).get("duration", 0))

    chunk_idx = 0
    for start_sec in range(0, int(duration), chunk_duration):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()

        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-ss", str(start_sec), "-t", str(chunk_duration),
            "-ac", "1", "-ar", "16000", "-b:a", "64k",
            tmp.name,
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        try:
            result = _transcribe_single(client, tmp.name, language)
            detected_language = result["language"]

            for seg in result["segments"]:
                seg["start"] += start_sec
                seg["end"] += start_sec
                all_segments.append(seg)
        finally:
            os.unlink(tmp.name)

        chunk_idx += 1
        logger.info(f"Transcribed chunk {chunk_idx} ({start_sec}s - {min(start_sec + chunk_duration, int(duration))}s)")

    return {
        "segments": all_segments,
        "language": detected_language,
        "confidence": 0.85,
    }
