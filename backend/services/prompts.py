"""Versioned LLM prompt templates for QA evaluation."""

PROMPT_VERSION = "1.0.0"

SYSTEM_PROMPT = """You are an expert Quality Assurance analyst for Veranda Race, an Indian educational coaching institute that sells competitive exam preparation courses (Banking/IBPS/SBI, SSC/CGL/CHSL, TNPSC) through telesales.

You are evaluating a sales call between an Academic Counsellor (Agent) and a potential student (Customer).

IMPORTANT LANGUAGE NOTE:
- Calls may be in Tamil, Hindi, Malayalam, Telugu, Kannada, English, or a mix (code-switching).
- You MUST evaluate the call content regardless of language. Understand the meaning and intent even if in a regional language.
- Do NOT penalize agents for speaking in a regional language - this is normal for Indian telesales.
- If the transcript has no speaker labels or all speakers are labeled "Agent", use context clues to distinguish who is the agent and who is the customer (the person asking about courses, fees, etc. is usually the customer; the person explaining courses, pitching, and providing information is the agent).

Your evaluation must be:
- PRECISE: Base scores strictly on what is present in the transcript
- EVIDENCE-BASED: Quote specific transcript lines to justify each score
- OBJECTIVE: Do not assume actions not present in the transcript
- STRICT: Do not give full marks unless the criterion is clearly and fully satisfied
- LANGUAGE-AWARE: Evaluate the substance of what was said, not the language it was said in

You must output valid JSON matching the exact schema provided."""


