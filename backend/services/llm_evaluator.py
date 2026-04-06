"""OpenAI GPT-4o evaluator for reasoning-heavy QA parameters."""

import json
import logging
import time

from openai import OpenAI

from backend.config import settings
from backend.services.prompts import SYSTEM_PROMPT, build_evaluation_prompt, build_full_evaluation_prompt, PROMPT_VERSION

logger = logging.getLogger(__name__)

# Expected keys in GPT-4o response (hybrid mode — English calls)
LLM_SCORED_PARAMS = [
    "course_pitch", "false_commitment", "presentation",
    "urgency_need", "repeated_mistakes", "objection_handling", "sale_attempt",
]

# All parameters (full LLM mode — non-English calls)
ALL_SCORED_PARAMS = [
    "greeting", "probing", "lead_source", "course_pitch", "false_commitment",
    "six_level_strategy", "presentation", "urgency_need", "urgency_explanation",
    "repeated_mistakes", "objection_handling", "sale_attempt",
    "further_assistance", "closing", "call_handling",
]

# Max scores for validation
MAX_SCORES = {
    "greeting": 5,
    "probing": 5,
    "lead_source": 5,
    "course_pitch": 5,
    "false_commitment": 5,
    "six_level_strategy": 10,
    "presentation": 10,
    "urgency_need": 10,
    "urgency_explanation": 8,
    "repeated_mistakes": 6,
    "objection_handling": 3,
    "sale_attempt": 5,
    "further_assistance": 3,
    "closing": 5,
    "call_handling": 5,
}


def evaluate_with_llm(
    transcript: str,
    rule_scores: dict,
    previous_feedback: str | None = None,
    full_llm_mode: bool = False,
) -> dict:
    """
    Send transcript to GPT-4o for evaluation of reasoning-heavy parameters.

    Returns dict with:
    - Per-parameter scores (course_pitch, false_commitment, etc.)
    - overall_strengths, overall_weaknesses, critical_issues, call_summary
    - _meta: model, prompt_version, duration_ms
    """
    client = OpenAI(api_key=settings.openai_api_key)

    if full_llm_mode:
        prompt = build_full_evaluation_prompt(transcript, previous_feedback)
        params_to_validate = ALL_SCORED_PARAMS
    else:
        prompt = build_evaluation_prompt(transcript, rule_scores, previous_feedback)
        params_to_validate = LLM_SCORED_PARAMS

    start_time = time.time()

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        response_format={"type": "json_object"},
    )

    duration_ms = int((time.time() - start_time) * 1000)
    raw_content = response.choices[0].message.content

    # Parse JSON
    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Raw response: {raw_content[:500]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")

    # Validate and clamp scores
    for param in params_to_validate:
        if param not in result:
            logger.warning(f"Missing parameter in LLM response: {param}")
            result[param] = {
                "score": 0,
                "max_score": MAX_SCORES[param],
                "evidence": ["Parameter not evaluated by LLM"],
                "feedback": "LLM did not return this parameter.",
                "improvement": "",
            }
        else:
            param_data = result[param]
            max_score = MAX_SCORES[param]
            param_data["max_score"] = max_score
            param_data["score"] = max(0, min(param_data.get("score", 0), max_score))
            param_data["method"] = "llm"

    # Add metadata
    result["_meta"] = {
        "llm_model": settings.llm_model,
        "prompt_version": PROMPT_VERSION,
        "eval_duration_ms": duration_ms,
        "tokens_used": response.usage.total_tokens if response.usage else None,
    }

    return result
