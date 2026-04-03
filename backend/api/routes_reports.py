from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.report import QAReport
from backend.models.schemas import QAReportResponse

router = APIRouter(tags=["reports"])


@router.get("/reports/{call_id}", response_model=QAReportResponse)
async def get_report(call_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QAReport).where(QAReport.call_id == call_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found for this call")
    return QAReportResponse.model_validate(report)
