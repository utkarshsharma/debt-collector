"""SMS messaging functions using Twilio."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from twilio.base.exceptions import TwilioRestException

from schemas.enums import SMSStatus, SMSType
from schemas.sms import SMSMessage, SMSResponse, SMSTemplateContext
from twilio_sms import get_client, get_from_number

logger = logging.getLogger(__name__)


def _map_twilio_status(twilio_status: str) -> SMSStatus:
    """Map Twilio message status to our SMSStatus enum."""
    status_map = {
        "queued": SMSStatus.QUEUED,
        "sending": SMSStatus.SENDING,
        "sent": SMSStatus.SENT,
        "delivered": SMSStatus.DELIVERED,
        "failed": SMSStatus.FAILED,
        "undelivered": SMSStatus.UNDELIVERED,
    }
    return status_map.get(twilio_status.lower(), SMSStatus.QUEUED)


def send_sms(
    to_phone: str,
    message: str,
    sms_type: SMSType = SMSType.REMINDER,
    debtor_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
) -> SMSResponse:
    """
    Send an SMS message via Twilio.

    Args:
        to_phone: Recipient phone number in E.164 format
        message: SMS message body (max 1600 chars)
        sms_type: Purpose of the SMS (reminder, confirmation, etc.)
        debtor_id: Associated debtor ID for tracking
        campaign_id: Associated campaign ID for tracking

    Returns:
        SMSResponse: Response with status and message details

    Raises:
        ValueError: If phone format is invalid or message is too long
        TwilioRestException: If Twilio API call fails
    """
    # Validate input using schema
    sms_message = SMSMessage(
        to_phone=to_phone,
        message=message,
        sms_type=sms_type,
        debtor_id=debtor_id,
        campaign_id=campaign_id,
    )

    client = get_client()
    from_number = get_from_number()

    log_context = {
        "to_phone": to_phone,
        "sms_type": sms_type.value,
        "debtor_id": str(debtor_id) if debtor_id else None,
        "campaign_id": str(campaign_id) if campaign_id else None,
    }

    logger.info("Sending SMS", extra={"step": "sms_send_start", **log_context})

    try:
        twilio_message = client.messages.create(
            body=sms_message.message,
            from_=from_number,
            to=sms_message.to_phone,
        )

        response = SMSResponse(
            sid=twilio_message.sid,
            to_phone=sms_message.to_phone,
            from_phone=from_number,
            status=_map_twilio_status(twilio_message.status),
            message=sms_message.message,
            sms_type=sms_type,
            debtor_id=debtor_id,
            campaign_id=campaign_id,
            created_at=datetime.utcnow(),
        )

        logger.info(
            "SMS sent successfully",
            extra={
                "step": "sms_send_success",
                "sid": twilio_message.sid,
                "status": twilio_message.status,
                **log_context,
            },
        )

        return response

    except TwilioRestException as e:
        logger.error(
            f"SMS send failed: {e.msg}",
            extra={
                "step": "sms_send_failed",
                "error_code": str(e.code),
                "error_message": e.msg,
                **log_context,
            },
        )

        # Return response with error details
        return SMSResponse(
            sid=f"error_{datetime.utcnow().timestamp()}",
            to_phone=sms_message.to_phone,
            from_phone=from_number,
            status=SMSStatus.FAILED,
            message=sms_message.message,
            sms_type=sms_type,
            debtor_id=debtor_id,
            campaign_id=campaign_id,
            created_at=datetime.utcnow(),
            error_code=str(e.code),
            error_message=e.msg,
        )


def send_sms_from_template(
    to_phone: str,
    template: str,
    context: SMSTemplateContext,
    sms_type: SMSType = SMSType.REMINDER,
    debtor_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
) -> SMSResponse:
    """
    Send an SMS using a template with variable substitution.

    Args:
        to_phone: Recipient phone number in E.164 format
        template: Message template with {{variable}} placeholders
        context: Template context with variable values
        sms_type: Purpose of the SMS
        debtor_id: Associated debtor ID for tracking
        campaign_id: Associated campaign ID for tracking

    Returns:
        SMSResponse: Response with status and message details
    """
    # Render template with context
    message = render_template(template, context)

    return send_sms(
        to_phone=to_phone,
        message=message,
        sms_type=sms_type,
        debtor_id=debtor_id,
        campaign_id=campaign_id,
    )


def render_template(template: str, context: SMSTemplateContext) -> str:
    """
    Render an SMS template with context variables.

    Uses {{variable}} syntax for substitution.

    Args:
        template: Message template with placeholders
        context: Context object with variable values

    Returns:
        str: Rendered message
    """
    message = template

    # Core variables (always present)
    message = message.replace("{{debtor_name}}", context.debtor_name)
    message = message.replace("{{company_name}}", context.company_name)
    message = message.replace("{{amount_owed}}", f"{context.currency}{context.amount_owed}")
    message = message.replace("{{currency}}", context.currency)

    # Optional variables
    if context.due_date:
        message = message.replace("{{due_date}}", context.due_date)
    if context.promise_date:
        message = message.replace("{{promise_date}}", context.promise_date)
    if context.promise_amount:
        message = message.replace("{{promise_amount}}", f"{context.currency}{context.promise_amount}")

    return message


def get_message_status(sid: str) -> SMSStatus:
    """
    Check the delivery status of an SMS message.

    Args:
        sid: Twilio message SID

    Returns:
        SMSStatus: Current status of the message
    """
    client = get_client()
    message = client.messages(sid).fetch()
    return _map_twilio_status(message.status)


__all__ = [
    "send_sms",
    "send_sms_from_template",
    "render_template",
    "get_message_status",
]
