"""Rule-based scoring engine for deterministic QA parameters."""

import re
from typing import Any

RULE_ENGINE_VERSION = "1.0.0"

# --- Pattern banks ---

GREETING_PATTERNS = [
    r"good\s*(morning|afternoon|evening)",
    r"(hi|hello|hey)\b",
    r"welcome\s+to",
    r"namaste",
    r"vanakkam",
]
COMPANY_PATTERNS = [r"veranda\s*race", r"race\s*institute", r"veranda\s*learning"]
AGENT_NAME_PATTERNS = [r"(my\s+name\s+is|this\s+is|i\s+am|i'm)\s+\w+"]

LEAD_SOURCE_PATTERNS = [
    r"how\s+did\s+you\s+(hear|know|find|learn)\s+(about|of)",
    r"where\s+did\s+you\s+(hear|find|see|come)",
    r"(lead\s+source|how\s+you\s+came\s+to\s+know)",
    r"(from\s+where|which\s+platform|how\s+did\s+you\s+get\s+to\s+know)",
    r"(website|facebook|instagram|youtube|newspaper|reference|friend|google)",
]

FURTHER_ASSIST_PATTERNS = [
    r"(anything\s+else|any\s+other\s+(doubt|question|query|concern))",
    r"(anything\s+more|any\s+further|any\s+more\s+question)",
    r"(is\s+there\s+anything|do\s+you\s+have\s+any)",
    r"(can\s+i\s+help\s+you\s+with\s+anything)",
    r"whatsapp",
]

CLOSING_PATTERNS = [
    r"thank\s*(you|s)\s*(for|very)",
    r"all\s+the\s+best",
    r"have\s+a\s+(good|nice|great)\s+day",
    r"(follow.?up|callback|call\s*back)\s*(on|date|time|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
]

PROBING_ITEMS = {
    "name": [r"(your\s+name|may\s+i\s+know\s+your\s+name|what.*name)"],
    "age": [r"(your\s+age|how\s+old|age\s+limit|what.*age)"],
    "qualification": [r"(qualifi|education|degree|graduate|post.?graduate|12th|10th|diploma)"],
    "location": [r"(where\s+are\s+you|which\s+(city|place|state|location)|located|from\s+where)"],
    "mode": [r"(online|offline|mode\s+of|prefer.*online|prefer.*offline|blended|hybrid)"],
}

SIX_LEVEL_KEYWORDS = [
    "basic class", "basic circle", "extremer circle",
    "super batch", "superbatch", "rip", "rapid improvement",
    "mock interview", "mock test",
]

URGENCY_POINTS = [
    (r"notif(ication|y)|exam\s+(notification|date|coming)", "Notification/Exam dates"),
    (r"(new\s+batch|batch\s+start|don.?t\s+miss)", "New batch starting"),
    (r"(coupon|discount|offer|promo)", "Coupon/Offer"),
    (r"(fee\s+increas|price\s+increas|fee\s+hike|fees\s+will)", "Fee increase"),
    (r"(competition|compet|more\s+candidates|lakhs\s+of)", "Competition increasing"),
    (r"(age\s+limit|age\s+bar|age\s+criteria|running\s+out\s+of\s+age)", "Age limit"),
    (r"(don.?t\s+break\s+study|continue\s+study|after\s+college)", "Study continuity"),
    (r"(syllabus\s+complet|cover\s+syllabus|finish\s+syllabus)", "Syllabus completion"),
    (r"(limited\s+seat|seat\s+filling|only\s+few)", "Limited seats"),
    (r"(easy\s+exam|avoid\s+tough|level\s+increas)", "Exam difficulty"),
]


def _search_agent_text(segments: list[dict], patterns: list[str], search_range: str = "all") -> list[str]:
    """Search agent utterances for pattern matches. Returns matching text excerpts."""
    matches = []
    agent_segments = [s for s in segments if s.get("speaker") == "Agent"]

    if search_range == "first_5":
        agent_segments = agent_segments[:5]
    elif search_range == "last_5":
        agent_segments = agent_segments[-5:]

    for seg in agent_segments:
        text = seg["text"]
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(text)
                break
    return matches


def _search_all_text(segments: list[dict], patterns: list[str]) -> list[str]:
    """Search all segments (both speakers) for patterns."""
    matches = []
    for seg in segments:
        for pattern in patterns:
            if re.search(pattern, seg["text"], re.IGNORECASE):
                matches.append(seg["text"])
                break
    return matches


