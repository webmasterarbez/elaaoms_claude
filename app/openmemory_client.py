"""
OpenMemory client for storing and retrieving agent profiles and caller memories.
"""

import logging
import json
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenMemoryClient:
    """Client for interacting with OpenMemory API."""

    def __init__(self):
        self.api_url = settings.openmemory_api_url
        self.api_key = settings.openmemory_api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }

    async def store_memory(
        self,
        user_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store a memory in OpenMemory.

        Args:
            user_id: User identifier (caller_id or agent_id)
            content: Memory content (text or JSON string)
            metadata: Additional metadata

        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            payload = {
                "user_id": user_id,
                "content": content,
                "metadata": metadata
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/memory/store",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                memory_id = result.get("memory_id") or result.get("id")
                logger.info(f"Stored memory {memory_id} for user {user_id}")
                return memory_id

        except Exception as e:
            logger.error(f"Failed to store memory: {e}", exc_info=True)
            return None

    async def search_memories(
        self,
        user_id: str,
        query: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories in OpenMemory.

        Args:
            user_id: User identifier
            query: Semantic search query (optional)
            filter_dict: Metadata filters (optional)
            limit: Maximum number of results

        Returns:
            List of memory objects
        """
        try:
            payload = {
                "user_id": user_id,
                "limit": limit
            }

            if query:
                payload["query"] = query

            if filter_dict:
                payload["filter"] = filter_dict

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/memory/search",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                memories = result.get("memories", result.get("results", []))
                logger.debug(f"Found {len(memories)} memories for user {user_id}")
                return memories

        except Exception as e:
            logger.error(f"Failed to search memories: {e}", exc_info=True)
            return []

    async def reinforce_memory(self, memory_id: str) -> bool:
        """
        Reinforce an existing memory to boost its importance.

        Args:
            memory_id: Memory identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/memory/reinforce/{memory_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"Reinforced memory {memory_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to reinforce memory: {e}", exc_info=True)
            return False


class AgentProfileManager:
    """Manages agent profiles in OpenMemory."""

    def __init__(self, client: OpenMemoryClient):
        self.client = client
        self.ttl_hours = settings.agent_profile_ttl_hours

    async def get_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve agent profile from OpenMemory.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent profile dict if found and not expired, None otherwise
        """
        try:
            memories = await self.client.search_memories(
                user_id=agent_id,
                filter_dict={"type": "agent_profile"},
                limit=1
            )

            if not memories:
                logger.info(f"No agent profile found for {agent_id}")
                return None

            memory = memories[0]
            metadata = memory.get("metadata", {})
            expires_at_str = metadata.get("expires_at")

            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if expires_at < datetime.utcnow():
                    logger.info(f"Agent profile for {agent_id} has expired")
                    return None

            # Parse JSON content
            content = memory.get("content", "{}")
            profile = json.loads(content) if isinstance(content, str) else content

            logger.info(f"Retrieved agent profile for {agent_id}")
            return profile

        except Exception as e:
            logger.error(f"Error retrieving agent profile: {e}", exc_info=True)
            return None

    async def store_agent_profile(self, agent_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Store or update agent profile in OpenMemory.

        Args:
            agent_id: Agent identifier
            profile_data: Agent profile data from ElevenLabs API

        Returns:
            True if successful, False otherwise
        """
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=self.ttl_hours)

            content = json.dumps(profile_data)
            metadata = {
                "type": "agent_profile",
                "agent_id": agent_id,
                "last_updated": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "source": "elevenlabs_api"
            }

            memory_id = await self.client.store_memory(
                user_id=agent_id,
                content=content,
                metadata=metadata
            )

            if memory_id:
                logger.info(f"Stored agent profile for {agent_id}")
                return True
            else:
                logger.error(f"Failed to store agent profile for {agent_id}")
                return False

        except Exception as e:
            logger.error(f"Error storing agent profile: {e}", exc_info=True)
            return False


class CallerMemoryManager:
    """Manages caller memories in OpenMemory."""

    def __init__(self, client: OpenMemoryClient):
        self.client = client

    async def store_caller_memory(
        self,
        caller_id: str,
        agent_id: str,
        conversation_id: str,
        content: str,
        category: str,
        importance: int,
        entities: List[str]
    ) -> Optional[str]:
        """
        Store a caller memory in OpenMemory.

        Args:
            caller_id: Caller identifier (phone number)
            agent_id: Agent identifier
            conversation_id: Conversation identifier
            content: Memory content
            category: Memory category (factual, preference, issue, emotional, relational)
            importance: Importance score (1-10)
            entities: List of entities mentioned

        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            metadata = {
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "category": category,
                "importance": importance,
                "entities": entities,
                "timestamp": datetime.utcnow().isoformat()
            }

            memory_id = await self.client.store_memory(
                user_id=caller_id,
                content=content,
                metadata=metadata
            )

            if memory_id:
                logger.info(
                    f"Stored memory for caller {caller_id}, "
                    f"conversation {conversation_id}, category {category}"
                )

            return memory_id

        except Exception as e:
            logger.error(f"Error storing caller memory: {e}", exc_info=True)
            return None

    async def find_similar_memory(
        self,
        caller_id: str,
        agent_id: str,
        content: str,
        similarity_threshold: float = 0.85
    ) -> Optional[Dict[str, Any]]:
        """
        Find similar existing memory for deduplication.

        Args:
            caller_id: Caller identifier
            agent_id: Agent identifier
            content: Memory content to check
            similarity_threshold: Minimum similarity score

        Returns:
            Similar memory if found, None otherwise
        """
        try:
            memories = await self.client.search_memories(
                user_id=caller_id,
                query=content,
                filter_dict={"agent_id": agent_id},
                limit=1
            )

            if memories:
                memory = memories[0]
                score = memory.get("score", 0)

                if score >= similarity_threshold:
                    logger.info(
                        f"Found similar memory with score {score:.2f} "
                        f"for caller {caller_id}"
                    )
                    return memory

            return None

        except Exception as e:
            logger.error(f"Error finding similar memory: {e}", exc_info=True)
            return None

    async def get_last_conversation_memories(
        self,
        caller_id: str,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all memories from the last conversation.

        Args:
            caller_id: Caller identifier
            agent_id: Agent identifier

        Returns:
            List of memories from the last conversation
        """
        try:
            # Get all memories for this caller + agent
            all_memories = await self.client.search_memories(
                user_id=caller_id,
                filter_dict={"agent_id": agent_id},
                limit=1000
            )

            if not all_memories:
                logger.info(f"No memories found for caller {caller_id}, agent {agent_id}")
                return []

            # Group by conversation_id
            conversations = {}
            for memory in all_memories:
                metadata = memory.get("metadata", {})
                conv_id = metadata.get("conversation_id")
                timestamp_str = metadata.get("timestamp")

                if conv_id and timestamp_str:
                    if conv_id not in conversations:
                        conversations[conv_id] = []
                    conversations[conv_id].append(memory)

            if not conversations:
                return []

            # Find conversation with latest timestamp
            latest_conv_id = max(
                conversations.keys(),
                key=lambda cid: max(
                    datetime.fromisoformat(m["metadata"]["timestamp"].replace('Z', '+00:00'))
                    for m in conversations[cid]
                )
            )

            last_memories = conversations[latest_conv_id]
            logger.info(
                f"Retrieved {len(last_memories)} memories from last conversation "
                f"{latest_conv_id} for caller {caller_id}"
            )

            return last_memories

        except Exception as e:
            logger.error(f"Error getting last conversation memories: {e}", exc_info=True)
            return []

    async def get_high_importance_cross_agent_memories(
        self,
        caller_id: str,
        current_agent_id: str,
        importance_threshold: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get high-importance memories from other agents.

        Args:
            caller_id: Caller identifier
            current_agent_id: Current agent identifier (to exclude)
            importance_threshold: Minimum importance score (default from settings)

        Returns:
            List of high-importance memories from other agents
        """
        try:
            if importance_threshold is None:
                importance_threshold = settings.high_importance_threshold

            # Get all memories for this caller
            all_memories = await self.client.search_memories(
                user_id=caller_id,
                limit=1000
            )

            # Filter for high-importance from other agents
            cross_agent_memories = [
                memory for memory in all_memories
                if (
                    memory.get("metadata", {}).get("agent_id") != current_agent_id
                    and memory.get("metadata", {}).get("importance", 0) >= importance_threshold
                )
            ]

            # Sort by importance (descending) and take top 5
            cross_agent_memories.sort(
                key=lambda m: m.get("metadata", {}).get("importance", 0),
                reverse=True
            )

            result = cross_agent_memories[:5]

            logger.info(
                f"Retrieved {len(result)} high-importance cross-agent memories "
                f"for caller {caller_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Error getting cross-agent memories: {e}", exc_info=True)
            return []
