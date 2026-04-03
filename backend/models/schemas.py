from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# --- Call Schemas ---

class CallUploadResponse(BaseModel):
    call_id: UUID
    status: str
    message: str


class CallStatusResponse(BaseModel):
    call_id: UUID
    status: str
    error_message: str | None = None


class CallDetail(BaseModel):
    id: UUID
    filename: str
    file_size_bytes: int
    duration_seconds: float | None
    status: str
    error_message: str | None
    agent_name: str | None
    call_language: str
    call_type: str | None
    transcript: str | None
    whisper_confidence: float | None
    stt_engine_used: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CallListItem(BaseModel):
    id: UUID
    filename: str
    duration_seconds: float | None
    status: str
    agent_name: str | None
    call_language: str
    call_type: str | None
    total_score: float | None = None
    grade: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CallListResponse(BaseModel):
    calls: list[CallListItem]
    total: int
    page: int
    limit: int


# --- Score Schemas ---

class ParameterScore(BaseModel):
    score: float
    max_score: float
    method: str  # "rule" | "hybrid" | "llm" | "user_input"
    evidence: list[str] = Field(default_factory=list)
    feedback: str = ""
    improvement: str = ""


class QAReportResponse(BaseModel):
    id: UUID
    call_id: UUID
    total_score: float
    grade: str
    scores: dict[str, ParameterScore]
    strengths: list[str] | None
    weaknesses: list[str] | None
    critical_issues: list[str] | None
    improvements: str | None
    call_summary: str | None
    llm_model: str | None
    prompt_version: str | None
    rule_engine_version: str | None
    eval_duration_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Analytics Schemas ---

class AgentStats(BaseModel):
    agent_name: str
    total_calls: int
    avg_score: float
    best_score: float
    worst_score: float
    avg_grade: str


class ParameterStats(BaseModel):
    parameter: str
    avg_score: float
    max_possible: float
    avg_percentage: float


class AnalyticsSummary(BaseModel):
    total_calls: int
    total_evaluated: int
    avg_score: float
    grade_distribution: dict[str, int]