def score_greeting(segments: list[dict]) -> dict:
    """Score: Greeting (max 5). Agent greets with name + company name."""
    agent_first = [s for s in segments if s.get("speaker") == "Agent"][:3]
    if not agent_first:
        return _result(0, 5, [], "No agent greeting detected.", "Start the call with a warm greeting including your name and 'Veranda Race'.")

    combined = " ".join(s["text"] for s in agent_first)
    score = 0
    evidence = [s["text"] for s in agent_first]

    has_greeting = any(re.search(p, combined, re.IGNORECASE) for p in GREETING_PATTERNS)
    has_company = any(re.search(p, combined, re.IGNORECASE) for p in COMPANY_PATTERNS)
    has_name = any(re.search(p, combined, re.IGNORECASE) for p in AGENT_NAME_PATTERNS)

    if has_greeting:
        score += 2
    if has_company:
        score += 2
    if has_name:
        score += 1

    feedback_parts = []
    if not has_greeting:
        feedback_parts.append("Missing greeting phrase (Good morning/Hello)")
    if not has_company:
        feedback_parts.append("Did not mention Veranda Race/company name")
    if not has_name:
        feedback_parts.append("Did not introduce self by name")

    feedback = "Good greeting." if score == 5 else "; ".join(feedback_parts)
    improvement = "" if score == 5 else "Use: 'Good morning, this is [Name] from Veranda Race. How can I help you?'"

    return _result(score, 5, evidence, feedback, improvement)


def score_lead_source(segments: list[dict]) -> dict:
    """Score: Primary Lead Source Identification (max 5)."""
    matches = _search_agent_text(segments, LEAD_SOURCE_PATTERNS)
    if matches:
        return _result(5, 5, matches[:2], "Agent asked about lead source.", "")
    return _result(0, 5, [], "Agent did not ask how the customer found Veranda Race.", "Ask: 'May I know how you came to know about Veranda Race?'")


def score_further_assistance(segments: list[dict]) -> dict:
    """Score: Further Assistance (max 3). Asks 'anything else' + WhatsApp."""
    matches = _search_agent_text(segments, FURTHER_ASSIST_PATTERNS, "last_5")
    whatsapp = any(re.search(r"whatsapp", s["text"], re.IGNORECASE) for s in segments if s.get("speaker") == "Agent")

    score = 0
    evidence = matches[:2]

    anything_else = len([m for m in matches if not re.search(r"whatsapp", m, re.IGNORECASE)]) > 0
    if anything_else:
        score += 2
    if whatsapp:
        score += 1
        evidence.append("[WhatsApp mentioned]")

    feedback_parts = []
    if not anything_else:
        feedback_parts.append("Did not ask if customer had further doubts")
    if not whatsapp:
        feedback_parts.append("Did not mention sharing details via WhatsApp")

    feedback = "Good - offered further assistance." if score == 3 else "; ".join(feedback_parts)
    improvement = "" if score == 3 else "Before closing, ask 'Do you have any other doubts?' and offer to share details via WhatsApp."

    return _result(score, 3, evidence, feedback, improvement)


def score_closing(segments: list[dict]) -> dict:
    """Score: Closing (max 5). Proper closing + follow-up scheduling."""
    agent_last = [s for s in segments if s.get("speaker") == "Agent"][-5:]
    if not agent_last:
        return _result(0, 5, [], "No closing detected.", "End with 'Thank you for calling Veranda Race' and schedule a follow-up.")

    combined = " ".join(s["text"] for s in agent_last)
    evidence = [s["text"] for s in agent_last]
    score = 0

    has_thank = any(re.search(r"thank", combined, re.IGNORECASE) for _ in [1])
    has_followup = any(re.search(p, combined, re.IGNORECASE) for p in [
        r"follow.?up", r"call\s*(you\s+)?back", r"(tomorrow|next\s+week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        r"(when\s+can\s+i|when\s+should\s+i|i.?ll\s+call)",
    ])
    has_best_wishes = any(re.search(r"(all\s+the\s+best|good\s+luck|have\s+a\s+(good|nice|great)\s+day)", combined, re.IGNORECASE) for _ in [1])

    if has_thank:
        score += 2
    if has_followup:
        score += 2
    if has_best_wishes:
        score += 1

    feedback_parts = []
    if not has_thank:
        feedback_parts.append("Missing 'Thank you for calling'")
    if not has_followup:
        feedback_parts.append("No follow-up date/callback scheduled")
    if not has_best_wishes:
        feedback_parts.append("No best wishes / positive closing")

    feedback = "Strong closing." if score == 5 else "; ".join(feedback_parts)
    improvement = "" if score == 5 else "End with: 'Thank you for calling Veranda Race. I'll follow up with you on [date]. All the best!'"

    return _result(score, 5, evidence[:3], feedback, improvement)


def score_call_handling(segments: list[dict]) -> dict:
    """Score: Call Handling Behavior (max 5). Check for long silences, agent talk ratio."""
    if not segments:
        return _result(0, 5, [], "No segments to analyze.", "")

    agent_time = sum(s["end"] - s["start"] for s in segments if s.get("speaker") == "Agent")
    customer_time = sum(s["end"] - s["start"] for s in segments if s.get("speaker") == "Customer")
    total_time = agent_time + customer_time

    score = 5
    feedback_parts = []
    evidence = []

    # Check talk ratio - agent should talk 50-75% in a sales call
    if total_time > 0:
        agent_ratio = agent_time / total_time
        evidence.append(f"Agent talk ratio: {agent_ratio:.0%}")

        if agent_ratio < 0.3:
            score -= 2
            feedback_parts.append("Agent spoke too little - may not be proactive enough")
        elif agent_ratio > 0.85:
            score -= 1
            feedback_parts.append("Agent dominated the conversation - listen more to the customer")

    # Check if agent was the last speaker (shouldn't disconnect abruptly)
    if segments:
        last_speaker = segments[-1].get("speaker")
        if last_speaker == "Customer":
            score -= 1
            feedback_parts.append("Customer was the last speaker - agent may have disconnected early")
            evidence.append(f"Last utterance by: {last_speaker}")

    # Check for very short call (might indicate agent not being proactive)
    if total_time < 60:
        score -= 2
        feedback_parts.append("Very short call (<1 min) - agent may not have engaged properly")

    score = max(0, score)
    feedback = "Good call handling behavior." if score == 5 else "; ".join(feedback_parts)
    improvement = "" if score == 5 else "Maintain a balanced conversation, listen actively, and don't end the call abruptly."

    return _result(score, 5, evidence, feedback, improvement)


