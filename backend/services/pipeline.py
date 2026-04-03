"""Pipeline orchestrator: ties all processing stages together."""

import logging
import traceback
import uuid

from sqlalchemy import select

from backend.models.database import async_session
from backend.models.call import Call
from backend.models.report import QAReport
from backend.services.audio_preprocessor import preprocess_audio, HAS_AUDIO_LIBS
from backend.services.fallback_stt import transcribe_with_openai_api
from backend.services.speaker_labeler import label_speakers, format_transcript
from backend.services.rule_engine import run_all_rules
from backend.services.llm_evaluator import evaluate_with_llm
from backend.services.score_merger import merge_scores
from backend.config import settings

logger = logging.getLogger(__name__)


async def process_call(call_id: str):
    """
    Full processing pipeline:
    1. Preprocess audio (noise reduction, normalization)
    2. Transcribe + diarize (WhisperX, fallback to OpenAI API)
    3. Label speakers (Agent vs Customer)
    4. Rule-based scoring
    5. LLM evaluation
    6. Merge scores and generate report
    """
    async with async_session() as db:
        result = await db.execute(select(Call).where(Call.id == uuid.UUID(call_id)))
        call = result.scalar_one_or_none()
        if not call:
            logger.error(f"Call {call_id} not found")
            return

        try:
            # --- Stage 1: Preprocess ---
            await _update_status(db, call, "PREPROCESSING")
            if HAS_AUDIO_LIBS:
                processed_path, duration = preprocess_audio(call.file_path)
                call.duration_seconds = duration
            else:
                logger.info("Audio libs not available, skipping preprocessing")
                processed_path = call.file_path

            # --- Stage 2: Transcribe + Diarize ---
            await _update_status(db, call, "TRANSCRIBING")
            if HAS_AUDIO_LIBS:
                try:
                    from backend.services.transcription import transcribe_and_diarize
                    transcription = transcribe_and_diarize(processed_path)
                except Exception as e:
                    logger.warning(f"WhisperX failed: {e}. Trying OpenAI API fallback.")
                    transcription = transcribe_with_openai_api(processed_path)
                    transcription["_fallback"] = True
            else:
                logger.info("Using OpenAI API for transcription (cloud mode)")
                transcription = transcribe_with_openai_api(processed_path)
                transcription["_fallback"] = True

            # Check confidence - fallback if too low
            if (
                transcription.get("confidence", 1.0) < settings.whisper_confidence_threshold
                and not transcription.get("_fallback")
            ):
                logger.info(f"Low confidence ({transcription['confidence']}), using OpenAI API fallback")
                transcription = transcribe_with_openai_api(processed_path)
                transcription["_fallback"] = True

            call.whisper_confidence = transcription["confidence"]
            call.stt_engine_used = "openai_api" if transcription.get("_fallback") else "whisperx"

            # --- Stage 3: Label speakers ---
            segments = label_speakers(transcription["segments"])
            transcript_text = format_transcript(segments)
            call.transcript = transcript_text

            # --- Stage 4: Evaluate ---
            await _update_status(db, call, "EVALUATING")

            # Rule-based scoring
            rule_scores = run_all_rules(segments)

            # LLM scoring
            llm_scores = evaluate_with_llm(
                transcript_text,
                rule_scores,
                previous_feedback=call.previous_feedback,
            )

            # Merge scores
            report_data = merge_scores(rule_scores, llm_scores)

            # --- Stage 5: Store report ---
            report = QAReport(
                call_id=call.id,
                total_score=report_data["total_score"],
                grade=report_data["grade"],
                scores=report_data["scores"],
                strengths=report_data["strengths"],
                weaknesses=report_data["weaknesses"],
                critical_issues=report_data["critical_issues"],
                improvements=report_data["improvements"],
                call_summary=report_data["call_summary"],
                llm_model=report_data["llm_model"],
                prompt_version=report_data["prompt_version"],
                rule_engine_version=report_data["rule_engine_version"],
                eval_duration_ms=report_data["eval_duration_ms"],
            )
            db.add(report)

            await _update_status(db, call, "COMPLETED")
            logger.info(f"Call {call_id} processed successfully. Score: {report_data['total_score']}/{100}")

        except Exception as e:
            logger.error(f"Pipeline failed for call {call_id}: {traceback.format_exc()}")
            call.status = "FAILED"
            call.error_message = str(e)[:500]
            await db.commit()


async def _update_status(db, call: Call, status: str):
    call.status = status
    await db.commit()
