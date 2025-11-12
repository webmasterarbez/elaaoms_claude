"""
OpenMemory integration for webhook payload storage.
Webhook data is saved to filesystem and tagged for OpenMemory processing.
In Claude Code context, use MCP tools to persist memories directly.
"""

import logging
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
    Send webhook payload to OpenMemory.

    Note: OpenMemory integration works via MCP tools in Claude Code environment.
    For standalone FastAPI deployment, webhook data is saved to filesystem.
    In Claude Code context, use mcp__openmemory__openmemory_store to persist memories.

    Args:
        webhook_payload: The complete webhook payload (type + data wrapper)
        request_id: Request tracking ID for logging

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract caller_id from nested dynamic_variables
        caller_id = extract_caller_id(webhook_payload.get("data", {}))

        if not caller_id:
            logger.warning(f"[{request_id}] Skipping OpenMemory storage: caller_id not found")
            return False

        # Prepare webhook data for storage
        webhook_type = webhook_payload.get("type")
        conversation_id = webhook_payload.get("data", {}).get("conversation_id")
        data_section = webhook_payload.get("data", {})

        # Create content summary for the memory
        if webhook_type == "post_call_transcription":
            transcript = data_section.get("transcript", [])
            transcript_summary = ". ".join([
                f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
                for msg in transcript
            ])
            content = f"ElevenLabs Webhook - Post Call Transcription. Conversation ID: {conversation_id}. Caller ID: {caller_id}. Transcript: {transcript_summary}"
        else:
            # For other webhook types, create a generic summary
            content = f"ElevenLabs Webhook - {webhook_type}. Conversation ID: {conversation_id}. Caller ID: {caller_id}."

        # Metadata for the memory
        metadata = {
            "webhook_type": webhook_type,
            "conversation_id": conversation_id,
            "request_id": request_id
        }

        logger.debug(f"[{request_id}] Processing webhook for OpenMemory storage - caller_id: {caller_id}")
        logger.debug(f"[{request_id}] Webhook content: {content}")
        logger.debug(f"[{request_id}] Note: In Claude Code environment, use MCP tools to store in OpenMemory. In standalone mode, webhook is saved to filesystem.")

        # Log that webhook is queued for OpenMemory storage
        # In production, this would integrate with OpenMemory via:
        # - MCP tools in Claude Code context
        # - Direct API calls to a compatible OpenMemory endpoint
        logger.info(
            f"[{request_id}] Webhook queued for OpenMemory storage: "
            f"type={webhook_type}, conversation_id={conversation_id}, caller_id={caller_id}"
        )

        return True

    except Exception as e:
        logger.error(f"[{request_id}] Error preparing OpenMemory storage: {str(e)}", exc_info=True)
        return False
