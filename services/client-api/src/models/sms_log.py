"""SMS log model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class SMSLog(Base):
    """A record of an SMS message sent during or after a call."""

    __tablename__ = "sms_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    call_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id"),
    )
    debtor_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("debtors.id"),
        nullable=False,
    )
    twilio_sid: Mapped[str | None] = mapped_column(String(100))
    to_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    from_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sms_type: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str | None] = mapped_column(String(30))
    error_code: Mapped[str | None] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    call: Mapped["Call | None"] = relationship("Call", back_populates="sms_logs")
    debtor: Mapped["Debtor"] = relationship("Debtor", back_populates="sms_logs")
