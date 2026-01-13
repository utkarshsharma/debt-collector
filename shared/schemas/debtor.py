"""Debtor-related Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from schemas.enums import DelinquencyStage


class DebtorBase(BaseModel):
    """Base debtor fields shared across schemas."""

    external_id: Optional[str] = Field(None, description="Client's internal ID for this debtor")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: str = Field(..., description="Phone number in E.164 format")
    email: Optional[str] = Field(None, max_length=255)
    timezone: str = Field(default="America/New_York", max_length=50)
    amount_owed: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    due_date: Optional[date] = None
    stage: DelinquencyStage = Field(default=DelinquencyStage.PRE_DELINQUENCY)
    metadata: Optional[dict] = Field(default=None, description="Flexible client-specific data")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone is in E.164 format."""
        v = v.strip()
        if not v.startswith("+"):
            raise ValueError("Phone must be in E.164 format (start with +)")
        if len(v) < 10 or len(v) > 15:
            raise ValueError("Phone must be 10-15 characters")
        return v


class DebtorCreate(DebtorBase):
    """Schema for creating a new debtor."""

    pass


class DebtorUpdate(BaseModel):
    """Schema for updating an existing debtor."""

    external_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None
    amount_owed: Optional[Decimal] = None
    currency: Optional[str] = None
    due_date: Optional[date] = None
    stage: Optional[DelinquencyStage] = None
    metadata: Optional[dict] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone is in E.164 format if provided."""
        if v is None:
            return v
        v = v.strip()
        if not v.startswith("+"):
            raise ValueError("Phone must be in E.164 format (start with +)")
        if len(v) < 10 or len(v) > 15:
            raise ValueError("Phone must be 10-15 characters")
        return v


class DebtorResponse(DebtorBase):
    """Schema for debtor response."""

    id: UUID
    client_id: UUID
    opted_out: bool = False
    opted_out_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