def score_probing_rules(segments: list[dict]) -> dict:
    """
    Partial rule-based scoring for Probing (max 5).
    Counts how many of [name, age, qualification, location, mode] were asked.
    Returns rule score + evidence. LLM will verify quality.
    """
    found_items = {}
    for item_name, patterns in PROBING_ITEMS.items():
        matches = _search_all_text(segments, patterns)
        if matches:
            found_items[item_name] = matches[0]

    count = len(found_items)
    score = min(count, 5)
    evidence = [f"{k}: '{v[:80]}'" for k, v in found_items.items()]
    missing = [k for k in PROBING_ITEMS if k not in found_items]

    feedback = f"Collected {count}/5 customer details."
    if missing:
        feedback += f" Missing: {', '.join(missing)}."

    return _result(score, 5, evidence, feedback, f"Also ask about: {', '.join(missing)}" if missing else "")


def score_six_level_rules(segments: list[dict]) -> dict:
    """
    Partial rule-based scoring for 6 Level Strategy (max 10).
    Counts how many of the 6 levels were mentioned.
    """
    agent_text = " ".join(s["text"] for s in segments if s.get("speaker") == "Agent").lower()
    found = []
    for keyword in SIX_LEVEL_KEYWORDS:
        if keyword in agent_text:
            found.append(keyword)

    # Deduplicate similar matches
    unique_levels = set()
    for kw in found:
        if "basic class" in kw:
            unique_levels.add("Basic Class")
        elif "basic circle" in kw:
            unique_levels.add("Basic Circle")
        elif "extremer" in kw:
            unique_levels.add("Extremer Circle")
        elif "super" in kw:
            unique_levels.add("Superbatch")
        elif "rip" in kw or "rapid" in kw:
            unique_levels.add("RIP")
        elif "mock" in kw:
            unique_levels.add("Mock Interview")

    count = len(unique_levels)
    # Rough scoring: ~1.5 points per level mentioned
    score = min(round(count * 1.67), 10)

    evidence = [f"Mentioned: {', '.join(unique_levels)}"] if unique_levels else []
    missing = {"Basic Class", "Basic Circle", "Extremer Circle", "Superbatch", "RIP", "Mock Interview"} - unique_levels

    feedback = f"Mentioned {count}/6 levels of the practice methodology."
    if missing:
        feedback += f" Missing: {', '.join(missing)}."

    return _result(score, 10, evidence, feedback, f"Explain all 6 levels: {', '.join(missing)}" if missing else "")


def score_urgency_rules(segments: list[dict]) -> dict:
    """
    Partial rule-based scoring for Urgency Explanation (max 8).
    Each urgency point found = 2 marks, max 4 points = 8 marks.
    """
    agent_text = " ".join(s["text"] for s in segments if s.get("speaker") == "Agent").lower()

    found_points = []
    for pattern, label in URGENCY_POINTS:
        if re.search(pattern, agent_text, re.IGNORECASE):
            found_points.append(label)

    count = min(len(found_points), 4)
    score = count * 2  # 2 marks per point, max 4 points

    evidence = [f"Urgency point: {p}" for p in found_points[:4]]
    feedback = f"Used {len(found_points)} urgency point(s)."
    if count < 4:
        feedback += f" Need at least 4 for full marks."

    return _result(score, 8, evidence, feedback, "Use more urgency tactics: exam notifications, fee increases, competition, age limits." if score < 8 else "")


def run_all_rules(segments: list[dict]) -> dict[str, dict]:
    """Run all rule-based scoring and return results keyed by parameter name."""
    return {
        "greeting": score_greeting(segments),
        "lead_source": score_lead_source(segments),
        "further_assistance": score_further_assistance(segments),
        "closing": score_closing(segments),
        "call_handling": score_call_handling(segments),
        # Hybrid params (rule part only - LLM will refine)
        "probing": score_probing_rules(segments),
        "six_level_strategy": score_six_level_rules(segments),
        "urgency_explanation": score_urgency_rules(segments),
    }


def _result(score: float, max_score: float, evidence: list[str], feedback: str, improvement: str) -> dict:
    return {
        "score": score,
        "max_score": max_score,
        "method": "rule",
        "evidence": evidence,
        "feedback": feedback,
        "improvement": improvement,
    }
