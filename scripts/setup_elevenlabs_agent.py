#!/usr/bin/env python3
"""
Setup script for ElevenLabs Debt Collection Agent.

This script:
1. Creates an ElevenLabs agent with debt collection prompts
2. (Optionally) Sets up Twilio phone number integration
3. (Optionally) Makes a test outbound call

Usage:
    # Create agent only
    python scripts/setup_elevenlabs_agent.py --create-agent

    # Setup phone number (requires agent to exist)
    python scripts/setup_elevenlabs_agent.py --setup-phone

    # Make test call (requires agent and phone to exist)
    python scripts/setup_elevenlabs_agent.py --test-call --to-number +15551234567

    # Do everything
    python scripts/setup_elevenlabs_agent.py --all --to-number +15551234567

Required environment variables:
    ELEVENLABS_API_KEY - Your ElevenLabs API key
    ELEVENLABS_VOICE_ID - Voice ID from ElevenLabs voice library

For phone setup (optional):
    TWILIO_ACCOUNT_SID - Twilio Account SID
    TWILIO_AUTH_TOKEN - Twilio Auth Token
    TWILIO_PHONE_NUMBER - Your Twilio phone number

For test calls (optional):
    ELEVENLABS_AGENT_ID - Agent ID (set after creation)
    ELEVENLABS_PHONE_NUMBER_ID - Phone number ID (set after phone setup)
"""

import argparse
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# Add shared package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_env_vars(required: list[str]) -> bool:
    """Check if required environment variables are set."""
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    return True


