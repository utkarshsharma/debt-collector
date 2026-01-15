"""
ElevenLabs Agent Tools configuration.

This module defines server tools (webhooks) that allow the voice agent
to interact with external APIs during conversations.
"""

import os
from typing import Any


def create_sms_tool(
    twilio_account_sid: str | None = None,
    twilio_phone_number: str | None = None,
) -> dict[str, Any]:
    """
    Create a Twilio SMS webhook tool for the ElevenLabs agent.

    This tool allows the agent to send SMS messages directly via Twilio's API
    during or at the end of a conversation.

    Args:
        twilio_account_sid: Twilio Account SID (uses env var if not provided)
        twilio_phone_number: Twilio phone number to send from (uses env var if not provided)

    Returns:
        Tool configuration dictionary for ElevenLabs agent

    Raises:
        ValueError: If required credentials are not provided or set in environment
    """
    # Get credentials from env if not provided
    if twilio_account_sid is None:
        twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        if not twilio_account_sid:
            raise ValueError(
                "twilio_account_sid must be provided or TWILIO_ACCOUNT_SID env var must be set"
            )

    if twilio_phone_number is None:
        twilio_phone_number = os.environ.get("TWILIO_SMS_NUMBER") or os.environ.get(
            "TWILIO_PHONE_NUMBER"
        )
        if not twilio_phone_number:
            raise ValueError(
                "twilio_phone_number must be provided or TWILIO_SMS_NUMBER/TWILIO_PHONE_NUMBER env var must be set"
            )

    return {
        "type": "webhook",
        "name": "send_sms",
        "description": (
            "Send an SMS text message to the debtor. Use this tool before ending the call "
            "to send a confirmation, follow-up, or contact information message based on the "
            "conversation outcome. The message should be appropriate for the situation: "
            "payment confirmation, callback acknowledgment, dispute logged, hardship support, "
            "or general follow-up."
        ),
        "api_schema": {
            "url": f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json",
            "method": "POST",
            "content_type": "application/x-www-form-urlencoded",
            "request_headers": {
                # References secret stored in ElevenLabs dashboard
                # Format: Base64(AccountSID:AuthToken)
                "Authorization": "Basic {{secret:TWILIO_AUTH}}"
            },
            "request_body_schema": {
                "type": "object",
                "description": "SMS message parameters",
                "properties": {
                    "To": {
                        "type": "string",
                        "description": (
                            "The destination phone number in E.164 format (e.g., +15551234567). "
                            "This should be the debtor's phone number from the call."
                        ),
                    },
                    "From": {
                        "type": "string",
                        "description": f"The Twilio phone number to send from. Always use: {twilio_phone_number}",
                        "const": twilio_phone_number,
                    },
                    "Body": {
                        "type": "string",
                        "description": (
                            "The SMS message content. Keep it concise (under 160 chars preferred). "
                            "Include the debtor's name, company name, and relevant details based on "
                            "the conversation outcome (payment amount/date, callback info, dispute ack, etc.)."
                        ),
                        "maxLength": 1600,
                    },
                },
                "required": ["To", "From", "Body"],
            },
        },
        "response_timeout_secs": 10,
        # Play a subtle sound while SMS is being sent
        "tool_call_sound": "typing",
        "tool_call_sound_behavior": "auto",
    }


def get_sms_tool_prompt_instructions() -> str:
    """
    Get the prompt instructions for the SMS tool.

    Returns:
        String containing instructions to add to the agent's system prompt
    """
    return '''
## SMS Tool - REQUIRED Before Ending Call

You MUST use the send_sms tool before ending every call to send an appropriate text message.
Choose the message type based on the conversation outcome:

### 1. PAYMENT COMMITMENT
When debtor commits to a specific payment amount AND date:
- Send: "Hi {{debtor_name}}, this confirms your commitment to pay $[AMOUNT] to {{company_name}} by [DATE]. Thank you!"
- Say: "I'm sending you a confirmation text now."

### 2. CALLBACK REQUESTED
When debtor asks you to call back later:
- Send: "Hi {{debtor_name}}, we'll call you back as discussed. Please contact {{company_name}} if you'd like to reach us sooner."
- Say: "I'll send you a text with our contact info."

### 3. DISPUTE RAISED
When debtor disputes the debt:
- Send: "Hi {{debtor_name}}, we've noted your dispute regarding your {{company_name}} account. Someone will follow up within 5 business days."
- Say: "I'm sending you confirmation that we've logged your dispute."

### 4. HARDSHIP CLAIMED
When debtor claims financial hardship:
- Send: "Hi {{debtor_name}}, we understand you're experiencing difficulties. Please call {{company_name}} to discuss payment options when you're ready."
- Say: "I'll text you our contact info for when you're ready to discuss options."

### 5. NO COMMITMENT / HUNG UP / VOICEMAIL
When call ends without a specific resolution:
- Send: "Hi {{debtor_name}}, we tried to reach you about your {{company_name}} account. Please call us back at your earliest convenience."

### DO NOT SEND SMS IF:
- Wrong number was confirmed
- A third party answered (not the debtor)
- Debtor explicitly opted out (said "stop calling" or similar)

IMPORTANT: Always include the debtor's name and company name in the message.
The "From" number is always: {{twilio_from_number}} - do not change it.
'''
