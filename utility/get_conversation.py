#!/usr/bin/env python3
"""
Utility to fetch conversation details from ElevenLabs API and send to OpenMemory via webhook.

Usage:
    python utility/get_conversation.py <conversation_id_1> [conversation_id_2] ...

Example:
    python utility/get_conversation.py conv_123abc
    python utility/get_conversation.py conv_123abc conv_456def conv_789ghi

Environment Variables:
    ELEVENLABS_API_KEY: Your ElevenLabs API key (required)
    ELEVENLABS_POST_CALL_HMAC_KEY: HMAC key for signing webhook requests (required)
    WEBHOOK_URL: Webhook endpoint URL (default: http://localhost:8000/webhook/post-call)
"""

import os
import sys
import json
import logging
import argparse
import requests
import hmac
import time
from hashlib import sha256
from typing import Dict, Any, List, Optional
from pathlib import Path


def load_env_file():
    """
    Load environment variables from .env file in project root.
    
    Only sets variables that are not already in the environment,
    allowing command-line flags to override .env values.
    """
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Only set if not already in environment
                    if key and key not in os.environ:
                        os.environ[key] = value


# Load .env file before anything else
load_env_file()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConversationGetter:
    """Fetches conversation details from ElevenLabs and sends to webhook."""

    ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
    DEFAULT_WEBHOOK_URL = "http://localhost:8000/webhook/post-call"

    def __init__(self, api_key: str, hmac_key: str, webhook_url: Optional[str] = None):
        """
        Initialize the conversation getter.

        Args:
            api_key: ElevenLabs API key
            hmac_key: HMAC key for signing webhook requests
            webhook_url: Optional webhook URL (defaults to localhost)
        """
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required")
        if not hmac_key:
            raise ValueError("ELEVENLABS_POST_CALL_HMAC_KEY is required for signing requests")

        self.api_key = api_key
        self.hmac_key = hmac_key
        self.webhook_url = webhook_url or self.DEFAULT_WEBHOOK_URL
        self.session = requests.Session()
        self.session.headers.update({
            "xi-api-key": self.api_key
        })

    def get_conversation_details(self, conversation_id: str) -> Dict[str, Any]:
        """
        Fetch conversation details from ElevenLabs API.

        Args:
            conversation_id: The conversation ID to fetch

        Returns:
            Dictionary containing conversation details

        Raises:
            requests.HTTPError: If the API request fails
        """
        url = f"{self.ELEVENLABS_API_BASE}/convai/conversations/{conversation_id}"

        logger.info(f"Fetching conversation details for: {conversation_id}")
        logger.debug(f"API URL: {url}")
        logger.debug(f"API key header present: {'xi-api-key' in self.session.headers}")
        logger.debug(f"API key length: {len(self.api_key) if self.api_key else 0}")

        try:
            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched conversation {conversation_id}")
            logger.debug(f"Response data: {json.dumps(data, indent=2)}")

            return data

        except requests.HTTPError as e:
            logger.error(f"HTTP error fetching conversation {conversation_id}: {e}")
            if e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response headers: {dict(e.response.headers)}")
                try:
                    error_body = e.response.text
                    logger.error(f"Response body: {error_body[:500]}")  # First 500 chars
                except Exception:
                    logger.error("Response: Could not read response body")
            else:
                logger.error("Response: No response object")
            raise
        except Exception as e:
            logger.error(f"Error fetching conversation {conversation_id}: {e}")
            raise

    def format_as_webhook(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format conversation data to match ElevenLabs webhook structure.

        The webhook expects a specific format with type and data fields.
        This converts the API response to match that structure.

        Note: The backend will apply the new filtering strategy:
        - Transcript pre-filtering removes system prompts/config before LLM extraction
        - LLM extraction focuses on conversation content only
        - Post-extraction validation rejects bad content before storage
        - Memories are isolated by phone number (caller_id) and filtered by type

        Args:
            conversation_data: Raw conversation data from API

        Returns:
            Formatted webhook payload
        """
        # Extract key fields from conversation data
        conversation_id = conversation_data.get("conversation_id")
        agent_id = conversation_data.get("agent_id")

        # Build transcript array from transcript field if it exists
        # The backend's _filter_transcript() will clean this before LLM processing
        transcript = []
        if "transcript" in conversation_data:
            transcript = conversation_data["transcript"]

        # Calculate duration from start/end times if not provided
        duration = conversation_data.get("duration")
        if duration is None:
            start_time = conversation_data.get("start_time_unix_secs")
            end_time = conversation_data.get("end_time_unix_secs")
            if start_time and end_time:
                duration = int(end_time - start_time)

        # Format as post_call_transcription webhook
        # All fields are passed through - backend handles filtering and validation
        webhook_payload = {
            "type": "post_call_transcription",
            "data": {
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "transcript": transcript,
                "duration": duration,  # Include duration for backend processing
                "conversation_initiation_client_data": conversation_data.get(
                    "conversation_initiation_client_data", {}
                ),
                "dynamic_variables": conversation_data.get("dynamic_variables", {}),
                "metadata": conversation_data.get("metadata", {}),
                "analysis": conversation_data.get("analysis", {}),
                "status": conversation_data.get("status", "completed"),
                "start_time_unix_secs": conversation_data.get("start_time_unix_secs"),
                "end_time_unix_secs": conversation_data.get("end_time_unix_secs"),
            }
        }

        return webhook_payload

    def _sign_webhook_request(self, payload_json: str) -> str:
        """
        Create HMAC signature for webhook request.

        Uses the same signature format as ElevenLabs:
        - Payload to sign: {timestamp}.{json_payload}
        - Header format: t={timestamp},v0={hash}

        Args:
            payload_json: JSON string of the payload

        Returns:
            Signature header value (t={timestamp},v0={hash})
        """
        timestamp = int(time.time())
        full_payload_to_sign = f"{timestamp}.{payload_json}"

        mac = hmac.new(
            key=self.hmac_key.encode("utf-8"),
            msg=full_payload_to_sign.encode("utf-8"),
            digestmod=sha256,
        )
        calculated_hash = mac.hexdigest()

        signature_header = f"t={timestamp},v0={calculated_hash}"
        return signature_header

    def send_to_webhook(self, webhook_payload: Dict[str, Any]) -> bool:
        """
        Send formatted conversation data to webhook endpoint with HMAC signature.

        Args:
            webhook_payload: Formatted webhook payload

        Returns:
            True if successful, False otherwise
        """
        conversation_id = webhook_payload.get("data", {}).get("conversation_id")

        logger.info(f"Sending conversation {conversation_id} to webhook: {self.webhook_url}")

        try:
            # Serialize payload
            payload_json = json.dumps(webhook_payload)

            # Create HMAC signature
            signature_header = self._sign_webhook_request(payload_json)

            # Send request with signature
            response = requests.post(
                self.webhook_url,
                data=payload_json,  # Use data instead of json to send pre-serialized JSON
                headers={
                    "Content-Type": "application/json",
                    "elevenlabs-signature": signature_header
                },
                timeout=30
            )

            response.raise_for_status()

            result = response.json()
            logger.info(f"Successfully sent conversation {conversation_id} to webhook")
            logger.debug(f"Webhook response: {json.dumps(result, indent=2)}")

            return True

        except requests.HTTPError as e:
            logger.error(f"HTTP error sending to webhook: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            return False
        except Exception as e:
            logger.error(f"Error sending to webhook: {e}")
            return False

    def process_conversation(self, conversation_id: str) -> bool:
        """
        Fetch conversation details and send to webhook.

        Args:
            conversation_id: The conversation ID to process

        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch conversation details from ElevenLabs API
            conversation_data = self.get_conversation_details(conversation_id)

            # Format as webhook payload
            webhook_payload = self.format_as_webhook(conversation_data)

            # Send to webhook endpoint
            success = self.send_to_webhook(webhook_payload)

            return success

        except Exception as e:
            logger.error(f"Failed to process conversation {conversation_id}: {e}")
            return False

    def process_multiple_conversations(self, conversation_ids: List[str]) -> Dict[str, bool]:
        """
        Process multiple conversations.

        Args:
            conversation_ids: List of conversation IDs to process

        Returns:
            Dictionary mapping conversation_id to success status
        """
        results = {}

        logger.info(f"Processing {len(conversation_ids)} conversation(s)")

        for conversation_id in conversation_ids:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing conversation: {conversation_id}")
            logger.info(f"{'='*60}")

            success = self.process_conversation(conversation_id)
            results[conversation_id] = success

            if success:
                logger.info(f"✓ Successfully processed {conversation_id}")
            else:
                logger.error(f"✗ Failed to process {conversation_id}")

        return results


def main():
    """Main entry point for the utility."""
    parser = argparse.ArgumentParser(
        description="Fetch ElevenLabs conversation details and send to OpenMemory webhook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single conversation
  python utility/get_conversation.py conv_123abc

  # Process multiple conversations
  python utility/get_conversation.py conv_123abc conv_456def conv_789ghi

  # Use custom webhook URL
  WEBHOOK_URL=http://example.com/webhook/post-call python utility/get_conversation.py conv_123abc
        """
    )

    parser.add_argument(
        "conversation_ids",
        nargs="+",
        help="One or more conversation IDs to fetch and process"
    )

    parser.add_argument(
        "--webhook-url",
        default=os.getenv("WEBHOOK_URL"),
        help="Webhook URL to send data to (default: from WEBHOOK_URL env or http://localhost:8000/webhook/post-call)"
    )

    parser.add_argument(
        "--api-key",
        default=os.getenv("ELEVENLABS_API_KEY"),
        help="ElevenLabs API key (default: from ELEVENLABS_API_KEY env)"
    )

    parser.add_argument(
        "--hmac-key",
        default=os.getenv("ELEVENLABS_POST_CALL_HMAC_KEY"),
        help="HMAC key for signing requests (default: from ELEVENLABS_POST_CALL_HMAC_KEY env)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate API key
    if not args.api_key:
        logger.error("ERROR: ELEVENLABS_API_KEY is required")
        logger.error("Set it via environment variable or --api-key flag")
        logger.debug(f"Environment variable ELEVENLABS_API_KEY: {'SET' if os.getenv('ELEVENLABS_API_KEY') else 'NOT SET'}")
        sys.exit(1)

    # Validate HMAC key
    if not args.hmac_key:
        logger.error("ERROR: ELEVENLABS_POST_CALL_HMAC_KEY is required")
        logger.error("Set it via environment variable or --hmac-key flag")
        logger.debug(f"Environment variable ELEVENLABS_POST_CALL_HMAC_KEY: {'SET' if os.getenv('ELEVENLABS_POST_CALL_HMAC_KEY') else 'NOT SET'}")
        sys.exit(1)
    
    # Log API key status (without showing the actual key)
    api_key_preview = args.api_key[:8] + "..." if len(args.api_key) > 8 else "***"
    logger.debug(f"Using API key: {api_key_preview} (length: {len(args.api_key)})")

    # Create conversation getter
    try:
        getter = ConversationGetter(
            api_key=args.api_key,
            hmac_key=args.hmac_key,
            webhook_url=args.webhook_url
        )

        logger.info(f"Using webhook URL: {getter.webhook_url}")

        # Process conversations
        results = getter.process_multiple_conversations(args.conversation_ids)

        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("SUMMARY")
        logger.info(f"{'='*60}")

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        logger.info(f"Total conversations: {total_count}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {total_count - success_count}")

        # Exit with appropriate code
        if success_count == total_count:
            logger.info("\n✓ All conversations processed successfully!")
            sys.exit(0)
        elif success_count > 0:
            logger.warning(f"\n⚠ Partial success: {success_count}/{total_count} conversations processed")
            sys.exit(1)
        else:
            logger.error("\n✗ All conversations failed to process")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