def create_agent(stage: str = "early_delinquency") -> str | None:
    """Create the ElevenLabs agent."""
    print("\n📦 Creating ElevenLabs Agent...")

    if not check_env_vars(["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]):
        return None

    from elevenlabs.agent import create_debt_collection_agent

    try:
        response = create_debt_collection_agent(
            name="Debt Collection Agent",
            stage=stage,
            llm_model="gpt-5.2",  # Using GPT-5.2 as requested
        )

        agent_id = response.agent_id if hasattr(response, "agent_id") else response.get("agent_id")
        print(f"✅ Agent created successfully!")
        print(f"   Agent ID: {agent_id}")
        print(f"   Stage: {stage}")
        print(f"\n   Add to your .env file:")
        print(f"   ELEVENLABS_AGENT_ID={agent_id}")

        return agent_id

    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return None


def setup_phone(agent_id: str | None = None) -> str | None:
    """Set up Twilio phone number with ElevenLabs."""
    print("\n📞 Setting up Twilio Phone Number...")

    required_vars = [
        "ELEVENLABS_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
    ]

    if not agent_id:
        required_vars.append("ELEVENLABS_AGENT_ID")

    if not check_env_vars(required_vars):
        return None

    from elevenlabs.phone import setup_twilio_phone_number

    try:
        response = setup_twilio_phone_number(agent_id=agent_id)

        phone_id = response.phone_number_id if hasattr(response, "phone_number_id") else response.get("phone_number_id")
        print(f"✅ Phone number configured successfully!")
        print(f"   Phone Number ID: {phone_id}")
        print(f"\n   Add to your .env file:")
        print(f"   ELEVENLABS_PHONE_NUMBER_ID={phone_id}")

        return phone_id

    except Exception as e:
        print(f"❌ Failed to setup phone: {e}")
        return None


def test_call(
    to_number: str,
    agent_id: str | None = None,
    phone_id: str | None = None,
) -> bool:
    """Make a test outbound call."""
    print(f"\n📱 Making test call to {to_number}...")

    required_vars = ["ELEVENLABS_API_KEY"]
    if not agent_id:
        required_vars.append("ELEVENLABS_AGENT_ID")
    if not phone_id:
        required_vars.append("ELEVENLABS_PHONE_NUMBER_ID")

    if not check_env_vars(required_vars):
        return False

    from elevenlabs.calls import make_outbound_call

    try:
        # Test data
        response = make_outbound_call(
            to_number=to_number,
            debtor_name="Test User",
            company_name="Test Finance Company",
            amount_owed=Decimal("150.00"),
            due_date=date.today() - timedelta(days=7),  # 7 days past due
            account_number="5678",
            agent_id=agent_id,
            agent_phone_number_id=phone_id,
            delinquency_stage="early_delinquency",
        )

        conversation_id = response.conversation_id if hasattr(response, "conversation_id") else response.get("conversation_id")
        call_sid = response.call_sid if hasattr(response, "call_sid") else response.get("callSid")

        print(f"✅ Call initiated successfully!")
        print(f"   Conversation ID: {conversation_id}")
        print(f"   Twilio Call SID: {call_sid}")
        print(f"\n   The phone at {to_number} should be ringing now!")

        return True

    except Exception as e:
        print(f"❌ Failed to make call: {e}")
        return False


def list_agents():
    """List all existing agents."""
    print("\n📋 Listing existing agents...")

    if not check_env_vars(["ELEVENLABS_API_KEY"]):
        return

    from elevenlabs.agent import list_agents

    try:
        agents = list_agents()
        if not agents:
            print("   No agents found.")
            return

        for agent in agents:
            agent_id = agent.agent_id if hasattr(agent, "agent_id") else agent.get("agent_id")
            name = agent.name if hasattr(agent, "name") else agent.get("name")
            print(f"   - {name}: {agent_id}")

    except Exception as e:
        print(f"❌ Failed to list agents: {e}")


def list_phones():
    """List all configured phone numbers."""
    print("\n📋 Listing configured phone numbers...")

    if not check_env_vars(["ELEVENLABS_API_KEY"]):
        return

    from elevenlabs.phone import list_phone_numbers

    try:
        phones = list_phone_numbers()
        if not phones:
            print("   No phone numbers configured.")
            return

        for phone in phones:
            phone_id = phone.phone_number_id if hasattr(phone, "phone_number_id") else phone.get("phone_number_id")
            number = phone.phone_number if hasattr(phone, "phone_number") else phone.get("phone_number")
            label = phone.label if hasattr(phone, "label") else phone.get("label", "No label")
            print(f"   - {label} ({number}): {phone_id}")

    except Exception as e:
        print(f"❌ Failed to list phones: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Setup ElevenLabs Debt Collection Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--create-agent",
        action="store_true",
        help="Create a new ElevenLabs agent",
    )
    parser.add_argument(
        "--setup-phone",
        action="store_true",
        help="Setup Twilio phone number with ElevenLabs",
    )
    parser.add_argument(
        "--test-call",
        action="store_true",
        help="Make a test outbound call",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Do all steps: create agent, setup phone, test call",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing agents and phone numbers",
    )
    parser.add_argument(
        "--to-number",
        type=str,
        help="Phone number to call for test (E.164 format, e.g., +15551234567)",
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="early_delinquency",
        choices=["pre_delinquency", "early_delinquency", "late_delinquency"],
        help="Delinquency stage for the agent prompt",
    )

    args = parser.parse_args()

    # Default to listing if no action specified
    if not any([args.create_agent, args.setup_phone, args.test_call, args.all, args.list]):
        args.list = True

    print("=" * 60)
    print("  ElevenLabs Debt Collection Agent Setup")
    print("=" * 60)

    agent_id = None
    phone_id = None

    if args.list:
        list_agents()
        list_phones()

    if args.create_agent or args.all:
        agent_id = create_agent(stage=args.stage)
        if not agent_id and args.all:
            print("\n❌ Stopping: Agent creation failed")
            return

    if args.setup_phone or args.all:
        phone_id = setup_phone(agent_id=agent_id)
        if not phone_id and args.all:
            print("\n❌ Stopping: Phone setup failed")
            return

    if args.test_call or args.all:
        if not args.to_number:
            print("\n❌ --to-number is required for test calls")
            return
        test_call(
            to_number=args.to_number,
            agent_id=agent_id,
            phone_id=phone_id,
        )

    print("\n" + "=" * 60)
    print("  Setup Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
