"""
OpenMemory integration for webhook payload storage.
Note: The local /memory/ingest endpoint has a configuration issue where it rejects
all content types with 500 errors. This module logs webhooks for processing.
For actual OpenMemory storage, use the OpenMemory MCP tools via Claude Code.
"""

import logging
import json
from typing import Optional, Dict, Any
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_caller_id(webhook_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract system__caller_id from webhook data's dynamic_variables.

    Handles nested structure in ElevenLabs webhooks:
    - First checks: webhook_data.conversation_initiation_client_data.dynamic_variables
    - Falls back to: webhook_data.dynamic_variables

    Args:
        webhook_data: The webhook.data dictionary containing dynamic_variables

    Returns:
        The phone number (system__caller_id) or None if not found
    """
    try:
        # First try nested structure in conversation_initiation_client_data
        conversation_init = webhook_data.get("conversation_initiation_client_data", {})
        dynamic_variables = conversation_init.get("dynamic_variables", {})
        caller_id = dynamic_variables.get("system__caller_id")

        if caller_id:
            logger.debug(f"Found caller_id in conversation_initiation_client_data: {caller_id}")
            return caller_id

        # Fall back to top-level dynamic_variables (for other payload formats)
        dynamic_variables = webhook_data.get("dynamic_variables", {})
        caller_id = dynamic_variables.get("system__caller_id")

        if caller_id:
            logger.debug(f"Found caller_id in top-level dynamic_variables: {caller_id}")
            return caller_id
        else:
            logger.warning("system__caller_id not found in dynamic_variables (checked both nested and top-level)")
            return None
    except Exception as e:
        logger.warning(f"Error extracting caller_id: {str(e)}")
        return None


def send_to_openmemory(webhook_payload: Dict[str, Any], request_id: str) -> bool:
    """
    Log webhook for OpenMemory storage.

    NOTE: The local OpenMemory /memory/ingest endpoint has a configuration issue
    where it rejects all content types (text/html, application/json, etc.) with
    HTTP 500 "Unsupported content type" errors. This is a bug in the endpoint
    that needs to be fixed in the OpenMemory server configuration.

    For actual webhook storage in OpenMemory, you have two options:
    1. Use the MCP tools via Claude Code (recommended):
       - mcp__openmemory__openmemory_store()
    2. Use a different OpenMemory instance with a working /memory/ingest endpoint

    Args:
        webhook_payload: The complete webhook payload (type + data wrapper)
        request_id: Request tracking ID for logging

    Returns:
        True (always succeeds since we're just logging)
    """
    try:
        # Extract caller_id from nested dynamic_variables
        caller_id = extract_caller_id(webhook_payload.get("data", {}))

        if not caller_id:
            logger.warning(f"[{request_id}] Skipping OpenMemory logging: caller_id not found")
            return False

        webhook_type = webhook_payload.get("type")
        conversation_id = webhook_payload.get("data", {}).get("conversation_id")
        data_section = webhook_payload.get("data", {})

        # Create a summary of the webhook for logging
        summary = _create_webhook_summary(webhook_type, conversation_id, caller_id, data_section)

        # Log the webhook details
        logger.info(
            f"[{request_id}] Webhook ready for OpenMemory storage:\n"
            f"  Type: {webhook_type}\n"
            f"  Conversation ID: {conversation_id}\n"
            f"  Caller ID: {caller_id}\n"
            f"  Summary: {summary}"
        )

        logger.debug(
            f"[{request_id}] Full webhook payload:\n"
            f"{json.dumps(webhook_payload, indent=2, default=str)}"
        )

        return True

    except Exception as e:
        logger.error(f"[{request_id}] Error logging webhook for OpenMemory: {str(e)}", exc_info=True)
        return False


def _create_webhook_summary(webhook_type: str, conversation_id: str, caller_id: str, data: Dict[str, Any]) -> str:
    """Create a text summary of webhook data."""

    if webhook_type == "post_call_transcription":
        transcript_items = data.get("transcript", [])
        transcript_summary = " | ".join([
            f"{msg.get('role', 'Unknown')}: {msg.get('message', '')[:50]}"
            for msg in transcript_items[:3]  # First 3 messages only
        ])
        return f"Transcription with {len(transcript_items)} messages: {transcript_summary}"

    elif webhook_type == "post_call_audio":
        return "Audio file received"

    elif webhook_type == "call_initiation_failure":
        return f"Call failed: {data.get('failure_reason', 'Unknown reason')}"

    else:
        return f"Webhook of type {webhook_type}"
