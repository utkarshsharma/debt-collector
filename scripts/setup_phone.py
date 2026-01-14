#!/usr/bin/env python3
"""Link Twilio phone number to ElevenLabs agent."""

import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.phone_numbers.types.phone_numbers_create_request_body import (
    PhoneNumbersCreateRequestBody_Twilio
)

load_dotenv()

def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    agent_id = os.environ.get("ELEVENLABS_AGENT_ID")
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

    print("=" * 60)
    print("  Linking Twilio Phone Number to ElevenLabs Agent")
    print("=" * 60)
    print()
    print(f"  Agent ID: {agent_id}")
    print(f"  Twilio Number: {twilio_number}")
    print()

    client = ElevenLabs(api_key=api_key)

    try:
        # Create the request body for Twilio phone number
        request_body = PhoneNumbersCreateRequestBody_Twilio(
            provider="twilio",
            phone_number=twilio_number,
            label="Debt Collection Line",
            sid=twilio_sid,
            token=twilio_token,
        )

        response = client.conversational_ai.phone_numbers.create(request=request_body)

        phone_id = response.phone_number_id if hasattr(response, 'phone_number_id') else response.get('phone_number_id')

        print("✅ Phone number linked successfully!")
        print()
        print(f"  Phone Number ID: {phone_id}")
        print()

        # Now assign the agent to this phone number
        print("  Assigning agent to this phone number...")
        client.conversational_ai.phone_numbers.update(
            phone_number_id=phone_id,
            agent_id=agent_id
        )
        print("  ✅ Agent assigned to phone number!")
        print()
        print("  Add this to your .env file:")
        print(f"  ELEVENLABS_PHONE_NUMBER_ID={phone_id}")
        print()

        return phone_id

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
