"""
OpenMemory integration for webhook payload storage.
Sends post-call webhook payloads to OpenMemory using multimodal ingestion.
"""

import requests
import logging
import json
import base64
from typing import Optional, Dict, Any
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_caller_id(webhook_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract system__caller_id from webhook data's dynamic_variables.

    Args:
        webhook_data: The webhook.data dictionary containing dynamic_variables

    Returns:
        The phone number (system__caller_id) or None if not found
    """
    try:
        dynamic_variables = webhook_data.get("dynamic_variables", {})
        caller_id = dynamic_variables.get("system__caller_id")
        if caller_id:
            return caller_id
        else:
            logger.warning("system__caller_id not found in dynamic_variables")
            return None
    except Exception as e:
        logger.warning(f"Error extracting caller_id: {str(e)}")
        return None


def send_to_openmemory(webhook_payload: Dict[str, Any], request_id: str) -> bool:
    """
    Send webhook payload to OpenMemory using multimodal ingestion.

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

        # Prepare OpenMemory API request
        api_url = f"{settings.openmemory_api_url}/memory/ingest"
        headers = {
            "Authorization": f"Bearer {settings.openmemory_api_key}",
            "Content-Type": "application/json"
        }

        # Base64 encode the webhook JSON payload
        json_str = json.dumps(webhook_payload, indent=2, default=str)
        base64_encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

        # Prepare payload for memory ingestion
        payload = {
            "content_type": "application/json",
            "data": base64_encoded,
            "metadata": {
                "user": caller_id,
                "webhook_type": webhook_payload.get("type"),
                "conversation_id": webhook_payload.get("data", {}).get("conversation_id"),
                "request_id": request_id
            }
        }

        logger.debug(f"[{request_id}] Sending to OpenMemory - caller_id: {caller_id}")

        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code in [200, 201]:
            logger.info(
                f"[{request_id}] Successfully stored webhook in OpenMemory "
                f"for caller_id: {caller_id}"
            )
            return True
        else:
            logger.error(
                f"[{request_id}] OpenMemory ingestion failed with status {response.status_code}: "
                f"{response.text}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.error(f"[{request_id}] OpenMemory request timed out")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[{request_id}] OpenMemory request failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"[{request_id}] Error sending to OpenMemory: {str(e)}", exc_info=True)
        return False
