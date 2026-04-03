import uuid
import json
from datetime import datetime

from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, func, Uuid, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class JSONType(TypeDecorator):
    """JSON type that works with both PostgreSQL (native JSONB) and SQLite (TEXT)."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


class QAReport(Base):
    __tablename__ = "qa_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("calls.id", ondelete="CASCADE"), unique=True
    )

    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(2), nullable=False)

    scores: Mapped[dict] = mapped_column(JSONType, nullable=False)
    strengths: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    critical_issues: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    improvements: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    llm_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rule_engine_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    eval_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    call: Mapped["Call"] = relationship(back_populates="report")
