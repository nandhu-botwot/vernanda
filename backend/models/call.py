import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, Integer, DateTime, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="UPLOADED", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    call_language: Mapped[str] = mapped_column(String(10), default="en")
    call_type: Mapped[str | None] = mapped_column(String(10), nullable=True)

    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    whisper_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    stt_engine_used: Mapped[str | None] = mapped_column(String(30), nullable=True)

    previous_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    report: Mapped["QAReport"] = relationship(back_populates="call", uselist=False, cascade="all, delete-orphan")
