"""Split long audio files into overlapping chunks for parallel processing."""

from pathlib import Path
from pydub import AudioSegment


def chunk_audio(
    file_path: str,
    chunk_duration_ms: int = 15 * 60 * 1000,  # 15 minutes
    overlap_ms: int = 30 * 1000,               # 30 seconds overlap
    max_duration_ms: int = 45 * 60 * 1000,     # Only chunk if > 45 minutes
) -> list[dict]:
    """
    Split audio into overlapping chunks if it exceeds max_duration_ms.

    Returns list of dicts: [{"path": str, "start_ms": int, "end_ms": int}, ...]
    If audio is short enough, returns single entry with original file.
    """
    audio = AudioSegment.from_file(file_path)
    total_ms = len(audio)

    if total_ms <= max_duration_ms:
        return [{"path": file_path, "start_ms": 0, "end_ms": total_ms}]

    chunks = []
    stem = Path(file_path).stem
    parent = Path(file_path).parent
    start = 0
    chunk_idx = 0

    while start < total_ms:
        end = min(start + chunk_duration_ms, total_ms)
        chunk = audio[start:end]

        chunk_path = str(parent / f"{stem}_chunk{chunk_idx}.wav")
        chunk.export(chunk_path, format="wav")

        chunks.append({"path": chunk_path, "start_ms": start, "end_ms": end})

        # Move start forward, accounting for overlap
        start = end - overlap_ms if end < total_ms else total_ms
        chunk_idx += 1

    return chunks
