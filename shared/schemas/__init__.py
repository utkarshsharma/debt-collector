"""Shared Pydantic schemas for debt collector services."""

from schemas.enums import (
    DelinquencyStage,
    CampaignStatus,
    CampaignDebtorStatus,
    CallStatus,
    CallOutcome,
    PromiseStatus,
)
from schemas.debtor import DebtorCreate, DebtorResponse, DebtorUpdate
from schemas.call import CallCreate, CallResponse, CallExtraction

__all__ = [
    # Enums
    "DelinquencyStage",
    "CampaignStatus",
    "CampaignDebtorStatus",
    "CallStatus",
    "CallOutcome",
    "PromiseStatus",
    # Debtor schemas
    "DebtorCreate",
    "DebtorResponse",
    "DebtorUpdate",
    # Call schemas
    "CallCreate",
    "CallResponse",
    "CallExtraction",
]
