"""
Twilio SMS integration for debt collection messaging.

This module provides:
- Client initialization
- SMS sending functionality
- Template-based message rendering
"""

import os
from twilio.rest import Client

# Lazy initialization - client is created on first use
_client: Client | None = None


def get_client() -> Client:
    """
    Get the Twilio client singleton.

    Initializes the client on first call using TWILIO_ACCOUNT_SID and
    TWILIO_AUTH_TOKEN env vars.

    Returns:
        Client: The initialized Twilio client

    Raises:
        ValueError: If required environment variables are not set
    """
    global _client

    if _client is None:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

        if not account_sid:
            raise ValueError(
                "TWILIO_ACCOUNT_SID environment variable is required. "
                "Get your Account SID from https://console.twilio.com"
            )
        if not auth_token:
            raise ValueError(
                "TWILIO_AUTH_TOKEN environment variable is required. "
                "Get your Auth Token from https://console.twilio.com"
            )

        _client = Client(account_sid, auth_token)

    return _client


def reset_client() -> None:
    """Reset the client singleton. Useful for testing."""
    global _client
    _client = None


def get_from_number() -> str:
    """
    Get the Twilio phone number to send SMS from.

    Returns:
        str: The Twilio phone number in E.164 format

    Raises:
        ValueError: If TWILIO_PHONE_NUMBER is not set
    """
    from_number = os.environ.get("TWILIO_PHONE_NUMBER")
    if not from_number:
        raise ValueError(
            "TWILIO_PHONE_NUMBER environment variable is required. "
            "This is your Twilio phone number in E.164 format."
        )
    return from_number


__all__ = ["get_client", "reset_client", "get_from_number"]
