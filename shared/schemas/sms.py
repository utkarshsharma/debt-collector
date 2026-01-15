"""SMS-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from schemas.enums import DelinquencyStage, SMSStatus, SMSType


class SMSMessage(BaseModel):
    """Schema for sending an SMS message."""

    to_phone: str = Field(..., description="Recipient phone number in E.164 format")
    message: str = Field(..., min_length=1, max_length=1600, description="SMS message body")
    debtor_id: Optional[UUID] = Field(None, description="Associated debtor ID")
    campaign_id: Optional[UUID] = Field(None, description="Associated campaign ID")
    sms_type: SMSType = Field(default=SMSType.REMINDER, description="Purpose of the SMS")

    @field_validator("to_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone is in E.164 format."""
        v = v.strip()
        if not v.startswith("+"):
            raise ValueError("Phone must be in E.164 format (start with +)")
        if len(v) < 10 or len(v) > 15:
            raise ValueError("Phone must be 10-15 characters")
        return v


class SMSResponse(BaseModel):
    """Schema for SMS send response."""

    sid: str = Field(..., description="Twilio message SID")
    to_phone: str = Field(..., description="Recipient phone number")
    from_phone: str = Field(..., description="Sender phone number")
    status: SMSStatus = Field(..., description="Message status")
    message: str = Field(..., description="Message body sent")
    sms_type: SMSType = Field(..., description="Purpose of the SMS")
    debtor_id: Optional[UUID] = Field(None, description="Associated debtor ID")
    campaign_id: Optional[UUID] = Field(None, description="Associated campaign ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class SMSTemplateContext(BaseModel):
    """Context variables for SMS template rendering."""

    debtor_name: str = Field(..., description="Debtor's full name")
    company_name: str = Field(..., description="Company name")
    amount_owed: str = Field(..., description="Amount owed (formatted)")
    currency: str = Field(default="$", description="Currency symbol")
    due_date: Optional[str] = Field(None, description="Due date (formatted)")
    promise_date: Optional[str] = Field(None, description="Promise payment date")
    promise_amount: Optional[str] = Field(None, description="Promise amount")
    stage: DelinquencyStage = Field(
        default=DelinquencyStage.PRE_DELINQUENCY, description="Delinquency stage"
    )
