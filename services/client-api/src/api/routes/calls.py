"""Call endpoints."""

import asyncio
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from elevenlabs_integration import get_client as get_elevenlabs_client
from elevenlabs_integration.calls import get_conversation, make_outbound_call

from ...core.config import get_settings
from ...core.database import get_db
from ...models import Call, Debtor, PaymentPromise, SMSLog
from ..schemas import (
    CallDetail,
    CallListItem,
    PaginatedResponse,
    TriggerCallRequest,
    TriggerCallResponse,
)

router = APIRouter()
settings = get_settings()


@router.get("", response_model=PaginatedResponse[CallListItem])
async def list_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    debtor_id: UUID | None = None,
    status: str | None = None,
    outcome: str | None = None,
    sort_by: Literal["initiated_at", "duration_sec"] = "initiated_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CallListItem]:
    """List calls with pagination and filtering."""

    # Build query with join to get debtor name
    query = select(Call, Debtor).join(Debtor, Call.debtor_id == Debtor.id)

    # Apply filters
    if debtor_id:
        query = query.where(Call.debtor_id == debtor_id)
    if status:
        query = query.where(Call.status == status)
    if outcome:
        query = query.where(Call.outcome == outcome)

    # Count total
    count_query = select(func.count()).select_from(
        select(Call.id)
        .where(Call.debtor_id == debtor_id if debtor_id else True)
        .where(Call.status == status if status else True)
        .where(Call.outcome == outcome if outcome else True)
        .subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    if sort_by == "duration_sec":
        order_col = Call.duration_sec
    else:
        order_col = Call.initiated_at

    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute
    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        CallListItem(
            id=call.id,
            debtor_id=call.debtor_id,
            debtor_name=debtor.full_name,
            status=call.status,
            outcome=call.outcome,
            duration_sec=call.duration_sec,
            initiated_at=call.initiated_at,
            sentiment_score=call.sentiment_score,
        )
        for call, debtor in rows
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + limit < total,
    )