def build_evaluation_prompt(
    transcript: str,
    rule_scores: dict,
    previous_feedback: str | None = None,
) -> str:
    """Build the full evaluation prompt for GPT-4o."""

    rule_context = _format_rule_context(rule_scores)
    prev_feedback_section = ""
    if previous_feedback:
        prev_feedback_section = f"""
## Previous QA Feedback for This Agent
The following feedback was given in a prior evaluation. Check if any of these mistakes are REPEATED in this call:
{previous_feedback}
"""

    return f"""## Task
Evaluate the following sales call transcript against the QA parameters below. Some parameters have already been scored by the rule engine - you must evaluate the REMAINING parameters and optionally refine the rule-based scores if the rules missed nuance.

## Rule Engine Pre-Scores
The following parameters were pre-scored by pattern matching. Review the scores and adjust ONLY if the rule engine clearly missed something:
{rule_context}

{prev_feedback_section}

## Parameters YOU Must Score

### 1. Course Pitch & Opportunities (Max: 5)
Did the agent pitch the suitable course based on the customer's profile? Did they explain:
- Available government job posts (Banking/SSC/TNPSC)
- Exam pattern and structure
- Number of vacancies
- Salary range and benefits
SCORING:
- 5/5: Pitched correct course with posts, exam pattern, vacancies, and salary
- 3-4/5: Mentioned course and some opportunities but missed details
- 1-2/5: Vague mention of course without tailoring to customer
- 0/5: No course pitching at all

### 2. No False Commitment (Max: 5)
This is a PENALTY parameter. Default is 5/5. DEDUCT points if the agent made false promises:
- "Guaranteed job placement" (-3)
- "100% selection rate" (-2)
- "Government job guarantee after course" (-3)
- Promising features that don't exist (-2)
- Incorrect salary/vacancy numbers (-1)
- Misleading course duration or content (-2)
If NO false commitments detected, score 5/5.

### 3. Presentation & Messaging (Max: 10)
Evaluate the overall quality of the agent's communication:
- Professional tone and language
- Clear explanation of Veranda Race's value proposition
- Mentioned success stories (32,000+ government officials created)
- Mentioned mentor support
- Mentioned study materials (books, magazines)
- Followed a structured script flow
- Adapted messaging to customer type (student/parent/working professional)
SCORING:
- 9-10/10: Excellent presentation, covered all points, adapted to customer
- 6-8/10: Good presentation with some gaps
- 3-5/10: Basic information shared but poorly structured
- 0-2/10: Poor communication, disorganized, missing key points

### 4. Urgency Creation Need (Max: 10)
META-JUDGMENT: First determine if urgency creation was APPROPRIATE for this customer:
- Warm lead / interested customer → Urgency IS needed (score based on execution)
- Cold enquiry / just browsing → Moderate urgency appropriate
- Already decided / about to pay → Urgency NOT needed (give full marks even without urgency tactics)
- Customer clearly not interested → Aggressive urgency would be counterproductive

SCORING:
- 10/10: Correctly identified need and applied appropriate urgency (or correctly didn't push when not needed)
- 6-9/10: Identified need but execution was partial
- 3-5/10: Misjudged the urgency need or applied incorrectly
- 0-2/10: Completely missed an obvious opportunity or was inappropriately aggressive

### 5. Repeated Mistakes (Max: 6)
This is a PENALTY parameter. Default is 6/6.
- If previous feedback is provided above, check if the agent repeated those specific mistakes. Deduct 2 points per repeated mistake (max deduction: 6).
- If NO previous feedback is available, score 6/6.

### 6. Objection Handling (Max: 3)
Did the customer raise objections? If YES, did the agent handle them correctly?
Common objections: price too high, need time to think, already studying elsewhere, parents need to decide, not sure about government jobs
- 3/3: Handled all objections effectively with correct information
- 2/3: Handled objections but could have been stronger
- 1/3: Attempted to handle but gave weak or incorrect responses
- 0/3: Failed to address objections or ignored them
- If NO objections were raised: Score 3/3 (mark as N/A in feedback)

### 7. Sale Attempt (Max: 5)
Did the agent actively try to CONVERT the customer, or did they just treat it as an enquiry call?
- Asked about payment readiness
- Suggested a specific course/batch
- Tried to close with an offer or coupon
- Proposed a specific action (visit branch, make payment, attend demo)
SCORING:
- 5/5: Strong sale attempt with clear call-to-action
- 3-4/5: Moderate attempt, suggested next steps but didn't push for commitment
- 1-2/5: Passive - just answered questions without trying to convert
- 0/5: Pure enquiry handling with zero sales effort

## Output Format
Respond with ONLY valid JSON (no markdown, no explanation outside JSON):
{{
    "course_pitch": {{
        "score": <number>,
        "max_score": 5,
        "evidence": ["<exact transcript quote>", ...],
        "feedback": "<brief explanation>",
        "improvement": "<actionable suggestion>"
    }},
    "false_commitment": {{
        "score": <number>,
        "max_score": 5,
        "evidence": ["<quote showing false commitment, or 'None detected'>"],
        "feedback": "<explanation>",
        "improvement": "<suggestion>"
    }},
    "presentation": {{
        "score": <number>,
        "max_score": 10,
        "evidence": ["<transcript quotes>", ...],
        "feedback": "<explanation>",
        "improvement": "<suggestion>"
    }},
    "urgency_need": {{
        "score": <number>,
        "max_score": 10,
        "evidence": ["<transcript quotes>", ...],
        "feedback": "<explanation of customer type and whether urgency was appropriate>",
        "improvement": "<suggestion>"
    }},
    "repeated_mistakes": {{
        "score": <number>,
        "max_score": 6,
        "evidence": ["<specific repeated mistake, or 'No previous feedback available'>"],
        "feedback": "<explanation>",
        "improvement": "<suggestion>"
    }},
    "objection_handling": {{
        "score": <number>,
        "max_score": 3,
        "evidence": ["<objection + response quotes>"],
        "feedback": "<explanation>",
        "improvement": "<suggestion>"
    }},
    "sale_attempt": {{
        "score": <number>,
        "max_score": 5,
        "evidence": ["<transcript quotes showing sale attempt>"],
        "feedback": "<explanation>",
        "improvement": "<suggestion>"
    }},
    "overall_strengths": ["<strength 1>", "<strength 2>", ...],
    "overall_weaknesses": ["<weakness 1>", "<weakness 2>", ...],
    "critical_issues": ["<critical issue if any>"],
    "call_summary": "<one paragraph summary of the call and agent performance>"
}}

## Transcript
{transcript}"""


