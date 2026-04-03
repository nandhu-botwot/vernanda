import uuid
import aiofiles
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.database import get_db
from backend.models.call import Call
from backend.models.schemas import CallUploadResponse
from backend.services.pipeline import process_call

router = APIRouter(tags=["upload"])

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac", ".aac"}


@router.post("/calls/upload", response_model=CallUploadResponse, status_code=202)
async def upload_call(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    agent_name: str = Form(default=None),
    call_language: str = Form(default="en"),
    call_type: str = Form(default=None),
    previous_feedback: str = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file format: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Read file and check size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(413, f"File too large. Max: {settings.max_file_size_mb}MB")

    # Save to disk
    call_id = uuid.uuid4()
    stored_filename = f"{call_id}{ext}"
    file_path = settings.upload_path / stored_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create DB record
    call = Call(
        id=call_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size_bytes=len(content),
        status="UPLOADED",
        agent_name=agent_name,
        call_language=call_language,
        call_type=call_type,
        previous_feedback=previous_feedback,
    )
    db.add(call)
    await db.commit()

    # Kick off background processing
    background_tasks.add_task(process_call, str(call_id))

    return CallUploadResponse(
        call_id=call_id,
        status="UPLOADED",
        message="File uploaded successfully. Processing started.",
    )
