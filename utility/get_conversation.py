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
    WEBHOOK_URL: Webhook endpoint URL (default: http://localhost:8000/webhook/post-call)
"""

import os
import sys
import json
import logging
import argparse
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path

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

    def __init__(self, api_key: str, webhook_url: Optional[str] = None):
        """
        Initialize the conversation getter.

        Args:
            api_key: ElevenLabs API key
            webhook_url: Optional webhook URL (defaults to localhost)
        """
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required")

        self.api_key = api_key
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

        try:
            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched conversation {conversation_id}")
            logger.debug(f"Response data: {json.dumps(data, indent=2)}")

            return data

        except requests.HTTPError as e:
            logger.error(f"HTTP error fetching conversation {conversation_id}: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"Error fetching conversation {conversation_id}: {e}")
            raise

    def format_as_webhook(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format conversation data to match ElevenLabs webhook structure.

        The webhook expects a specific format with type and data fields.
        This converts the API response to match that structure.

        Args:
            conversation_data: Raw conversation data from API

        Returns:
            Formatted webhook payload
        """
        # Extract key fields from conversation data
        conversation_id = conversation_data.get("conversation_id")
        agent_id = conversation_data.get("agent_id")

        # Build transcript array from transcript field if it exists
        transcript = []
        if "transcript" in conversation_data:
            transcript = conversation_data["transcript"]

        # Format as post_call_transcription webhook
        webhook_payload = {
            "type": "post_call_transcription",
            "data": {
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "transcript": transcript,
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

    def send_to_webhook(self, webhook_payload: Dict[str, Any]) -> bool:
        """
        Send formatted conversation data to webhook endpoint.

        Note: This sends without HMAC signature since it's an internal call.
        The webhook endpoint should handle this appropriately.

        Args:
            webhook_payload: Formatted webhook payload

        Returns:
            True if successful, False otherwise
        """
        conversation_id = webhook_payload.get("data", {}).get("conversation_id")

        logger.info(f"Sending conversation {conversation_id} to webhook: {self.webhook_url}")

        try:
            response = requests.post(
                self.webhook_url,
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Internal-Request": "true"  # Flag for internal requests
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
        sys.exit(1)

    # Create conversation getter
    try:
        getter = ConversationGetter(
            api_key=args.api_key,
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