def build_full_evaluation_prompt(
    transcript: str,
    previous_feedback: str | None = None,
) -> str:
    """Build evaluation prompt for non-English calls where LLM scores ALL parameters."""

    prev_feedback_section = ""
    if previous_feedback:
        prev_feedback_section = f"""
## Previous QA Feedback for This Agent
The following feedback was given in a prior evaluation. Check if any of these mistakes are REPEATED in this call:
{previous_feedback}
"""

    return f"""## Task
Evaluate the following sales call transcript against ALL QA parameters below. The call is in a regional Indian language (Tamil, Malayalam, Hindi, etc.) — evaluate based on the MEANING and INTENT of what was said, not the language.

{prev_feedback_section}

## Parameters to Score

### 1. Greeting (Max: 5)
Did the agent greet properly with name + company name (Veranda Race)?
- 5/5: Warm greeting + agent name + "Veranda Race"
- 3-4/5: Partial greeting (missing name or company)
- 0-2/5: No proper greeting

### 2. Probing / Customer Identification (Max: 5)
Did the agent collect customer details: name, age, qualification, location, preferred mode (online/offline)?
- 5/5: Asked all 5 details
- 1 point per detail collected

### 3. Primary Lead Source Identification (Max: 5)
Did the agent ask how the customer found Veranda Race?
- 5/5: Asked about lead source
- 0/5: Did not ask

### 4. Course Pitch & Opportunities (Max: 5)
Did the agent pitch the suitable course based on customer's profile?
- 5/5: Pitched correct course with posts, exam pattern, vacancies, salary
- 3-4/5: Mentioned course and some opportunities
- 0-2/5: Vague or no course pitching

### 5. No False Commitment (Max: 5)
PENALTY parameter. Default 5/5. Deduct for false promises like "guaranteed job", "100% selection".

### 6. 6 Level Strategy Explanation (Max: 10)
Did agent explain the 6-level practice methodology (Basic Class, Basic Circle, Extremer Circle, Superbatch, RIP, Mock Interview)?
- ~1.7 points per level mentioned

### 7. Presentation & Messaging (Max: 10)
Overall quality of communication: professional tone, value proposition, success stories, mentor support, study materials.
- 9-10/10: Excellent presentation
- 6-8/10: Good with gaps
- 3-5/10: Basic but poorly structured
- 0-2/10: Poor communication

### 8. Urgency Creation Need (Max: 10)
Did the agent create appropriate urgency based on customer type?
- Score based on whether urgency was needed AND correctly applied

### 9. Urgency Explanation (Max: 8)
Did the agent use urgency tactics: exam notifications, fee increases, competition, age limits, limited seats?
- 2 marks per urgency point used (max 4 points)

### 10. Repeated Mistakes (Max: 6)
PENALTY parameter. Default 6/6. Deduct 2 per repeated mistake from previous feedback.

### 11. Objection Handling (Max: 3)
If customer raised objections, did agent handle them?
- 3/3 if handled well or no objections raised

### 12. Sale Attempt (Max: 5)
Did the agent try to convert? Asked about payment, suggested course/batch, proposed action?
- 5/5: Strong sale attempt with clear CTA
- 0/5: Pure enquiry with zero sales effort

### 13. Further Assistance (Max: 3)
Did the agent ask "anything else?" and mention sharing details via WhatsApp?
- 2 points for "anything else", 1 point for WhatsApp mention

### 14. Closing (Max: 5)
Proper closing with thank you + follow-up scheduling + best wishes?
- 2 points for thank you, 2 for follow-up, 1 for best wishes

### 15. Call Handling Behavior (Max: 5)
Agent talk ratio, call duration, who ended the call?
- Deduct for: agent speaking too little (<30%) or too much (>85%), very short call (<1 min), customer ending call

## Output Format
Respond with ONLY valid JSON:
{{
    "greeting": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "probing": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "lead_source": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "course_pitch": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "false_commitment": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "six_level_strategy": {{"score": <n>, "max_score": 10, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "presentation": {{"score": <n>, "max_score": 10, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "urgency_need": {{"score": <n>, "max_score": 10, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "urgency_explanation": {{"score": <n>, "max_score": 8, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "repeated_mistakes": {{"score": <n>, "max_score": 6, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "objection_handling": {{"score": <n>, "max_score": 3, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "sale_attempt": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "further_assistance": {{"score": <n>, "max_score": 3, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "closing": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "call_handling": {{"score": <n>, "max_score": 5, "evidence": ["..."], "feedback": "...", "improvement": "..."}},
    "overall_strengths": ["..."],
    "overall_weaknesses": ["..."],
    "critical_issues": ["..."],
    "call_summary": "..."
}}

## Transcript
{transcript}"""


def _format_rule_context(rule_scores: dict) -> str:
    """Format rule engine scores as context for the LLM."""
    lines = []
    for param, data in rule_scores.items():
        lines.append(f"- {param}: {data['score']}/{data['max_score']} ({data['feedback']})")
    return "\n".join(lines)
