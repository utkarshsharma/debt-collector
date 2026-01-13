"""Tests for Pydantic schemas."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from schemas.enums import (
    DelinquencyStage,
    CallOutcome,
    CallState,
)
from schemas.debtor import DebtorCreate, DebtorUpdate, DebtorResponse
from schemas.call import CallExtraction, PaymentPromise


class TestDebtorSchemas:
    """Tests for debtor schemas."""

    def test_debtor_create_valid(self):
        """Test creating a valid debtor."""
        debtor = DebtorCreate(
            external_id="LOAN-123",
            first_name="John",
            last_name="Doe",
            phone="+15551234567",
            amount_owed=Decimal("1500.00"),
            due_date=date(2026, 2, 1),
            stage=DelinquencyStage.PRE_DELINQUENCY,
        )
        assert debtor.phone == "+15551234567"
        assert debtor.amount_owed == Decimal("1500.00")
        assert debtor.stage == DelinquencyStage.PRE_DELINQUENCY

    def test_debtor_create_invalid_phone_no_plus(self):
        """Test that phone without + is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DebtorCreate(phone="5551234567")
        assert "E.164 format" in str(exc_info.value)

    def test_debtor_create_invalid_phone_too_short(self):
        """Test that short phone is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DebtorCreate(phone="+123")
        assert "10-15 characters" in str(exc_info.value)

    def test_debtor_update_partial(self):
        """Test partial debtor update."""
        update = DebtorUpdate(amount_owed=Decimal("1200.00"))
        assert update.amount_owed == Decimal("1200.00")
        assert update.phone is None  # Not set

    def test_debtor_response_from_attributes(self):
        """Test debtor response can be created from ORM object."""
        # Simulate ORM object as dict
        data = {
            "id": uuid4(),
            "client_id": uuid4(),
            "external_id": "LOAN-123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+15551234567",
            "email": "john@example.com",
            "timezone": "America/New_York",
            "amount_owed": Decimal("1500.00"),
            "currency": "USD",
            "due_date": date(2026, 2, 1),
            "stage": DelinquencyStage.PRE_DELINQUENCY,
            "metadata": None,
            "opted_out": False,
            "opted_out_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        response = DebtorResponse(**data)
        assert response.phone == "+15551234567"


class TestCallExtraction:
    """Tests for CallExtraction schema (LLM output validation)."""

    def test_valid_extraction_with_promise(self):
        """Test valid call extraction with payment promise."""
        future_date = date.today() + timedelta(days=7)
        extraction = CallExtraction(
            confirmed_identity=True,
            speaking_with_debtor=True,
            wrong_number=False,
            outcome=CallOutcome.PROMISED_TO_PAY,
            promise_made=True,
            promise=PaymentPromise(amount=Decimal("500.00"), promise_date=future_date),
            debtor_sentiment=4,
            call_summary="Debtor confirmed identity and promised to pay $500 by next Friday.",
            final_state=CallState.COMMITMENT,
        )
        assert extraction.promise_made is True
        assert extraction.promise.amount == Decimal("500.00")

    def test_valid_extraction_no_promise(self):
        """Test valid call extraction without payment promise."""
        extraction = CallExtraction(
            confirmed_identity=True,
            speaking_with_debtor=True,
            wrong_number=False,
            outcome=CallOutcome.DISPUTED,
            promise_made=False,
            promise=None,
            dispute_reason="Claims already paid this debt",
            debtor_sentiment=2,
            call_summary="Debtor disputes the debt, claims it was already paid.",
            final_state=CallState.CLOSING,
        )
        assert extraction.promise_made is False
        assert extraction.promise is None
        assert extraction.dispute_reason is not None

    def test_invalid_promise_made_without_promise_details(self):
        """Test that promise_made=True requires promise details."""
        with pytest.raises(ValidationError) as exc_info:
            CallExtraction(
                confirmed_identity=True,
                speaking_with_debtor=True,
                outcome=CallOutcome.PROMISED_TO_PAY,
                promise_made=True,
                promise=None,  # Missing!
                debtor_sentiment=4,
                call_summary="Debtor promised to pay.",
                final_state=CallState.COMMITMENT,
            )
        assert "promise must be set when promise_made is True" in str(exc_info.value)

    def test_invalid_promise_details_without_promise_made(self):
        """Test that promise details without promise_made=True is rejected."""
        future_date = date.today() + timedelta(days=7)
        with pytest.raises(ValidationError) as exc_info:
            CallExtraction(
                confirmed_identity=True,
                speaking_with_debtor=True,
                outcome=CallOutcome.HUNG_UP,
                promise_made=False,
                promise=PaymentPromise(amount=Decimal("500.00"), promise_date=future_date),
                debtor_sentiment=2,
                call_summary="Debtor hung up.",
                final_state=CallState.CLOSING,
            )
        assert "promise must be None when promise_made is False" in str(exc_info.value)

    def test_invalid_sentiment_out_of_range(self):
        """Test that sentiment outside 1-5 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CallExtraction(
                confirmed_identity=True,
                speaking_with_debtor=True,
                outcome=CallOutcome.HUNG_UP,
                promise_made=False,
                debtor_sentiment=6,  # Invalid!
                call_summary="Debtor hung up.",
                final_state=CallState.CLOSING,
            )
        assert "less than or equal to 5" in str(exc_info.value)

    def test_invalid_promise_date_in_past(self):
        """Test that promise date in past is rejected."""
        past_date = date.today() - timedelta(days=7)
        with pytest.raises(ValidationError) as exc_info:
            PaymentPromise(amount=Decimal("500.00"), promise_date=past_date)
        assert "cannot be in the past" in str(exc_info.value)

    def test_invalid_promise_amount_zero(self):
        """Test that zero promise amount is rejected."""
        future_date = date.today() + timedelta(days=7)
        with pytest.raises(ValidationError) as exc_info:
            PaymentPromise(amount=Decimal("0.00"), promise_date=future_date)
        assert "greater than 0" in str(exc_info.value)

    def test_invalid_summary_too_short(self):
        """Test that summary too short is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CallExtraction(
                confirmed_identity=True,
                speaking_with_debtor=True,
                outcome=CallOutcome.HUNG_UP,
                promise_made=False,
                debtor_sentiment=2,
                call_summary="Short",  # Too short!
                final_state=CallState.CLOSING,
            )
        assert "at least 10 characters" in str(exc_info.value)
