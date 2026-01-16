"""API-specific Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool


class TriggerCallRequest(BaseModel):
    """Request to trigger an outbound call."""

    debtor_id: UUID


class TriggerCallResponse(BaseModel):
    """Response after triggering a call."""

    call_id: UUID
    debtor_id: UUID
    conversation_id: str | None = None
    twilio_call_sid: str | None = None
    status: str = "initiated"


class RecentActivityItem(BaseModel):
    """A recent activity event for the dashboard."""

    id: UUID
    type: str  # call_started, call_completed, sms_sent, promise_made
    debtor_name: str
    timestamp: datetime
    details: str


class DashboardStats(BaseModel):
    """Aggregated statistics for the dashboard."""

    total_debtors: int = 0
    debtors_by_stage: dict[str, int] = Field(default_factory=dict)

    calls_today: int = 0
    calls_this_week: int = 0
    calls_this_month: int = 0

    outcomes_today: dict[str, int] = Field(default_factory=dict)

    total_amount_owed: Decimal = Decimal("0")
    total_promises_pending: Decimal = Decimal("0")

    recent_activity: list[RecentActivityItem] = Field(default_factory=list)


class DebtorListItem(BaseModel):
    """Debtor item for list display."""

    id: UUID
    full_name: str
    phone: str
    amount_owed: Decimal | None
    due_date: datetime | None
    stage: str
    last_call_at: datetime | None = None
    last_call_outcome: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CallListItem(BaseModel):
    """Call item for list display."""

    id: UUID
    debtor_id: UUID
    debtor_name: str
    status: str
    outcome: str | None
    duration_sec: int | None
    initiated_at: datetime
    sentiment_score: Decimal | None

    class Config:
        from_attributes = True


class CallDetail(BaseModel):
    """Detailed call information."""

    id: UUID
    debtor_id: UUID
    debtor_name: str

    # Identifiers
    elevenlabs_conversation_id: str | None
    twilio_call_sid: str | None

    # Status
    status: str
    outcome: str | None
    final_state: str | None

    # Timing
    initiated_at: datetime
    started_at: datetime | None
    answered_at: datetime | None
    ended_at: datetime | None
    duration_sec: int | None

    # Phone
    from_number: str | None
    to_number: str | None

    # Content
    transcript: str | None
    transcript_json: dict | None
    extraction: dict | None
    ai_summary: str | None
    sentiment_score: Decimal | None

    # Recording
    recording_url: str | None

    # Related data
    sms_messages: list[dict] = Field(default_factory=list)
    payment_promise: dict | None = None

    class Config:
        from_attributes = True
