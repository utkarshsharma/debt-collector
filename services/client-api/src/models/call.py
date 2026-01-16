"""Call model."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Call(Base):
    """A call record with ElevenLabs conversation data."""

    __tablename__ = "calls"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    debtor_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("debtors.id"),
        nullable=False,
    )
    client_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
    )

    # ElevenLabs/Twilio identifiers
    elevenlabs_conversation_id: Mapped[str | None] = mapped_column(String(100))
    twilio_call_sid: Mapped[str | None] = mapped_column(String(100))

    # Call status and outcome
    status: Mapped[str] = mapped_column(String(30), default="initiated")
    outcome: Mapped[str | None] = mapped_column(String(30))
    final_state: Mapped[str | None] = mapped_column(String(30))

    # Timing
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_sec: Mapped[int | None] = mapped_column(Integer)

    # Phone numbers
    from_number: Mapped[str | None] = mapped_column(String(20))
    to_number: Mapped[str | None] = mapped_column(String(20))

    # Conversation content
    transcript: Mapped[str | None] = mapped_column(Text)
    transcript_json: Mapped[dict | None] = mapped_column(JSONB)

    # Extracted data (from CallExtraction schema)
    extraction: Mapped[dict | None] = mapped_column(JSONB)

    # Analysis
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    ai_summary: Mapped[str | None] = mapped_column(Text)

    # Recording
    recording_url: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    debtor: Mapped["Debtor"] = relationship("Debtor", back_populates="calls")
    client: Mapped["Client"] = relationship("Client", back_populates="calls")
    payment_promises: Mapped[list["PaymentPromise"]] = relationship(
        "PaymentPromise",
        back_populates="call",
        cascade="all, delete-orphan",
    )
    sms_logs: Mapped[list["SMSLog"]] = relationship(
        "SMSLog",
        back_populates="call",
    )
