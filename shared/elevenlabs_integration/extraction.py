"""
Post-call data extraction using GPT-5.2.

This module extracts structured CallExtraction data from conversation transcripts.
"""

import json
import os
from typing import Any

from openai import OpenAI

from ..prompts.extraction import EXTRACTION_PROMPT
from ..schemas.call import CallExtraction


# Lazy initialization
_openai_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """Get the OpenAI client singleton."""
    global _openai_client

    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Get your API key from https://platform.openai.com/api-keys"
            )
        _openai_client = OpenAI(api_key=api_key)

    return _openai_client


async def extract_call_data_async(transcript: str) -> CallExtraction:
    """
    Extract structured call data from a transcript using GPT-5.2.

    Args:
        transcript: The full conversation transcript

    Returns:
        Validated CallExtraction object

    Raises:
        ValueError: If extraction fails validation
    """
    from openai import AsyncOpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    client = AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Transcript:\n\n{transcript}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw_extraction = json.loads(response.choices[0].message.content)
    return CallExtraction(**raw_extraction)


def extract_call_data(transcript: str) -> CallExtraction:
    """
    Extract structured call data from a transcript using GPT-5.2 (sync version).

    Args:
        transcript: The full conversation transcript

    Returns:
        Validated CallExtraction object

    Raises:
        ValueError: If extraction fails validation
    """
    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Transcript:\n\n{transcript}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw_extraction = json.loads(response.choices[0].message.content)
    return CallExtraction(**raw_extraction)


def extract_from_conversation(conversation_id: str) -> CallExtraction:
    """
    Extract call data from an ElevenLabs conversation by ID.

    Fetches the transcript from ElevenLabs and extracts structured data.

    Args:
        conversation_id: ElevenLabs conversation ID

    Returns:
        Validated CallExtraction object
    """
    from .calls import get_conversation

    # Get the conversation from ElevenLabs
    conversation = get_conversation(conversation_id)

    # Extract the transcript
    transcript = conversation.get("transcript", "")
    if not transcript:
        raise ValueError(f"No transcript found for conversation {conversation_id}")

    # Extract structured data
    return extract_call_data(transcript)
