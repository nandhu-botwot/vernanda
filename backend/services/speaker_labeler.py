"""Speaker labeling: heuristics + LLM fallback."""

import json
import logging
import re

from openai import OpenAI
from backend.config import settings

logger = logging.getLogger(__name__)

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

    Strategy:
    1. If diarization provided 2+ speakers → use heuristic patterns
    2. If all segments have same/no speaker → use LLM to label
    """
    if not segments:
        return segments

    # Collect unique speakers
    speakers = set(seg.get("speaker", "UNKNOWN") for seg in segments)

    if len(speakers) <= 1:
        # No diarization — use LLM to identify speakers
        return _label_with_llm(segments)

    # Heuristic: Check greeting patterns to identify agent speaker
    agent_speaker = None
    speaker_texts = {}
    for seg in segments:
        spk = seg["speaker"]
        if spk not in speaker_texts:
            speaker_texts[spk] = []
        if len(speaker_texts[spk]) < 3:
            speaker_texts[spk].append(seg["text"])

    for spk, texts in speaker_texts.items():
        combined = " ".join(texts).lower()
        for pattern in COMPILED_AGENT_PATTERNS:
            if pattern.search(combined):
                agent_speaker = spk
                break
        if agent_speaker:
            break

    if agent_speaker is None:
        agent_speaker = segments[0].get("speaker", "UNKNOWN")

    for seg in segments:
        if seg["speaker"] == agent_speaker:
            seg["speaker"] = "Agent"
        else:
            seg["speaker"] = "Customer"

    return segments


def _label_with_llm(segments: list[dict]) -> list[dict]:
    """Use LLM to label speakers by processing in batches of 40 segments."""
    BATCH_SIZE = 40
    all_labels = []

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        for batch_start in range(0, len(segments), BATCH_SIZE):
            batch = segments[batch_start:batch_start + BATCH_SIZE]
            batch_labels = _label_batch(client, batch, len(batch))
            if batch_labels is None:
                logger.warning(f"Batch {batch_start} labeling failed, falling back")
                all_labels = None
                break
            all_labels.extend(batch_labels)

        if all_labels and len(all_labels) == len(segments):
            for i, seg in enumerate(segments):
                seg["speaker"] = "Agent" if all_labels[i] in ("A", "Agent", "agent") else "Customer"
            agent_count = sum(1 for s in segments if s["speaker"] == "Agent")
            customer_count = len(segments) - agent_count
            logger.info(f"LLM labeled {len(segments)} segments: {agent_count} Agent, {customer_count} Customer")
            return segments

    except Exception as e:
        logger.warning(f"LLM speaker labeling failed: {e}, falling back")

    # Fallback: label all as Agent
    for seg in segments:
        seg["speaker"] = "Agent"
    return segments


def _label_batch(client, batch: list[dict], n: int) -> list[str] | None:
    """Label a single batch of segments."""
    lines = []
    for i, seg in enumerate(batch):
        text = seg['text'][:80]
        lines.append(f"{i}: {text}")
    transcript = "\n".join(lines)

    prompt = f"""Sales call from Veranda Race (Indian coaching). {n} segments, label each A (Agent) or C (Customer).
Agent: greets, pitches courses, asks questions. Customer: responds, asks about fees.
Return JSON: {{"labels": ["A","C",...]}} — exactly {n} labels.

{transcript}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1000,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    result = json.loads(raw)

    labels = result.get("labels", result.get("speakers", []))
    if isinstance(result, list):
        labels = result

    if len(labels) == n:
        return labels

    # Accept if close — truncate or pad
    if len(labels) >= n:
        logger.info(f"Batch returned {len(labels)} labels for {n} segments, truncating")
        return labels[:n]

    logger.warning(f"Batch returned {len(labels)} labels for {n} segments")
    return None


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
