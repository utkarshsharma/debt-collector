#!/usr/bin/env python3
"""Make a test outbound call to verify the ElevenLabs agent works."""

import argparse
import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Make a test outbound call")
    parser.add_argument(
        "--to",
        type=str,
        required=True,
        help="Phone number to call in E.164 format (e.g., +15551234567)",
    )
    parser.add_argument(
        "--debtor-name",
        type=str,
        default="John Smith",
        help="Name of the test debtor",
    )
    parser.add_argument(
        "--company-name",
        type=str,
        default="ABC Financial Services",
        help="Name of the company",
    )
    parser.add_argument(
        "--amount",
        type=str,
        default="150.00",
        help="Amount owed",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip identity verification (for testing)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    agent_id = os.environ.get("ELEVENLABS_AGENT_ID")
    phone_id = os.environ.get("ELEVENLABS_PHONE_NUMBER_ID")

    print("=" * 60)
    print("  Making Test Outbound Call")
    print("=" * 60)
    print()
    print(f"  To: {args.to}")
    print(f"  Debtor Name: {args.debtor_name}")
    print(f"  Company: {args.company_name}")
    print(f"  Amount: ${args.amount}")
    print()
    print(f"  Agent ID: {agent_id}")
    print(f"  Phone ID: {phone_id}")
    print(f"  Skip Verification: {args.skip_verification}")
    print()

    client = ElevenLabs(api_key=api_key)

    try:
        print("📞 Initiating call...")
        print()

        response = client.conversational_ai.twilio.outbound_call(
            agent_id=agent_id,
            agent_phone_number_id=phone_id,
            to_number=args.to,
            conversation_initiation_client_data={
                "dynamic_variables": {
                    "debtor_name": args.debtor_name,
                    "company_name": args.company_name,
                    "amount_owed": args.amount,
                    "due_date": "January 7, 2026",
                    "account_number": "5678",
                    "skip_verification": "true" if args.skip_verification else "false",
                }
            },
        )

        # Check if call was successful
        if hasattr(response, 'success') and not response.success:
            print(f"❌ Call failed: {response.message}")
            print()
            if "geo-permissions" in response.message:
                print("  💡 Tip: Enable international calling in Twilio:")
                print("     https://www.twilio.com/console/voice/calls/geo-permissions/low-risk")
            return

        conversation_id = response.conversation_id if hasattr(response, 'conversation_id') else response.get('conversation_id')
        call_sid = response.call_sid if hasattr(response, 'call_sid') else response.get('call_sid', response.get('callSid'))

        print("✅ Call initiated successfully!")
        print()
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Call SID: {call_sid}")
        print()
        print(f"  📱 Your phone ({args.to}) should be ringing now!")
        print()
        print("  The AI will say:")
        print(f'  "Hello, this is Eric calling from {args.company_name}.')
        print(f'   May I speak with {args.debtor_name}?"')
        print()
        print("  Answer the call and have a conversation with the AI!")
        print()

    except Exception as e:
        print(f"❌ Error making call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
