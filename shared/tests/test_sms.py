"""Tests for SMS schemas and templates."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from schemas.enums import DelinquencyStage, SMSStatus, SMSType
from schemas.sms import SMSMessage, SMSResponse, SMSTemplateContext
from prompts.sms_templates import (
    get_template,
    get_reminder_template,
    REMINDER_PRE_DELINQUENCY,
    REMINDER_EARLY_DELINQUENCY,
    REMINDER_LATE_DELINQUENCY,
    CONFIRMATION_TEMPLATE,
    FOLLOW_UP_TEMPLATE,
    MISSED_CALL_TEMPLATE,
)
from twilio_sms.messages import render_template


class TestSMSMessage:
    """Tests for SMSMessage schema."""

    def test_valid_sms_message(self):
        """Test creating a valid SMS message."""
        msg = SMSMessage(
            to_phone="+15551234567",
            message="Hello, this is a test message.",
            sms_type=SMSType.REMINDER,
        )
        assert msg.to_phone == "+15551234567"
        assert msg.sms_type == SMSType.REMINDER

    def test_sms_message_with_ids(self):
        """Test SMS message with debtor and campaign IDs."""
        debtor_id = uuid4()
        campaign_id = uuid4()
        msg = SMSMessage(
            to_phone="+15551234567",
            message="Test message",
            debtor_id=debtor_id,
            campaign_id=campaign_id,
            sms_type=SMSType.CONFIRMATION,
        )
        assert msg.debtor_id == debtor_id
        assert msg.campaign_id == campaign_id

    def test_invalid_phone_no_plus(self):
        """Test that phone without + is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SMSMessage(to_phone="5551234567", message="Test")
        assert "E.164 format" in str(exc_info.value)

    def test_invalid_phone_too_short(self):
        """Test that short phone is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SMSMessage(to_phone="+123", message="Test")
        assert "10-15 characters" in str(exc_info.value)

    def test_invalid_message_empty(self):
        """Test that empty message is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SMSMessage(to_phone="+15551234567", message="")
        assert "at least 1 character" in str(exc_info.value)

    def test_invalid_message_too_long(self):
        """Test that message over 1600 chars is rejected."""
        long_message = "x" * 1601
        with pytest.raises(ValidationError) as exc_info:
            SMSMessage(to_phone="+15551234567", message=long_message)
        assert "at most 1600 characters" in str(exc_info.value)


class TestSMSResponse:
    """Tests for SMSResponse schema."""

    def test_valid_sms_response(self):
        """Test creating a valid SMS response."""
        response = SMSResponse(
            sid="SM1234567890abcdef",
            to_phone="+15551234567",
            from_phone="+15559876543",
            status=SMSStatus.SENT,
            message="Test message",
            sms_type=SMSType.REMINDER,
        )
        assert response.sid == "SM1234567890abcdef"
        assert response.status == SMSStatus.SENT
        assert response.error_code is None

    def test_sms_response_with_error(self):
        """Test SMS response with error details."""
        response = SMSResponse(
            sid="error_123",
            to_phone="+15551234567",
            from_phone="+15559876543",
            status=SMSStatus.FAILED,
            message="Test message",
            sms_type=SMSType.REMINDER,
            error_code="21211",
            error_message="Invalid 'To' Phone Number",
        )
        assert response.status == SMSStatus.FAILED
        assert response.error_code == "21211"


class TestSMSTemplateContext:
    """Tests for SMSTemplateContext schema."""

    def test_valid_context_minimal(self):
        """Test context with minimal required fields."""
        context = SMSTemplateContext(
            debtor_name="John Doe",
            company_name="ABC Company",
            amount_owed="150.00",
        )
        assert context.debtor_name == "John Doe"
        assert context.currency == "$"  # Default

    def test_valid_context_full(self):
        """Test context with all fields."""
        context = SMSTemplateContext(
            debtor_name="John Doe",
            company_name="ABC Company",
            amount_owed="150.00",
            currency="€",
            due_date="January 15, 2026",
            promise_date="January 20, 2026",
            promise_amount="75.00",
            stage=DelinquencyStage.EARLY_DELINQUENCY,
        )
        assert context.promise_date == "January 20, 2026"
        assert context.currency == "€"


