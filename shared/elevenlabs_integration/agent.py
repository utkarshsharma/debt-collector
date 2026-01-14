"""
ElevenLabs Agent creation and management.

This module handles creating and configuring the debt collection agent
via the ElevenLabs Agents Platform API.
"""

import os
from typing import Any

from . import get_client
from ..prompts.debt_collection import get_system_prompt, DelinquencyStage


# Default voice settings for debt collection (professional female voice)
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.7,
    "similarity_boost": 0.8,
    "speed": 1.0,
}

# Agent first message template
FIRST_MESSAGE = (
    "Hello, this is Sarah calling from {{company_name}}. "
    "May I speak with {{debtor_name}}?"
)


def create_debt_collection_agent(
    name: str = "Debt Collection Agent",
    stage: DelinquencyStage = "early_delinquency",
    voice_id: str | None = None,
    llm_model: str = "gpt-5.2",
    max_call_duration_seconds: int = 600,
) -> dict[str, Any]:
    """
    Create a new ElevenLabs agent for debt collection.

    Args:
        name: Display name for the agent
        stage: Delinquency stage for the system prompt
        voice_id: ElevenLabs voice ID (uses env var if not provided)
        llm_model: LLM model to use (default: gpt-5.2)
        max_call_duration_seconds: Max call duration (default: 10 minutes)

    Returns:
        Agent creation response with agent_id and configuration

    Raises:
        ValueError: If voice_id is not set
    """
    client = get_client()

    # Get voice ID from env if not provided
    if voice_id is None:
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
        if not voice_id:
            raise ValueError(
                "voice_id must be provided or ELEVENLABS_VOICE_ID env var must be set. "
                "Find voice IDs at https://elevenlabs.io/app/voice-library"
            )

    # Get the stage-specific system prompt
    system_prompt = get_system_prompt(stage)

    # Create the agent
    response = client.conversational_ai.agents.create(
        name=name,
        conversation_config={
            "agent": {
                "first_message": FIRST_MESSAGE,
                "language": "en",
                "prompt": {
                    "prompt": system_prompt,
                },
            },
            "asr": {
                "quality": "high",
                "provider": "elevenlabs",
            },
            "llm": {
                "model": llm_model,
                "temperature": 0.3,
                "max_tokens": 150,
            },
            "tts": {
                "model_id": "eleven_turbo_v2",
                "voice_id": voice_id,
                "stability": DEFAULT_VOICE_SETTINGS["stability"],
                "similarity_boost": DEFAULT_VOICE_SETTINGS["similarity_boost"],
            },
            "turn": {
                "mode": "turn_based",
                "turn_timeout": 7,
            },
        },
        platform_settings={
            "auth": {"enable_auth": False},
            "call_limits": {"max_call_duration_seconds": max_call_duration_seconds},
        },
    )

    return response


def get_agent(agent_id: str) -> dict[str, Any]:
    """
    Get an existing agent by ID.

    Args:
        agent_id: The agent ID to retrieve

    Returns:
        Agent configuration and details
    """
    client = get_client()
    return client.conversational_ai.agents.get(agent_id=agent_id)


def update_agent_prompt(
    agent_id: str,
    stage: DelinquencyStage,
) -> dict[str, Any]:
    """
    Update an agent's system prompt for a different delinquency stage.

    Args:
        agent_id: The agent ID to update
        stage: New delinquency stage for the prompt

    Returns:
        Updated agent configuration
    """
    client = get_client()
    system_prompt = get_system_prompt(stage)

    return client.conversational_ai.agents.update(
        agent_id=agent_id,
        conversation_config={
            "agent": {
                "prompt": {
                    "prompt": system_prompt,
                },
            },
        },
    )


def delete_agent(agent_id: str) -> None:
    """
    Delete an agent.

    Args:
        agent_id: The agent ID to delete
    """
    client = get_client()
    client.conversational_ai.agents.delete(agent_id=agent_id)


def list_agents() -> list[dict[str, Any]]:
    """
    List all agents in the workspace.

    Returns:
        List of agent configurations
    """
    client = get_client()
    return client.conversational_ai.agents.list()
