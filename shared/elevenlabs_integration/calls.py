"""
Outbound call functions for ElevenLabs Agents.

This module handles:
- Single outbound calls
- Batch calling for campaigns
- Call status checking
"""

import os
from decimal import Decimal
from datetime import date
from typing import Any

from . import get_client


def make_outbound_call(
    to_number: str,
    debtor_name: str,
    company_name: str,
    amount_owed: Decimal | float | str,
    due_date: date | str,
    account_number: str = "1234",
    agent_id: str | None = None,
    agent_phone_number_id: str | None = None,
    delinquency_stage: str = "early_delinquency",
) -> dict[str, Any]:
    """
    Make a single outbound call to a debtor.

    Args:
        to_number: Phone number to call in E.164 format (e.g., +15551234567)
        debtor_name: Name of the debtor
        company_name: Name of the client company
        amount_owed: Amount owed (will be formatted as currency)
        due_date: Payment due date
        account_number: Last 4 digits of account (for verification)
        agent_id: ElevenLabs agent ID (uses env var if not provided)
        agent_phone_number_id: Phone number ID to call from (uses env var if not provided)
        delinquency_stage: Stage for dynamic prompt adjustment

    Returns:
        Call response with conversation_id and callSid

    Example:
        >>> response = make_outbound_call(
        ...     to_number="+15551234567",
        ...     debtor_name="John Smith",
        ...     company_name="ABC Finance",
        ...     amount_owed=Decimal("150.00"),
        ...     due_date=date(2026, 1, 10),
        ... )
        >>> print(response["conversation_id"])
    """
    client = get_client()

    # Get IDs from environment if not provided
    agent_id = agent_id or os.environ.get("ELEVENLABS_AGENT_ID")
    agent_phone_number_id = agent_phone_number_id or os.environ.get(
        "ELEVENLABS_PHONE_NUMBER_ID"
    )

    if not agent_id:
        raise ValueError("agent_id or ELEVENLABS_AGENT_ID env var is required")
    if not agent_phone_number_id:
        raise ValueError(
            "agent_phone_number_id or ELEVENLABS_PHONE_NUMBER_ID env var is required"
        )

    # Format dynamic variables
    if isinstance(due_date, date):
        due_date_str = due_date.strftime("%B %d, %Y")  # e.g., "January 15, 2026"
    else:
        due_date_str = str(due_date)

    if isinstance(amount_owed, Decimal):
        amount_str = f"{amount_owed:,.2f}"
    else:
        amount_str = f"{float(amount_owed):,.2f}"

    # Make the call
    response = client.conversational_ai.twilio.outbound_call(
        agent_id=agent_id,
        agent_phone_number_id=agent_phone_number_id,
        to_number=to_number,
        conversation_initiation_client_data={
            "dynamic_variables": {
                "debtor_name": debtor_name,
                "company_name": company_name,
                "amount_owed": amount_str,
                "due_date": due_date_str,
                "account_number": account_number,
                "delinquency_stage": delinquency_stage,
            }
        },
    )

    return response


def submit_batch_calls(
    call_name: str,
    recipients: list[dict[str, Any]],
    agent_id: str | None = None,
    agent_phone_number_id: str | None = None,
    scheduled_time_unix: int | None = None,
    timezone: str | None = None,
) -> dict[str, Any]:
    """
    Submit a batch of outbound calls.

    Args:
        call_name: Name for this batch (e.g., "Campaign 123")
        recipients: List of recipient dicts with phone_number and dynamic_variables
        agent_id: ElevenLabs agent ID
        agent_phone_number_id: Phone number ID to call from
        scheduled_time_unix: Optional Unix timestamp to schedule calls
        timezone: Timezone for scheduling (e.g., "America/New_York")

    Returns:
        Batch response with batch_id and status

    Example:
        >>> recipients = [
        ...     {
        ...         "phone_number": "+15551234567",
        ...         "conversation_initiation_client_data": {
        ...             "dynamic_variables": {
        ...                 "debtor_name": "John Smith",
        ...                 "company_name": "ABC Finance",
        ...                 "amount_owed": "150.00",
        ...                 "due_date": "January 15, 2026",
        ...             }
        ...         }
        ...     }
        ... ]
        >>> batch = submit_batch_calls("Morning Campaign", recipients)
    """
    client = get_client()

    agent_id = agent_id or os.environ.get("ELEVENLABS_AGENT_ID")
    agent_phone_number_id = agent_phone_number_id or os.environ.get(
        "ELEVENLABS_PHONE_NUMBER_ID"
    )

    if not agent_id:
        raise ValueError("agent_id or ELEVENLABS_AGENT_ID env var is required")
    if not agent_phone_number_id:
        raise ValueError(
            "agent_phone_number_id or ELEVENLABS_PHONE_NUMBER_ID env var is required"
        )

    kwargs = {
        "call_name": call_name,
        "agent_id": agent_id,
        "agent_phone_number_id": agent_phone_number_id,
        "recipients": recipients,
    }

    if scheduled_time_unix:
        kwargs["scheduled_time_unix"] = scheduled_time_unix
    if timezone:
        kwargs["timezone"] = timezone

    return client.conversational_ai.batch_calling.submit(**kwargs)


def get_batch_status(batch_id: str) -> dict[str, Any]:
    """
    Get the status of a batch calling job.

    Args:
        batch_id: The batch ID to check

    Returns:
        Batch status with call counts and details
    """
    client = get_client()
    return client.conversational_ai.batch_calling.get(batch_id=batch_id)


def list_conversations(agent_id: str | None = None) -> list[dict[str, Any]]:
    """
    List recent conversations.

    Args:
        agent_id: Optional agent ID to filter by

    Returns:
        List of conversation records
    """
    client = get_client()
    agent_id = agent_id or os.environ.get("ELEVENLABS_AGENT_ID")

    if agent_id:
        return client.conversational_ai.conversations.list(agent_id=agent_id)
    return client.conversational_ai.conversations.list()


def get_conversation(conversation_id: str) -> dict[str, Any]:
    """
    Get details of a specific conversation including transcript.

    Args:
        conversation_id: The conversation ID

    Returns:
        Conversation details with transcript and metadata
    """
    client = get_client()
    return client.conversational_ai.conversations.get(
        conversation_id=conversation_id
    )
