#!/usr/bin/env python3
"""Create the ElevenLabs debt collection agent."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))

from prompts.debt_collection import EARLY_DELINQUENCY_PROMPT
from elevenlabs import ElevenLabs

FIRST_MESSAGE = (
    "Hello, this is Eric calling from {{company_name}}. "
    "May I speak with {{debtor_name}}?"
)

def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set")
        sys.exit(1)
    if not voice_id:
        print("❌ ELEVENLABS_VOICE_ID not set")
        sys.exit(1)

    print("=" * 60)
    print("  Creating ElevenLabs Debt Collection Agent")
    print("=" * 60)
    print()
    print(f"  Voice ID: {voice_id} (Eric)")
    print(f"  LLM: gpt-5.2")
    print()

    client = ElevenLabs(api_key=api_key)

    try:
        response = client.conversational_ai.agents.create(
            name="Debt Collection Agent",
            conversation_config={
                "agent": {
                    "first_message": FIRST_MESSAGE,
                    "language": "en",
                    "prompt": {
                        "prompt": EARLY_DELINQUENCY_PROMPT,
                        "llm": "gpt-5.2",
                        "temperature": 0.3,
                        "max_tokens": 150,
                    },
                },
                "asr": {
                    "quality": "high",
                    "provider": "elevenlabs",
                },
                "tts": {
                    "model_id": "eleven_turbo_v2",
                    "voice_id": voice_id,
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                },
                "turn": {
                    "mode": "turn",
                    "turn_timeout": 7,
                },
            },
            platform_settings={
                "auth": {"enable_auth": False},
                "call_limits": {"max_call_duration_seconds": 600},
            },
        )

        # Extract agent_id from response
        agent_id = response.agent_id if hasattr(response, 'agent_id') else response.get('agent_id')

        print("✅ Agent created successfully!")
        print()
        print(f"  Agent ID: {agent_id}")
        print()
        print("  Add this to your .env file:")
        print(f"  ELEVENLABS_AGENT_ID={agent_id}")
        print()

        return agent_id

    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
