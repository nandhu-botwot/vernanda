from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.call import Call
from backend.models.report import QAReport
from backend.models.schemas import CallDetail, CallStatusResponse, CallListItem, CallListResponse
from backend.services.pipeline import process_call

router = APIRouter(tags=["calls"])


@router.get("/calls/{call_id}/status", response_model=CallStatusResponse)
async def get_call_status(call_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(404, "Call not found")
    return CallStatusResponse(
        call_id=call.id,
        status=call.status,
        error_message=call.error_message,
    )


@router.get("/calls/{call_id}", response_model=CallDetail)
async def get_call(call_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(404, "Call not found")
    return CallDetail.model_validate(call)


@router.get("/calls", response_model=CallListResponse)
async def list_calls(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    agent_name: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Call)
    count_query = select(func.count(Call.id))

    if status:
        query = query.where(Call.status == status)
        count_query = count_query.where(Call.status == status)
    if agent_name:
        query = query.where(Call.agent_name.ilike(f"%{agent_name}%"))
        count_query = count_query.where(Call.agent_name.ilike(f"%{agent_name}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    offset = (page - 1) * limit
    query = query.order_by(desc(Call.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    calls = result.scalars().all()

    # Attach scores from reports
    items = []
    for call in calls:
        report_result = await db.execute(
            select(QAReport.total_score, QAReport.grade).where(QAReport.call_id == call.id)
        )
        report_row = report_result.first()

        item = CallListItem(
            id=call.id,
            filename=call.filename,
            duration_seconds=call.duration_seconds,
            status=call.status,
            agent_name=call.agent_name,
            call_language=call.call_language,
            call_type=call.call_type,
            total_score=report_row[0] if report_row else None,
            grade=report_row[1] if report_row else None,
            created_at=call.created_at,
        )
        items.append(item)

    return CallListResponse(calls=items, total=total, page=page, limit=limit)


@router.post("/calls/{call_id}/retry")
async def retry_call(
    call_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise HTTPException(404, "Call not found")
    if call.status != "FAILED":
        raise HTTPException(400, "Only FAILED calls can be retried")
    if call.retry_count >= 3:
        raise HTTPException(400, "Maximum retry attempts reached")

    call.status = "UPLOADED"
    call.error_message = None
    call.retry_count += 1
    await db.commit()

    background_tasks.add_task(process_call, str(call_id))
    return {"message": "Retry started", "retry_count": call.retry_count}
