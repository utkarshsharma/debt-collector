"""
ElevenLabs Agents Platform integration for debt collection voice AI.

This module provides:
- Client initialization
- Agent creation and management
- Twilio phone number setup
- Outbound call triggering (single + batch)
- Post-call data extraction
"""

import os
from elevenlabs import ElevenLabs

# Lazy initialization - client is created on first use
_client: ElevenLabs | None = None


def get_client() -> ElevenLabs:
    """
    Get the ElevenLabs client singleton.

    Initializes the client on first call using ELEVENLABS_API_KEY env var.

    Returns:
        ElevenLabs: The initialized client

    Raises:
        ValueError: If ELEVENLABS_API_KEY is not set
    """
    global _client

    if _client is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY environment variable is required. "
                "Get your API key from https://elevenlabs.io/app/settings/api-keys"
            )
        _client = ElevenLabs(api_key=api_key)

    return _client


def reset_client() -> None:
    """Reset the client singleton. Useful for testing."""
    global _client
    _client = None


__all__ = ["get_client", "reset_client"]
