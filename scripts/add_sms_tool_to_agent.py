#!/usr/bin/env python3
"""
Add the SMS tool and end_call system tool to an existing ElevenLabs agent.

This script:
1. Creates a Basic Auth connection for Twilio (workspace level)
2. Creates the SMS webhook tool using that auth connection
3. Links it to your existing agent using tool_ids
4. Adds the end_call system tool so the agent can terminate calls

Usage:
    python scripts/add_sms_tool_to_agent.py
"""

import os
import sys
from pathlib import Path

import requests

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared"))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv(project_root / ".env")

console = Console()

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"


def get_or_create_twilio_auth_connection(api_key: str) -> str:
    """
    Get existing or create new Twilio Basic Auth connection.

    Returns the auth_connection_id.
    """
    twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

    if not twilio_account_sid:
        raise ValueError("TWILIO_ACCOUNT_SID not set in environment")
    if not twilio_auth_token:
        raise ValueError("TWILIO_AUTH_TOKEN not set in environment")

    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

    # Check for existing Twilio auth connection
    response = requests.get(
        f"{ELEVENLABS_API_BASE}/workspace/auth-connections",
        headers=headers
    )
    response.raise_for_status()

    for conn in response.json().get("auth_connections", []):
        if conn.get("provider") == "twilio" and conn.get("auth_type") == "basic_auth":
            return conn.get("id")

    # Create new auth connection
    response = requests.post(
        f"{ELEVENLABS_API_BASE}/workspace/auth-connections",
        headers=headers,
        json={
            "name": "twilio_sms_auth",
            "provider": "twilio",
            "username": twilio_account_sid,
            "password": twilio_auth_token
        }
    )
    response.raise_for_status()
    return response.json().get("id")


def get_sms_tool_config(auth_connection_id: str) -> dict:
    """Get the SMS tool configuration using auth connection."""
    twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_phone_number = os.environ.get("TWILIO_SMS_NUMBER") or os.environ.get("TWILIO_PHONE_NUMBER")

    if not twilio_account_sid:
        raise ValueError("TWILIO_ACCOUNT_SID not set in environment")
    if not twilio_phone_number:
        raise ValueError("TWILIO_PHONE_NUMBER not set in environment")

    return {
        "type": "webhook",
        "name": "send_sms",
        "description": (
            "Send SMS to debtor before ending call. Use for: payment confirmation, "
            "callback acknowledgment, dispute logged, hardship support, or follow-up message. "
            "Always send an appropriate SMS based on the conversation outcome."
        ),
        "api_schema": {
            "url": f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json",
            "method": "POST",
            "content_type": "application/x-www-form-urlencoded",
            "auth_connection": {
                "auth_connection_id": auth_connection_id
            },
            "request_body_schema": {
                "type": "object",
                "properties": {
                    "To": {
                        "type": "string",
                        "description": "Debtor's phone number in E.164 format (e.g., +15551234567)"
                    },
                    "From": {
                        "type": "string",
                        "description": f"Twilio phone number to send from. Always use: {twilio_phone_number}",
                    },
                    "Body": {
                        "type": "string",
                        "description": "SMS message content. Keep concise (under 160 chars preferred).",
                        "maxLength": 1600
                    }
                },
                "required": ["To", "From", "Body"]
            }
        },
        "response_timeout_secs": 10
    }


def list_workspace_tools(api_key: str) -> list:
    """List all tools in the workspace."""
    response = requests.get(
        f"{ELEVENLABS_API_BASE}/convai/tools",
        headers={"xi-api-key": api_key}
    )
    response.raise_for_status()
    return response.json().get("tools", [])


def create_workspace_tool(api_key: str, tool_config: dict) -> dict:
    """Create a tool at the workspace level."""
    response = requests.post(
        f"{ELEVENLABS_API_BASE}/convai/tools",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        },
        json={"tool_config": tool_config}
    )
    response.raise_for_status()
    return response.json()


def delete_workspace_tool(api_key: str, tool_id: str) -> None:
    """Delete a tool from the workspace."""
    response = requests.delete(
        f"{ELEVENLABS_API_BASE}/convai/tools/{tool_id}",
        headers={"xi-api-key": api_key}
    )
    response.raise_for_status()


def update_agent_tools(
    api_key: str,
    agent_id: str,
    tool_ids: list,
    built_in_tools: dict | None = None
) -> dict:
    """
    Update an agent to use specific tools.

    Args:
        api_key: ElevenLabs API key
        agent_id: Agent ID to update
        tool_ids: List of workspace tool IDs (for webhook tools)
        built_in_tools: Dict of built-in system tools to enable
    """
    prompt_config = {"tool_ids": tool_ids}

    if built_in_tools:
        prompt_config["built_in_tools"] = built_in_tools

    response = requests.patch(
        f"{ELEVENLABS_API_BASE}/convai/agents/{agent_id}",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "conversation_config": {
                "agent": {
                    "prompt": prompt_config
                }
            }
        }
    )
    response.raise_for_status()
    return response.json()


