"""
Twilio phone number setup for ElevenLabs Agents.

This module handles importing Twilio phone numbers into ElevenLabs
for native integration (ElevenLabs manages the Twilio connection).
"""

import os
from typing import Any

from . import get_client


def setup_twilio_phone_number(
    phone_number: str | None = None,
    twilio_account_sid: str | None = None,
    twilio_auth_token: str | None = None,
    agent_id: str | None = None,
    label: str = "Debt Collection Line",
) -> dict[str, Any]:
    """
    Import a Twilio phone number into ElevenLabs for native integration.

    ElevenLabs will automatically configure the Twilio number with the correct
    webhook settings to route calls to your agent.

    Args:
        phone_number: Twilio phone number in E.164 format (e.g., +15551234567)
        twilio_account_sid: Twilio Account SID (from Twilio Console)
        twilio_auth_token: Twilio Auth Token (from Twilio Console)
        agent_id: ElevenLabs agent ID to handle calls
        label: Display label for the phone number

    Returns:
        Phone number configuration with phone_number_id

    Note:
        If parameters are not provided, they will be read from environment variables:
        - TWILIO_PHONE_NUMBER
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - ELEVENLABS_AGENT_ID
    """
    client = get_client()

    # Fall back to environment variables
    phone_number = phone_number or os.environ.get("TWILIO_PHONE_NUMBER")
    twilio_account_sid = twilio_account_sid or os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_auth_token = twilio_auth_token or os.environ.get("TWILIO_AUTH_TOKEN")
    agent_id = agent_id or os.environ.get("ELEVENLABS_AGENT_ID")

    # Validate required fields
    missing = []
    if not phone_number:
        missing.append("phone_number (or TWILIO_PHONE_NUMBER env var)")
    if not twilio_account_sid:
        missing.append("twilio_account_sid (or TWILIO_ACCOUNT_SID env var)")
    if not twilio_auth_token:
        missing.append("twilio_auth_token (or TWILIO_AUTH_TOKEN env var)")
    if not agent_id:
        missing.append("agent_id (or ELEVENLABS_AGENT_ID env var)")

    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")

    # Import the phone number into ElevenLabs
    response = client.conversational_ai.phone_numbers.create(
        phone_number=phone_number,
        provider="twilio",
        twilio_account_sid=twilio_account_sid,
        twilio_auth_token=twilio_auth_token,
        agent_id=agent_id,
        label=label,
    )

    return response


def get_phone_number(phone_number_id: str) -> dict[str, Any]:
    """
    Get phone number configuration by ID.

    Args:
        phone_number_id: The phone number ID from ElevenLabs

    Returns:
        Phone number configuration
    """
    client = get_client()
    return client.conversational_ai.phone_numbers.get(
        phone_number_id=phone_number_id
    )


def list_phone_numbers() -> list[dict[str, Any]]:
    """
    List all phone numbers in the workspace.

    Returns:
        List of phone number configurations
    """
    client = get_client()
    return client.conversational_ai.phone_numbers.list()


def delete_phone_number(phone_number_id: str) -> None:
    """
    Remove a phone number from ElevenLabs.

    Note: This only removes it from ElevenLabs. The number remains
    in your Twilio account.

    Args:
        phone_number_id: The phone number ID to remove
    """
    client = get_client()
    client.conversational_ai.phone_numbers.delete(
        phone_number_id=phone_number_id
    )
