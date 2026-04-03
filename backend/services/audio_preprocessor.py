"""Audio preprocessing pipeline: noise reduction, normalization, resampling, silence trimming."""

import subprocess
import tempfile
from pathlib import Path

import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize

from backend.config import settings

try:
    import noisereduce as nr
    HAS_NOISEREDUCE = True
except ImportError:
    HAS_NOISEREDUCE = False


def get_audio_info(file_path: str) -> dict:
    """Get audio metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise ValueError(f"Failed to read audio file: {result.stderr}")

    import json
    info = json.loads(result.stdout)
    duration = float(info.get("format", {}).get("duration", 0))
    return {"duration": duration, "format": info.get("format", {}), "streams": info.get("streams", [])}


def preprocess_audio(input_path: str, output_path: str | None = None) -> tuple[str, float]:
    """
    Full preprocessing pipeline:
    1. Load audio
    2. Convert to 16kHz mono WAV
    3. Normalize volume
    4. Reduce noise
    5. Trim leading/trailing silence

    Returns (output_path, duration_seconds).
    """
    if output_path is None:
        stem = Path(input_path).stem
        output_path = str(settings.processed_path / f"{stem}_processed.wav")

    # Load with pydub (handles mp3, wav, m4a, etc. via ffmpeg)
    audio = AudioSegment.from_file(input_path)

    # Convert to mono, 16kHz, 16-bit
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)

    # Normalize volume to -20 dBFS
    audio = normalize(audio)
    target_dbfs = -20.0
    change = target_dbfs - audio.dBFS
    audio = audio.apply_gain(change)

    # Noise reduction
    if HAS_NOISEREDUCE:
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        reduced = nr.reduce_noise(y=samples, sr=16000, prop_decrease=0.7, stationary=True)
        audio = AudioSegment(
            reduced.astype(np.int16).tobytes(),
            frame_rate=16000,
            sample_width=2,
            channels=1,
        )

    # Trim leading/trailing silence (threshold: -40 dBFS, minimum silence: 2000ms)
    audio = _trim_silence(audio, silence_thresh=-40, min_silence_len=2000)

    # Validate duration
    duration_seconds = len(audio) / 1000.0
    max_duration = settings.max_duration_minutes * 60
    if duration_seconds > max_duration:
        raise ValueError(
            f"Audio too long: {duration_seconds:.0f}s (max {max_duration}s). "
            f"Consider trimming the file."
        )

    # Export
    audio.export(output_path, format="wav")
    return output_path, duration_seconds


def _trim_silence(audio: AudioSegment, silence_thresh: int = -40, min_silence_len: int = 2000) -> AudioSegment:
    """Remove leading and trailing silence."""
    from pydub.silence import detect_leading_silence

    start_trim = detect_leading_silence(audio, silence_threshold=silence_thresh, chunk_size=10)
    reversed_audio = audio.reverse()
    end_trim = detect_leading_silence(reversed_audio, silence_threshold=silence_thresh, chunk_size=10)

    duration = len(audio)
    start = min(start_trim, duration)
    end = max(duration - end_trim, start)

    return audio[start:end]
