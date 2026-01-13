"""Enum definitions for debt collector system."""

from enum import Enum


class DelinquencyStage(str, Enum):
    """Stage of delinquency for a debtor."""

    PRE_DELINQUENCY = "pre_delinquency"
    EARLY_DELINQUENCY = "early_delinquency"
    LATE_DELINQUENCY = "late_delinquency"


class CampaignStatus(str, Enum):
    """Status of a call campaign."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CampaignDebtorStatus(str, Enum):
    """Status of a debtor within a campaign."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    EXHAUSTED = "exhausted"
    OPTED_OUT = "opted_out"


class CallStatus(str, Enum):
    """Status of an individual call."""

    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"


class CallOutcome(str, Enum):
    """Outcome of a completed call."""

    PROMISED_TO_PAY = "promised_to_pay"
    PARTIAL_PROMISE = "partial_promise"
    DISPUTED = "disputed"
    HARDSHIP = "hardship"
    WRONG_NUMBER = "wrong_number"
    CALLBACK_REQUESTED = "callback_requested"
    HUNG_UP = "hung_up"
    NO_ANSWER = "no_answer"
    VOICEMAIL_LEFT = "voicemail_left"
    OTHER = "other"


class PromiseStatus(str, Enum):
    """Status of a payment promise."""

    PENDING = "pending"
    OVERDUE = "overdue"
    PARTIAL = "partial"
    FULFILLED = "fulfilled"
    BROKEN = "broken"


class CallState(str, Enum):
    """State machine states for a call conversation."""

    GREETING = "greeting"
    VERIFICATION = "verification"
    PURPOSE = "purpose"
    NEGOTIATION = "negotiation"
    OBJECTION_HANDLING = "objection_handling"
    COMMITMENT = "commitment"
    CLOSING = "closing"
    WRONG_NUMBER = "wrong_number"
    HARDSHIP = "hardship"
    CALLBACK = "callback"