class TestSMSTemplates:
    """Tests for SMS template selection and content."""

    def test_get_reminder_template_pre_delinquency(self):
        """Test pre-delinquency reminder template."""
        template = get_reminder_template(DelinquencyStage.PRE_DELINQUENCY)
        assert template == REMINDER_PRE_DELINQUENCY
        assert "friendly reminder" in template
        assert "due on" in template

    def test_get_reminder_template_early_delinquency(self):
        """Test early delinquency reminder template."""
        template = get_reminder_template(DelinquencyStage.EARLY_DELINQUENCY)
        assert template == REMINDER_EARLY_DELINQUENCY
        assert "was due on" in template

    def test_get_reminder_template_late_delinquency(self):
        """Test late delinquency reminder template."""
        template = get_reminder_template(DelinquencyStage.LATE_DELINQUENCY)
        assert template == REMINDER_LATE_DELINQUENCY
        assert "past due" in template
        assert "immediately" in template

    def test_get_template_by_type(self):
        """Test getting template by SMS type."""
        assert get_template(SMSType.REMINDER) == REMINDER_EARLY_DELINQUENCY
        assert get_template(SMSType.CONFIRMATION) == CONFIRMATION_TEMPLATE
        assert get_template(SMSType.FOLLOW_UP) == FOLLOW_UP_TEMPLATE
        assert get_template(SMSType.MISSED_CALL) == MISSED_CALL_TEMPLATE

    def test_get_template_reminder_with_stage(self):
        """Test reminder template varies by stage."""
        pre = get_template(SMSType.REMINDER, DelinquencyStage.PRE_DELINQUENCY)
        late = get_template(SMSType.REMINDER, DelinquencyStage.LATE_DELINQUENCY)
        assert pre != late
        assert "friendly reminder" in pre
        assert "past due" in late


class TestTemplateRendering:
    """Tests for template rendering with context variables."""

    def test_render_reminder_template(self):
        """Test rendering a reminder template."""
        context = SMSTemplateContext(
            debtor_name="John Doe",
            company_name="ABC Financial",
            amount_owed="150.00",
            due_date="January 15, 2026",
        )
        template = REMINDER_PRE_DELINQUENCY
        result = render_template(template, context)

        assert "John Doe" in result
        assert "ABC Financial" in result
        assert "$150.00" in result
        assert "January 15, 2026" in result
        assert "{{" not in result  # No unrendered variables

    def test_render_confirmation_template(self):
        """Test rendering a confirmation template."""
        context = SMSTemplateContext(
            debtor_name="Jane Smith",
            company_name="XYZ Collections",
            amount_owed="500.00",
            promise_date="January 20, 2026",
            promise_amount="250.00",
        )
        result = render_template(CONFIRMATION_TEMPLATE, context)

        assert "Jane Smith" in result
        assert "XYZ Collections" in result
        assert "$250.00" in result
        assert "January 20, 2026" in result

    def test_render_with_different_currency(self):
        """Test rendering with non-default currency."""
        context = SMSTemplateContext(
            debtor_name="Hans Mueller",
            company_name="Euro Bank",
            amount_owed="200.00",
            currency="€",
            due_date="15 Januar 2026",
        )
        template = REMINDER_EARLY_DELINQUENCY
        result = render_template(template, context)

        assert "€200.00" in result
        assert "Hans Mueller" in result

    def test_render_late_delinquency_urgency(self):
        """Test late delinquency template has urgent language."""
        context = SMSTemplateContext(
            debtor_name="Test User",
            company_name="Test Co",
            amount_owed="1000.00",
            due_date="December 1, 2025",
        )
        result = render_template(REMINDER_LATE_DELINQUENCY, context)

        assert "past due" in result
        assert "immediately" in result
        assert "$1000.00" in result
