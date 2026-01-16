"""Payment promise model."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class PaymentPromise(Base):
    """A payment commitment extracted from a call."""

    __tablename__ = "payment_promises"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    call_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id"),
        nullable=False,
    )
    debtor_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("debtors.id"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    promise_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="payment_promises")
    debtor: Mapped["Debtor"] = relationship("Debtor", back_populates="payment_promises")
