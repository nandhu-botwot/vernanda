"""Merge rule-engine and LLM scores into a final QA report."""

from backend.services.rule_engine import RULE_ENGINE_VERSION

# Canonical parameter names and display labels
PARAMETER_SPEC = {
    "greeting":             {"label": "Greeting", "max": 5},
    "probing":              {"label": "Probing / Customer Identification", "max": 5},
    "lead_source":          {"label": "Primary Lead Source Identification", "max": 5},
    "course_pitch":         {"label": "Course Pitch & Opportunities", "max": 5},
    "false_commitment":     {"label": "No False Commitment", "max": 5},
    "six_level_strategy":   {"label": "6 Level Strategy Explanation", "max": 10},
    "presentation":         {"label": "Presentation & Messaging", "max": 10},
    "urgency_need":         {"label": "Urgency Creation Need", "max": 10},
    "urgency_explanation":  {"label": "Urgency Explanation", "max": 8},
    "repeated_mistakes":    {"label": "Repeated Mistakes", "max": 6},
    "objection_handling":   {"label": "Objection Handling", "max": 3},
    "sale_attempt":         {"label": "Sale Attempt", "max": 5},
    "further_assistance":   {"label": "Further Assistance", "max": 3},
    "closing":              {"label": "Closing", "max": 5},
    "call_disposition":     {"label": "Call Disposition", "max": 10},
    "call_handling":        {"label": "Call Handling Behavior", "max": 5},
}


def compute_grade(total: float) -> str:
    if total >= 90:
        return "A+"
    if total >= 80:
        return "A"
    if total >= 70:
        return "B+"
    if total >= 60:
        return "B"
    if total >= 50:
        return "C"
    if total >= 40:
        return "D"
    return "F"


def merge_scores(rule_scores: dict, llm_scores: dict) -> dict:
    """
    Merge rule-engine scores and LLM scores into a unified report.

    Returns:
    {
        "scores": {param_key: {score, max_score, method, evidence, feedback, improvement, label}},
        "total_score": float,
        "grade": str,
        "strengths": [...],
        "weaknesses": [...],
        "critical_issues": [...],
        "improvements": str,
        "call_summary": str,
        "llm_model": str,
        "prompt_version": str,
        "rule_engine_version": str,
        "eval_duration_ms": int,
    }
    """
    merged_scores = {}

    for param_key, spec in PARAMETER_SPEC.items():
        # Priority: LLM score > Rule score > Default
        if param_key in llm_scores and param_key not in ("_meta", "overall_strengths", "overall_weaknesses", "critical_issues", "call_summary"):
            entry = llm_scores[param_key]
            entry["method"] = entry.get("method", "llm")
        elif param_key in rule_scores:
            entry = rule_scores[param_key]
            entry["method"] = "rule"
        elif param_key == "call_disposition":
            # Default: full marks with manual verification note
            entry = {
                "score": 10,
                "max_score": 10,
                "method": "user_input",
                "evidence": [],
                "feedback": "Call disposition cannot be verified from audio alone. Defaulting to full marks - verify in CRM.",
                "improvement": "",
            }
        else:
            entry = {
                "score": 0,
                "max_score": spec["max"],
                "method": "missing",
                "evidence": [],
                "feedback": "Parameter could not be evaluated.",
                "improvement": "",
            }

        # Ensure max_score matches spec
        entry["max_score"] = spec["max"]
        entry["score"] = max(0, min(entry.get("score", 0), spec["max"]))
        entry["label"] = spec["label"]
        merged_scores[param_key] = entry

    # Calculate total
    total_score = sum(v["score"] for v in merged_scores.values())
    grade = compute_grade(total_score)

    # Extract LLM meta
    meta = llm_scores.get("_meta", {})

    # Build improvement suggestions from all parameters
    improvements = []
    for param_key, entry in merged_scores.items():
        if entry.get("improvement"):
            improvements.append(f"- {entry['label']}: {entry['improvement']}")

    return {
        "scores": merged_scores,
        "total_score": round(total_score, 1),
        "grade": grade,
        "strengths": llm_scores.get("overall_strengths", []),
        "weaknesses": llm_scores.get("overall_weaknesses", []),
        "critical_issues": llm_scores.get("critical_issues", []),
        "improvements": "\n".join(improvements) if improvements else "No specific improvements needed.",
        "call_summary": llm_scores.get("call_summary", ""),
        "llm_model": meta.get("llm_model", ""),
        "prompt_version": meta.get("prompt_version", ""),
        "rule_engine_version": RULE_ENGINE_VERSION,
        "eval_duration_ms": meta.get("eval_duration_ms", 0),
    }
