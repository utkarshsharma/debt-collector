"""Debtor model."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Debtor(Base):
    """A person who owes money to a client company."""

    __tablename__ = "debtors"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    client_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(100))
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")
    amount_owed: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    due_date: Mapped[date | None] = mapped_column(Date)
    stage: Mapped[str] = mapped_column(String(30), default="pre_delinquency")
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False)
    opted_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="debtors")
    calls: Mapped[list["Call"]] = relationship(
        "Call",
        back_populates="debtor",
        cascade="all, delete-orphan",
    )
    payment_promises: Mapped[list["PaymentPromise"]] = relationship(
        "PaymentPromise",
        back_populates="debtor",
        cascade="all, delete-orphan",
    )
    sms_logs: Mapped[list["SMSLog"]] = relationship(
        "SMSLog",
        back_populates="debtor",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Return full name of debtor."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or "Unknown"
