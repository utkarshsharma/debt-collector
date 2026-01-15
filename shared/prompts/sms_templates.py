"""
SMS message templates for debt collection.

Each template uses {{variable}} syntax for substitution:
- {{debtor_name}} - Debtor's name
- {{company_name}} - Client company name
- {{amount_owed}} - Formatted amount with currency (e.g., $150.00)
- {{due_date}} - Payment due date
- {{promise_date}} - Committed payment date
- {{promise_amount}} - Committed payment amount

Templates are organized by:
1. SMS Type (reminder, confirmation, follow_up, missed_call)
2. Delinquency Stage (pre, early, late)
"""

from typing import Literal

from schemas.enums import DelinquencyStage, SMSType

# =============================================================================
# REMINDER TEMPLATES - Sent before or after calls
# =============================================================================

REMINDER_PRE_DELINQUENCY = (
    "Hi {{debtor_name}}, this is a friendly reminder from {{company_name}}. "
    "Your payment of {{amount_owed}} is due on {{due_date}}. "
    "Please let us know if you have any questions."
)

REMINDER_EARLY_DELINQUENCY = (
    "Hi {{debtor_name}}, this is {{company_name}}. "
    "Your payment of {{amount_owed}} was due on {{due_date}}. "
    "Please call us to arrange payment or visit our website."
)

REMINDER_LATE_DELINQUENCY = (
    "{{debtor_name}}, your account with {{company_name}} is past due. "
    "Amount owed: {{amount_owed}}. Original due date: {{due_date}}. "
    "Please contact us immediately to discuss payment options."
)

# =============================================================================
# CONFIRMATION TEMPLATES - Sent after payment promises
# =============================================================================

CONFIRMATION_TEMPLATE = (
    "Hi {{debtor_name}}, this confirms your commitment to pay {{promise_amount}} "
    "to {{company_name}} by {{promise_date}}. Thank you for working with us."
)

CONFIRMATION_FULL_PAYMENT = (
    "Hi {{debtor_name}}, this confirms your commitment to pay {{amount_owed}} "
    "to {{company_name}} by {{promise_date}}. Thank you!"
)

CONFIRMATION_PARTIAL_PAYMENT = (
    "Hi {{debtor_name}}, this confirms your partial payment commitment of "
    "{{promise_amount}} to {{company_name}} by {{promise_date}}. "
    "We'll follow up about the remaining balance."
)

# =============================================================================
# FOLLOW-UP TEMPLATES - Sent before promise date
# =============================================================================

FOLLOW_UP_TEMPLATE = (
    "Hi {{debtor_name}}, reminder: your payment of {{promise_amount}} to "
    "{{company_name}} is due {{promise_date}}. Thank you."
)

FOLLOW_UP_DAY_BEFORE = (
    "Hi {{debtor_name}}, just a reminder that your payment of {{promise_amount}} "
    "to {{company_name}} is due tomorrow. Thank you for keeping your commitment."
)

FOLLOW_UP_DAY_OF = (
    "Hi {{debtor_name}}, your payment of {{promise_amount}} to {{company_name}} "
    "is due today. Thank you."
)

# =============================================================================
# MISSED CALL TEMPLATES - Sent after failed call attempts
# =============================================================================

MISSED_CALL_TEMPLATE = (
    "Hi {{debtor_name}}, we tried to reach you regarding your {{company_name}} "
    "account. Please call us back at your earliest convenience."
)

MISSED_CALL_WITH_AMOUNT = (
    "Hi {{debtor_name}}, {{company_name}} tried to reach you about your account. "
    "Amount due: {{amount_owed}}. Please call us back."
)

MISSED_CALL_URGENT = (
    "{{debtor_name}}, {{company_name}} has been trying to reach you about an "
    "important matter regarding your account ({{amount_owed}}). Please call us back today."
)


def get_reminder_template(stage: DelinquencyStage) -> str:
    """
    Get the appropriate reminder template for a delinquency stage.

    Args:
        stage: The delinquency stage

    Returns:
        The reminder template for that stage
    """
    templates = {
        DelinquencyStage.PRE_DELINQUENCY: REMINDER_PRE_DELINQUENCY,
        DelinquencyStage.EARLY_DELINQUENCY: REMINDER_EARLY_DELINQUENCY,
        DelinquencyStage.LATE_DELINQUENCY: REMINDER_LATE_DELINQUENCY,
    }
    return templates.get(stage, REMINDER_EARLY_DELINQUENCY)


def get_template(
    sms_type: SMSType,
    stage: DelinquencyStage = DelinquencyStage.EARLY_DELINQUENCY,
) -> str:
    """
    Get an SMS template by type and stage.

    Args:
        sms_type: The type of SMS (reminder, confirmation, follow_up, missed_call)
        stage: The delinquency stage (affects reminder tone)

    Returns:
        The appropriate template string
    """
    if sms_type == SMSType.REMINDER:
        return get_reminder_template(stage)
    elif sms_type == SMSType.CONFIRMATION:
        return CONFIRMATION_TEMPLATE
    elif sms_type == SMSType.FOLLOW_UP:
        return FOLLOW_UP_TEMPLATE
    elif sms_type == SMSType.MISSED_CALL:
        return MISSED_CALL_TEMPLATE
    else:
        return REMINDER_EARLY_DELINQUENCY


# Export all templates for direct access
__all__ = [
    # Reminder templates
    "REMINDER_PRE_DELINQUENCY",
    "REMINDER_EARLY_DELINQUENCY",
    "REMINDER_LATE_DELINQUENCY",
    # Confirmation templates
    "CONFIRMATION_TEMPLATE",
    "CONFIRMATION_FULL_PAYMENT",
    "CONFIRMATION_PARTIAL_PAYMENT",
    # Follow-up templates
    "FOLLOW_UP_TEMPLATE",
    "FOLLOW_UP_DAY_BEFORE",
    "FOLLOW_UP_DAY_OF",
    # Missed call templates
    "MISSED_CALL_TEMPLATE",
    "MISSED_CALL_WITH_AMOUNT",
    "MISSED_CALL_URGENT",
    # Helper functions
    "get_reminder_template",
    "get_template",
]
