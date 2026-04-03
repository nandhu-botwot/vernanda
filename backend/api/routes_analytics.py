from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.call import Call
from backend.models.report import QAReport
from backend.models.schemas import AgentStats, ParameterStats, AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    total_calls = (await db.execute(select(func.count(Call.id)))).scalar()
    total_evaluated = (await db.execute(select(func.count(QAReport.id)))).scalar()

    avg_result = await db.execute(select(func.avg(QAReport.total_score)))
    avg_score = avg_result.scalar() or 0.0

    # Grade distribution
    grade_rows = await db.execute(
        select(QAReport.grade, func.count(QAReport.id)).group_by(QAReport.grade)
    )
    grade_distribution = {row[0]: row[1] for row in grade_rows.all()}

    return AnalyticsSummary(
        total_calls=total_calls,
        total_evaluated=total_evaluated,
        avg_score=round(avg_score, 1),
        grade_distribution=grade_distribution,
    )


@router.get("/agents", response_model=list[AgentStats])
async def get_agent_stats(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Call.agent_name,
            func.count(QAReport.id).label("total_calls"),
            func.avg(QAReport.total_score).label("avg_score"),
            func.max(QAReport.total_score).label("best_score"),
            func.min(QAReport.total_score).label("worst_score"),
        )
        .join(QAReport, QAReport.call_id == Call.id)
        .where(Call.agent_name.isnot(None))
        .group_by(Call.agent_name)
        .order_by(func.avg(QAReport.total_score).desc())
    )
    result = await db.execute(query)
    rows = result.all()

    def _avg_grade(avg: float) -> str:
        if avg >= 90:
            return "A+"
        if avg >= 80:
            return "A"
        if avg >= 70:
            return "B+"
        if avg >= 60:
            return "B"
        if avg >= 50:
            return "C"
        if avg >= 40:
            return "D"
        return "F"

    return [
        AgentStats(
            agent_name=row[0],
            total_calls=row[1],
            avg_score=round(row[2], 1),
            best_score=round(row[3], 1),
            worst_score=round(row[4], 1),
            avg_grade=_avg_grade(row[2]),
        )
        for row in rows
    ]


@router.get("/parameters", response_model=list[ParameterStats])
async def get_parameter_stats(db: AsyncSession = Depends(get_db)):
    """Compute average score for each QA parameter across all reports."""
    result = await db.execute(select(QAReport.scores))
    all_scores = result.scalars().all()

    if not all_scores:
        return []

    # Aggregate across all reports
    param_totals: dict[str, dict] = {}
    for scores in all_scores:
        if not scores:
            continue
        for param_key, param_data in scores.items():
            if param_key not in param_totals:
                param_totals[param_key] = {"total": 0.0, "max": param_data.get("max_score", 0), "count": 0}
            param_totals[param_key]["total"] += param_data.get("score", 0)
            param_totals[param_key]["count"] += 1

    stats = []
    for param_key, data in param_totals.items():
        avg = data["total"] / data["count"] if data["count"] > 0 else 0
        max_possible = data["max"]
        stats.append(
            ParameterStats(
                parameter=param_key,
                avg_score=round(avg, 2),
                max_possible=max_possible,
                avg_percentage=round((avg / max_possible * 100) if max_possible > 0 else 0, 1),
            )
        )

    stats.sort(key=lambda s: s.avg_percentage)
    return stats
