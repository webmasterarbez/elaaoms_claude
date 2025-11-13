"""
ElevenLabs API client for fetching agent profiles.
"""

import logging
import httpx
from typing import Optional, Dict, Any
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ElevenLabsClient:
    """Client for interacting with ElevenLabs API."""

    def __init__(self):
        self.api_url = settings.elevenlabs_api_url
        self.api_key = settings.elevenlabs_api_key
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def get_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch agent profile from ElevenLabs API.

        API Endpoint: GET /convai/agents/{agent_id}
        Docs: https://elevenlabs.io/docs/api-reference/agents/get

        Args:
            agent_id: Agent identifier

        Returns:
            Agent profile data if successful, None otherwise
        """
        try:
            url = f"{self.api_url}/convai/agents/{agent_id}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                profile = response.json()
                logger.info(f"Successfully fetched agent profile for {agent_id}")
                return profile

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching agent profile for {agent_id}: "
                f"{e.response.status_code} - {e.response.text}"
            )
            return None

        except httpx.RequestError as e:
            logger.error(f"Request error fetching agent profile for {agent_id}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching agent profile: {e}", exc_info=True)
            return None

    async def get_conversation_details(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch conversation details from ElevenLabs API.

        API Endpoint: GET /convai/conversations/{conversation_id}

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation details if successful, None otherwise
        """
        try:
            url = f"{self.api_url}/convai/conversations/{conversation_id}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                conversation = response.json()
                logger.info(f"Successfully fetched conversation details for {conversation_id}")
                return conversation

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching conversation {conversation_id}: "
                f"{e.response.status_code} - {e.response.text}"
            )
            return None

        except httpx.RequestError as e:
            logger.error(f"Request error fetching conversation {conversation_id}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error fetching conversation: {e}", exc_info=True)
            return None
