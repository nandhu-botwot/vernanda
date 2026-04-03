"""ARQ background task definitions (for production use with Redis)."""

from arq import create_pool
from arq.connections import RedisSettings

from backend.config import settings
from backend.services.pipeline import process_call


async def process_call_task(ctx, call_id: str):
    """ARQ task wrapper for the processing pipeline."""
    await process_call(call_id)


class WorkerSettings:
    """ARQ worker settings."""
    functions = [process_call_task]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
    job_timeout = 1800  # 30 minutes max per job
