"""Heuristics to label speakers as Agent vs Customer."""

import re

# Patterns indicating the speaker is the agent
AGENT_PATTERNS = [
    r"veranda\s*race",
    r"good\s*(morning|afternoon|evening)",
    r"welcome\s+to",
    r"(my\s+name\s+is|this\s+is)\s+\w+",
    r"how\s+(can|may)\s+i\s+help",
    r"academic\s+counsellor",
    r"calling\s+from",
]

COMPILED_AGENT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in AGENT_PATTERNS]


def label_speakers(segments: list[dict]) -> list[dict]:
    """
    Label SPEAKER_00, SPEAKER_01, etc. as 'Agent' or 'Customer'.

    Heuristics (in priority order):
    1. Speaker whose first utterance matches agent greeting patterns -> Agent
    2. If no pattern match, first speaker is assumed to be Agent
    3. All other speakers are Customer
    """
    if not segments:
        return segments

    # Collect unique speakers
    speakers = {}
    for seg in segments:
        spk = seg.get("speaker", "UNKNOWN")
        if spk not in speakers:
            speakers[spk] = {"first_text": seg["text"], "total_time": 0}
        speakers[spk]["total_time"] += seg.get("end", 0) - seg.get("start", 0)

    if len(speakers) <= 1:
        # No diarization available — alternate speakers based on pauses
        # If there's a gap > 1.5s between segments, assume speaker changed
        labeled = _label_by_pauses(segments)
        if labeled:
            return labeled
        # Fallback: label all as Agent (LLM prompt handles this)
        for seg in segments:
            seg["speaker"] = "Agent"
        return segments

    # Heuristic 1: Check greeting patterns in each speaker's first few utterances
    agent_speaker = None
    speaker_texts = {}
    for seg in segments:
        spk = seg["speaker"]
        if spk not in speaker_texts:
            speaker_texts[spk] = []
        if len(speaker_texts[spk]) < 3:  # Check first 3 utterances
            speaker_texts[spk].append(seg["text"])

    for spk, texts in speaker_texts.items():
        combined = " ".join(texts).lower()
        for pattern in COMPILED_AGENT_PATTERNS:
            if pattern.search(combined):
                agent_speaker = spk
                break
        if agent_speaker:
            break

    # Heuristic 2: First speaker is agent
    if agent_speaker is None:
        agent_speaker = segments[0].get("speaker", "UNKNOWN")

    # Apply labels
    for seg in segments:
        if seg["speaker"] == agent_speaker:
            seg["speaker"] = "Agent"
        else:
            seg["speaker"] = "Customer"

    return segments


def _label_by_pauses(segments: list[dict], pause_threshold: float = 1.5) -> list[dict] | None:
    """
    When no diarization is available, use pauses between segments to guess speaker turns.
    A pause > threshold seconds suggests a speaker change.
    First speaker is assumed to be Agent.
    """
    if len(segments) < 2:
        return None

    current_speaker = "Agent"
    segments[0]["speaker"] = current_speaker

    for i in range(1, len(segments)):
        gap = segments[i]["start"] - segments[i - 1]["end"]
        if gap >= pause_threshold:
            current_speaker = "Customer" if current_speaker == "Agent" else "Agent"
        segments[i]["speaker"] = current_speaker

    # Verify we got at least 2 speakers
    speakers = set(s["speaker"] for s in segments)
    if len(speakers) < 2:
        return None

    return segments


def format_transcript(segments: list[dict]) -> str:
    """Format labeled segments into a readable transcript string."""
    lines = []
    for seg in segments:
        timestamp = _format_time(seg["start"])
        speaker = seg["speaker"]
        text = seg["text"]
        lines.append(f"[{timestamp}] {speaker}: {text}")
    return "\n".join(lines)


def _format_time(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"