@router.get("/{call_id}", response_model=CallDetail)
async def get_call(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CallDetail:
    """Get detailed information about a call."""

    result = await db.execute(
        select(Call, Debtor).join(Debtor, Call.debtor_id == Debtor.id).where(Call.id == call_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Call not found")

    call, debtor = row

    # Get SMS messages for this call
    sms_result = await db.execute(
        select(SMSLog).where(SMSLog.call_id == call_id).order_by(SMSLog.sent_at)
    )
    sms_logs = sms_result.scalars().all()
    sms_messages = [
        {
            "id": str(sms.id),
            "to_phone": sms.to_phone,
            "message": sms.message,
            "status": sms.status,
            "sms_type": sms.sms_type,
            "sent_at": sms.sent_at.isoformat() if sms.sent_at else None,
        }
        for sms in sms_logs
    ]

    # Get payment promise if any
    promise_result = await db.execute(
        select(PaymentPromise).where(PaymentPromise.call_id == call_id).limit(1)
    )
    promise = promise_result.scalar_one_or_none()
    payment_promise = None
    if promise:
        payment_promise = {
            "id": str(promise.id),
            "amount": float(promise.amount),
            "promise_date": promise.promise_date.isoformat(),
            "status": promise.status,
        }

    return CallDetail(
        id=call.id,
        debtor_id=call.debtor_id,
        debtor_name=debtor.full_name,
        elevenlabs_conversation_id=call.elevenlabs_conversation_id,
        twilio_call_sid=call.twilio_call_sid,
        status=call.status,
        outcome=call.outcome,
        final_state=call.final_state,
        initiated_at=call.initiated_at,
        started_at=call.started_at,
        answered_at=call.answered_at,
        ended_at=call.ended_at,
        duration_sec=call.duration_sec,
        from_number=call.from_number,
        to_number=call.to_number,
        transcript=call.transcript,
        transcript_json=call.transcript_json,
        extraction=call.extraction,
        ai_summary=call.ai_summary,
        sentiment_score=call.sentiment_score,
        recording_url=call.recording_url,
        sms_messages=sms_messages,
        payment_promise=payment_promise,
    )


@router.post("/trigger", response_model=TriggerCallResponse, status_code=201)
async def trigger_call(
    request: TriggerCallRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> TriggerCallResponse:
    """Trigger an outbound call to a debtor."""

    # Get debtor
    result = await db.execute(select(Debtor).where(Debtor.id == request.debtor_id))
    debtor = result.scalar_one_or_none()

    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")

    if debtor.opted_out:
        raise HTTPException(status_code=400, detail="Debtor has opted out of calls")

    # Create call record
    call = Call(
        debtor_id=debtor.id,
        client_id=debtor.client_id,
        status="initiated",
        from_number=settings.twilio_phone_number,
        to_number=debtor.phone,
        initiated_at=datetime.now(),
    )
    db.add(call)
    await db.commit()
    await db.refresh(call)

    # Trigger ElevenLabs call
    try:
        response = make_outbound_call(
            to_number=debtor.phone,
            debtor_name=debtor.full_name,
            company_name="Demo Company",  # In production, get from client
            amount_owed=debtor.amount_owed or 0,
            due_date=debtor.due_date,
            account_number="1234",  # In production, from debtor metadata
            delinquency_stage=debtor.stage,
        )

        # Update call with ElevenLabs IDs
        conversation_id = (
            response.conversation_id
            if hasattr(response, "conversation_id")
            else response.get("conversation_id")
        )
        call_sid = (
            response.call_sid
            if hasattr(response, "call_sid")
            else response.get("callSid")
        )

        call.elevenlabs_conversation_id = conversation_id
        call.twilio_call_sid = call_sid
        call.status = "ringing"
        await db.commit()

        # Start background task to poll for completion
        background_tasks.add_task(
            poll_call_completion,
            call_id=call.id,
            conversation_id=conversation_id,
        )

        return TriggerCallResponse(
            call_id=call.id,
            debtor_id=debtor.id,
            conversation_id=conversation_id,
            twilio_call_sid=call_sid,
            status="ringing",
        )

    except Exception as e:
        call.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")


async def poll_call_completion(call_id: UUID, conversation_id: str):
    """Background task to poll ElevenLabs for call completion."""

    from ...core.database import async_session_maker

    delays = [5, 10, 15, 30, 30, 60, 60, 120]  # seconds

    for delay in delays:
        await asyncio.sleep(delay)

        try:
            # Get conversation status from ElevenLabs
            conversation = get_conversation(conversation_id)

            status = (
                conversation.status
                if hasattr(conversation, "status")
                else conversation.get("status")
            )

            if status in ("done", "failed"):
                # Update call record
                async with async_session_maker() as db:
                    result = await db.execute(select(Call).where(Call.id == call_id))
                    call = result.scalar_one_or_none()

                    if call:
                        call.status = "completed" if status == "done" else "failed"

                        # Extract duration
                        duration = (
                            conversation.call_duration_secs
                            if hasattr(conversation, "call_duration_secs")
                            else conversation.get("call_duration_secs")
                        )
                        if duration:
                            call.duration_sec = int(duration)
                            call.ended_at = datetime.now()

                        # Extract transcript
                        transcript = (
                            conversation.transcript
                            if hasattr(conversation, "transcript")
                            else conversation.get("transcript")
                        )
                        if transcript:
                            call.transcript_json = transcript
                            # Build readable transcript
                            lines = []
                            for turn in transcript:
                                role = turn.get("role", "unknown")
                                message = turn.get("message", "")
                                if message:
                                    speaker = "Agent" if role == "agent" else "User"
                                    lines.append(f"{speaker}: {message}")
                            call.transcript = "\n".join(lines)

                        # Extract analysis
                        analysis = (
                            conversation.analysis
                            if hasattr(conversation, "analysis")
                            else conversation.get("analysis")
                        )
                        if analysis:
                            call.ai_summary = analysis.get("transcript_summary")
                            # Try to determine outcome from transcript
                            # This would ideally use the CallExtraction schema

                        await db.commit()
                return

        except Exception as e:
            print(f"Error polling call {call_id}: {e}")
            continue

    # If we get here, call didn't complete within timeout
    async with async_session_maker() as db:
        result = await db.execute(select(Call).where(Call.id == call_id))
        call = result.scalar_one_or_none()
        if call and call.status not in ("completed", "failed"):
            call.status = "failed"
            await db.commit()
