"""Dashboard endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models import Call, Debtor, PaymentPromise
from ..schemas import DashboardStats, RecentActivityItem

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    """Get aggregated statistics for the dashboard overview."""

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Total debtors
    total_debtors_result = await db.execute(select(func.count(Debtor.id)))
    total_debtors = total_debtors_result.scalar() or 0

    # Debtors by stage
    stage_result = await db.execute(
        select(Debtor.stage, func.count(Debtor.id)).group_by(Debtor.stage)
    )
    debtors_by_stage = {row[0]: row[1] for row in stage_result.fetchall()}

    # Calls today
    calls_today_result = await db.execute(
        select(func.count(Call.id)).where(Call.initiated_at >= today_start)
    )
    calls_today = calls_today_result.scalar() or 0

    # Calls this week
    calls_week_result = await db.execute(
        select(func.count(Call.id)).where(Call.initiated_at >= week_start)
    )
    calls_this_week = calls_week_result.scalar() or 0

    # Calls this month
    calls_month_result = await db.execute(
        select(func.count(Call.id)).where(Call.initiated_at >= month_start)
    )
    calls_this_month = calls_month_result.scalar() or 0

    # Outcomes today
    outcomes_result = await db.execute(
        select(Call.outcome, func.count(Call.id))
        .where(Call.initiated_at >= today_start)
        .where(Call.outcome.isnot(None))
        .group_by(Call.outcome)
    )
    outcomes_today = {row[0]: row[1] for row in outcomes_result.fetchall()}

    # Total amount owed
    amount_result = await db.execute(
        select(func.sum(Debtor.amount_owed)).where(Debtor.opted_out == False)
    )
    total_amount_owed = amount_result.scalar() or 0

    # Total promises pending
    promises_result = await db.execute(
        select(func.sum(PaymentPromise.amount)).where(
            PaymentPromise.status == "pending"
        )
    )
    total_promises_pending = promises_result.scalar() or 0

    # Recent activity (last 10 completed calls)
    recent_calls_result = await db.execute(
        select(Call, Debtor)
        .join(Debtor, Call.debtor_id == Debtor.id)
        .where(Call.status == "completed")
        .order_by(Call.ended_at.desc())
        .limit(10)
    )
    recent_activity = []
    for call, debtor in recent_calls_result.fetchall():
        activity_type = "call_completed"
        details = call.outcome or "Completed"
        if call.outcome == "promised_to_pay":
            activity_type = "promise_made"
            # Try to get promise amount
            promise_result = await db.execute(
                select(PaymentPromise).where(PaymentPromise.call_id == call.id).limit(1)
            )
            promise = promise_result.scalar_one_or_none()
            if promise:
                details = f"Promised ${promise.amount:,.2f} by {promise.promise_date}"

        recent_activity.append(
            RecentActivityItem(
                id=call.id,
                type=activity_type,
                debtor_name=debtor.full_name,
                timestamp=call.ended_at or call.initiated_at,
                details=details,
            )
        )

    return DashboardStats(
        total_debtors=total_debtors,
        debtors_by_stage=debtors_by_stage,
        calls_today=calls_today,
        calls_this_week=calls_this_week,
        calls_this_month=calls_this_month,
        outcomes_today=outcomes_today,
        total_amount_owed=total_amount_owed,
        total_promises_pending=total_promises_pending,
        recent_activity=recent_activity,
    )
