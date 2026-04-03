"""WhisperX transcription + diarization pipeline."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy-loaded models (cached after first load)
_whisperx_model = None
_diarize_pipeline = None


def _load_whisperx_model():
    global _whisperx_model
    if _whisperx_model is not None:
        return _whisperx_model

    import whisperx
    from backend.config import settings

    logger.info(f"Loading WhisperX model: {settings.whisper_model} on {settings.whisper_device}")
    _whisperx_model = whisperx.load_model(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type="float16" if settings.whisper_device == "cuda" else "int8",
    )
    logger.info("WhisperX model loaded")
    return _whisperx_model


def _load_diarize_pipeline():
    global _diarize_pipeline
    if _diarize_pipeline is not None:
        return _diarize_pipeline

    import whisperx
    from backend.config import settings

    if not settings.hf_auth_token:
        logger.warning("HF_AUTH_TOKEN not set - diarization will be skipped")
        return None

    logger.info("Loading diarization pipeline")
    _diarize_pipeline = whisperx.DiarizationPipeline(
        use_auth_token=settings.hf_auth_token,
        device=settings.whisper_device,
    )
    logger.info("Diarization pipeline loaded")
    return _diarize_pipeline


def transcribe_and_diarize(audio_path: str) -> dict[str, Any]:
    """
    Full WhisperX pipeline: transcribe + align + diarize.

    Returns:
        {
            "segments": [{"start": float, "end": float, "text": str, "speaker": str}, ...],
            "language": str,
            "confidence": float,
        }
    """
    import whisperx
    from backend.config import settings

    model = _load_whisperx_model()

    # 1. Transcribe
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=16)
    detected_language = result.get("language", "en")

    # 2. Align timestamps at word level
    align_model, align_metadata = whisperx.load_align_model(
        language_code=detected_language,
        device=settings.whisper_device,
    )
    result = whisperx.align(
        result["segments"], align_model, align_metadata, audio, settings.whisper_device,
        return_char_alignments=False,
    )

    # 3. Diarize (assign speakers)
    diarize_pipeline = _load_diarize_pipeline()
    if diarize_pipeline is not None:
        diarize_segments = diarize_pipeline(audio_path, num_speakers=2)
        result = whisperx.assign_word_speakers(diarize_segments, result)

    # Calculate average confidence
    confidences = []
    for seg in result.get("segments", []):
        for word in seg.get("words", []):
            if "score" in word:
                confidences.append(word["score"])

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

    # Normalize segments
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg.get("start", 0), 2),
            "end": round(seg.get("end", 0), 2),
            "text": seg.get("text", "").strip(),
            "speaker": seg.get("speaker", "UNKNOWN"),
        })

    return {
        "segments": segments,
        "language": detected_language,
        "confidence": round(avg_confidence, 3),
    }
