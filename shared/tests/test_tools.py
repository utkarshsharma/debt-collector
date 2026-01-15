"""Tests for ElevenLabs agent tools configuration."""

import os
from unittest.mock import patch

import pytest

from elevenlabs_integration.tools import create_sms_tool, get_sms_tool_prompt_instructions


class TestSMSTool:
    """Tests for SMS tool configuration."""

    def test_create_sms_tool_with_explicit_params(self):
        """Test creating SMS tool with explicit parameters."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        assert tool["type"] == "webhook"
        assert tool["name"] == "send_sms"
        assert "Send an SMS text message" in tool["description"]
        assert tool["response_timeout_secs"] == 10

    def test_create_sms_tool_url_contains_account_sid(self):
        """Test that the Twilio API URL contains the account SID."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        assert "AC1234567890" in tool["api_schema"]["url"]
        assert "api.twilio.com" in tool["api_schema"]["url"]
        assert "/Messages.json" in tool["api_schema"]["url"]

    def test_create_sms_tool_http_method(self):
        """Test that the tool uses POST method."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        assert tool["api_schema"]["method"] == "POST"

    def test_create_sms_tool_content_type(self):
        """Test that the tool uses form-urlencoded content type."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        assert tool["api_schema"]["content_type"] == "application/x-www-form-urlencoded"

    def test_create_sms_tool_auth_header(self):
        """Test that the tool references the TWILIO_AUTH secret."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        headers = tool["api_schema"]["request_headers"]
        assert "Authorization" in headers
        assert "{{secret:TWILIO_AUTH}}" in headers["Authorization"]
        assert "Basic" in headers["Authorization"]

    def test_create_sms_tool_request_body_schema(self):
        """Test the request body schema has required fields."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        schema = tool["api_schema"]["request_body_schema"]
        assert schema["type"] == "object"
        assert "To" in schema["properties"]
        assert "From" in schema["properties"]
        assert "Body" in schema["properties"]
        assert schema["required"] == ["To", "From", "Body"]

    def test_create_sms_tool_from_number_is_const(self):
        """Test that the From number is set as a constant."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15559876543",
        )

        from_prop = tool["api_schema"]["request_body_schema"]["properties"]["From"]
        assert from_prop["const"] == "+15559876543"

    def test_create_sms_tool_body_max_length(self):
        """Test that Body has max length constraint."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        body_prop = tool["api_schema"]["request_body_schema"]["properties"]["Body"]
        assert body_prop["maxLength"] == 1600

    def test_create_sms_tool_has_sound_config(self):
        """Test that the tool has sound configuration for feedback."""
        tool = create_sms_tool(
            twilio_account_sid="AC1234567890",
            twilio_phone_number="+15551234567",
        )

        assert tool["tool_call_sound"] == "typing"
        assert tool["tool_call_sound_behavior"] == "auto"

    @patch.dict(os.environ, {
        "TWILIO_ACCOUNT_SID": "ACenvtest123",
        "TWILIO_SMS_NUMBER": "+15550001111",
    })
    def test_create_sms_tool_from_env_vars(self):
        """Test creating SMS tool using environment variables."""
        tool = create_sms_tool()

        assert "ACenvtest123" in tool["api_schema"]["url"]
        from_prop = tool["api_schema"]["request_body_schema"]["properties"]["From"]
        assert from_prop["const"] == "+15550001111"

    @patch.dict(os.environ, {
        "TWILIO_ACCOUNT_SID": "ACenvtest123",
        "TWILIO_PHONE_NUMBER": "+15550002222",
    }, clear=True)
    def test_create_sms_tool_fallback_to_phone_number(self):
        """Test that TWILIO_PHONE_NUMBER is used if TWILIO_SMS_NUMBER not set."""
        tool = create_sms_tool()

        from_prop = tool["api_schema"]["request_body_schema"]["properties"]["From"]
        assert from_prop["const"] == "+15550002222"

    @patch.dict(os.environ, {}, clear=True)
    def test_create_sms_tool_missing_account_sid_raises(self):
        """Test that missing TWILIO_ACCOUNT_SID raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_sms_tool()
        assert "TWILIO_ACCOUNT_SID" in str(exc_info.value)

    @patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "AC123"}, clear=True)
    def test_create_sms_tool_missing_phone_number_raises(self):
        """Test that missing phone number raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_sms_tool()
        assert "TWILIO_SMS_NUMBER" in str(exc_info.value) or "TWILIO_PHONE_NUMBER" in str(exc_info.value)


class TestSMSToolPromptInstructions:
    """Tests for SMS tool prompt instructions."""

    def test_prompt_instructions_not_empty(self):
        """Test that prompt instructions are provided."""
        instructions = get_sms_tool_prompt_instructions()
        assert len(instructions) > 100

    def test_prompt_instructions_contains_scenarios(self):
        """Test that instructions cover all SMS scenarios."""
        instructions = get_sms_tool_prompt_instructions()

        # All scenarios should be mentioned
        assert "PAYMENT COMMITMENT" in instructions
        assert "CALLBACK REQUESTED" in instructions
        assert "DISPUTE RAISED" in instructions
        assert "HARDSHIP CLAIMED" in instructions
        assert "NO COMMITMENT" in instructions

    def test_prompt_instructions_contains_exclusions(self):
        """Test that instructions list when NOT to send SMS."""
        instructions = get_sms_tool_prompt_instructions()

        assert "DO NOT SEND SMS IF" in instructions
        assert "Wrong number" in instructions
        assert "third party" in instructions.lower()
        assert "opted out" in instructions.lower()

    def test_prompt_instructions_mentions_tool_name(self):
        """Test that instructions reference the send_sms tool."""
        instructions = get_sms_tool_prompt_instructions()
        assert "send_sms" in instructions

    def test_prompt_instructions_uses_template_variables(self):
        """Test that instructions use the dynamic variable syntax."""
        instructions = get_sms_tool_prompt_instructions()

        # Should reference template variables
        assert "{{debtor_name}}" in instructions
        assert "{{company_name}}" in instructions
