"""Call-related Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from schemas.enums import CallStatus, CallOutcome, CallState


class CallCreate(BaseModel):
    """Schema for creating a new call record."""

    debtor_id: UUID
    campaign_id: Optional[UUID] = None


class CallResponse(BaseModel):
    """Schema for call response."""

    id: UUID
    debtor_id: UUID
    campaign_id: Optional[UUID] = None
    twilio_call_sid: Optional[str] = None
    status: CallStatus
    outcome: Optional[CallOutcome] = None
    duration_sec: Optional[int] = None
    started_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    sentiment_score: Optional[Decimal] = None
    ai_summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentPromise(BaseModel):
    """Payment promise extracted from a call."""

    amount: Decimal = Field(..., gt=0, description="Promised payment amount")
    promise_date: date = Field(..., description="Promised payment date")

    @field_validator("promise_date")
    @classmethod
    def validate_date_in_future(cls, v: date) -> date:
        """Validate promise date is not in the past."""
        from datetime import date as date_type
        if v < date_type.today():
            raise ValueError("Promise date cannot be in the past")
        return v


class CallExtraction(BaseModel):
    """
    Structured data extracted from a call by the LLM.

    This schema is used for LLM output validation (eval layer).
    All fields must be explicitly set by the LLM - no defaults that hide missing data.
    """

    # Identity verification
    confirmed_identity: bool = Field(..., description="Whether debtor identity was confirmed")
    speaking_with_debtor: bool = Field(..., description="Whether we reached the actual debtor")
    wrong_number: bool = Field(default=False, description="Whether this was a wrong number")

    # Call outcome
    outcome: CallOutcome = Field(..., description="Final outcome of the call")

    # Payment promise (if any)
    promise_made: bool = Field(default=False, description="Whether a payment promise was made")
    promise: Optional[PaymentPromise] = Field(
        default=None,
        description="Payment promise details if promise_made is True"
    )

    # Hardship/Dispute details
    hardship_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason given if debtor claims hardship"
    )
    dispute_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason given if debtor disputes the debt"
    )

    # Follow-up
    callback_requested: bool = Field(default=False, description="Whether debtor requested callback")
    preferred_callback_time: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Preferred callback time if requested"
    )

    # Opt-out
    requested_no_calls: bool = Field(default=False, description="Whether debtor requested no more calls")

    # Sentiment (1-5 scale)
    debtor_sentiment: int = Field(
        ...,
        ge=1,
        le=5,
        description="Debtor sentiment: 1=hostile, 3=neutral, 5=cooperative"
    )

    # Summary
    call_summary: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="1-2 sentence summary of the call"
    )

    # Final state
    final_state: CallState = Field(..., description="Final state of the conversation")

    @field_validator("promise")
    @classmethod
    def validate_promise_consistency(cls, v: Optional[PaymentPromise], info) -> Optional[PaymentPromise]:
        """Validate promise is set if promise_made is True."""
        promise_made = info.data.get("promise_made", False)
        if promise_made and v is None:
            raise ValueError("promise must be set when promise_made is True")
        if not promise_made and v is not None:
            raise ValueError("promise must be None when promise_made is False")
        return v