def get_built_in_tools_config() -> dict:
    """
    Get the built_in_tools configuration object.

    The built_in_tools field is a dictionary where each key is a tool name
    and the value is the tool configuration (SystemToolConfig-Input).
    """
    return {
        "end_call": {
            "type": "system",
            "name": "end_call",
            "description": (
                "End the call when the conversation is complete. Use this after: "
                "1) Getting a payment commitment and sending confirmation SMS, "
                "2) Scheduling a callback and sending contact info SMS, "
                "3) Logging a dispute and sending acknowledgment SMS, "
                "4) The debtor asks to end the call or says goodbye, "
                "5) The debtor confirms wrong number (no SMS needed). "
                "Always provide a polite farewell message before ending."
            ),
            "params": {
                "system_tool_type": "end_call"
            }
        }
    }


def main():
    console.print(Panel.fit(
        "[bold blue]Add SMS Tool + End Call to Agent[/bold blue]\n\n"
        "This script:\n"
        "1. Creates Twilio Basic Auth connection (workspace level)\n"
        "2. Creates SMS webhook tool using auth connection\n"
        "3. Links tool to agent\n"
        "4. Enables end_call built-in system tool",
        border_style="blue"
    ))

    # Get credentials
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    agent_id = os.environ.get("ELEVENLABS_AGENT_ID")

    if not api_key:
        console.print("[red]Error:[/red] ELEVENLABS_API_KEY not set")
        sys.exit(1)
    if not agent_id:
        console.print("[red]Error:[/red] ELEVENLABS_AGENT_ID not set")
        sys.exit(1)

    console.print(f"Agent ID: [cyan]{agent_id}[/cyan]\n")

    # Step 1: Create or get auth connection
    console.print("[bold]Step 1: Setting up Twilio Auth Connection...[/bold]")
    try:
        auth_connection_id = get_or_create_twilio_auth_connection(api_key)
        console.print(f"  [green]✓[/green] Auth connection: {auth_connection_id}")
    except ValueError as e:
        console.print(f"  [red]Error:[/red] {e}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]Error:[/red] {e.response.text}")
        sys.exit(1)

    console.print()

    # Step 2: Check/create SMS tool
    console.print("[bold]Step 2: Setting up SMS webhook tool...[/bold]")
    tool_ids_to_link = []
    existing_sms_tool_id = None

    try:
        existing_tools = list_workspace_tools(api_key)
        for tool in existing_tools:
            tool_name = tool.get("name") or tool.get("tool_config", {}).get("name")
            tool_id = tool.get("id") or tool.get("tool_id")
            api_schema = tool.get("tool_config", {}).get("api_schema", {})

            if tool_name == "send_sms":
                # Check if it's using auth_connection
                if api_schema.get("auth_connection"):
                    existing_sms_tool_id = tool_id
                    console.print(f"  [green]✓[/green] SMS tool exists with auth connection: {tool_id}")
                else:
                    # Old tool without auth_connection - need to recreate
                    console.print(f"  [yellow]![/yellow] Found old SMS tool without auth connection: {tool_id}")
                    console.print("  [dim]Will unlink and delete old tool...[/dim]")

                    # Unlink from agent first
                    update_agent_tools(api_key, agent_id, [], None)
                    delete_workspace_tool(api_key, tool_id)
                    console.print(f"  [green]✓[/green] Deleted old tool")

    except Exception as e:
        console.print(f"  [yellow]Warning:[/yellow] Could not list tools: {e}")

    if existing_sms_tool_id:
        tool_ids_to_link.append(existing_sms_tool_id)
    else:
        try:
            sms_tool_config = get_sms_tool_config(auth_connection_id)
            created_sms = create_workspace_tool(api_key, sms_tool_config)
            sms_tool_id = created_sms.get("id") or created_sms.get("tool_id")
            console.print(f"  [green]✓[/green] Created SMS tool: {sms_tool_id}")
            tool_ids_to_link.append(sms_tool_id)
        except ValueError as e:
            console.print(f"  [red]Error:[/red] {e}")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            console.print(f"  [red]Error creating SMS tool:[/red] {e.response.text}")
            sys.exit(1)

    console.print()

    # Step 3: Configure end_call as built-in tool
    console.print("[bold]Step 3: Configuring end_call built-in tool...[/bold]")
    built_in_tools = get_built_in_tools_config()
    console.print(f"  [green]✓[/green] end_call tool config ready")

    console.print()

    # Step 4: Update agent with both tools
    console.print("[bold]Step 4: Updating agent configuration...[/bold]")
    try:
        update_agent_tools(
            api_key,
            agent_id,
            tool_ids_to_link,
            built_in_tools=built_in_tools
        )
        console.print(f"  [green]✓[/green] Agent updated with:")
        console.print(f"      - {len(tool_ids_to_link)} webhook tool(s): {tool_ids_to_link}")
        console.print(f"      - 1 built-in tool: end_call")
    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]Error updating agent:[/red] {e}")
        console.print(f"  Response: {e.response.text}")
        sys.exit(1)

    console.print()

    console.print(Panel(
        f"[bold green]Tools Configured Successfully![/bold green]\n\n"
        f"Agent ID: {agent_id}\n\n"
        f"Auth Connection:\n"
        f"  • {auth_connection_id} (Twilio Basic Auth)\n\n"
        f"Webhook tools:\n"
        f"  • send_sms - Send SMS via Twilio\n\n"
        f"Built-in tools:\n"
        f"  • end_call - Terminate calls automatically\n\n"
        f"Test by making a call. The agent should now:\n"
        f"  1. Send SMS before ending\n"
        f"  2. Disconnect automatically when done",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
