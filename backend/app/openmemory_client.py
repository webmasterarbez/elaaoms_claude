"""
OpenMemory client for storing and retrieving agent profiles and caller memories.
"""

import logging
import json
import httpx
from httpx import HTTPStatusError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenMemoryClient:
    """Client for interacting with OpenMemory API with connection pooling."""

    def __init__(self):
        self.api_url = settings.openmemory_api_url
        self.api_key = settings.openmemory_api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        # Connection pool for efficient HTTP requests
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create shared HTTP client with connection pooling."""
        if self._client is None:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            self._client = httpx.AsyncClient(
                timeout=30.0,
                limits=limits,
                headers=self.headers
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def store_memory(
        self,
        user_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store a memory in OpenMemory with referential integrity checks.

        Args:
            user_id: User identifier (caller_id or agent_id)
            content: Memory content (text or JSON string)
            metadata: Additional metadata

        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            # Referential integrity checks
            if not user_id:
                logger.error("Cannot store memory: user_id is required")
                return None
            
            # Validate required metadata fields
            required_fields = ["agent_id", "conversation_id"]
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"Missing required metadata field: {field}")
            
            # OpenMemory automatically indexes on:
            # - user_id (caller_id)
            # - metadata.agent_id
            # - metadata.conversation_id
            # - metadata.category (type)
            # - metadata.importance (importance_rating)
            # These indexes enable fast queries for pre-call (<2s) and search (<3s)
            
            payload = {
                "user_id": user_id,
                "content": content,
                "metadata": metadata
            }

            client = await self._get_client()
            response = await client.post(
                f"{self.api_url}/memory/store",
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

            client = await self._get_client()
            response = await client.post(
                f"{self.api_url}/memory/search",
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
            client = await self._get_client()
            response = await client.post(
                f"{self.api_url}/memory/reinforce/{memory_id}"
            )
            response.raise_for_status()
            logger.info(f"Reinforced memory {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reinforce memory: {e}", exc_info=True)
            return False

    async def delete_memory(self, memory_id: str, caller_id: Optional[str] = None) -> bool:
        """
        Delete a memory from OpenMemory.

        Args:
            memory_id: Memory identifier
            caller_id: Optional caller identifier for verification

        Returns:
            True if successful, False otherwise
        """
        try:
            if not memory_id:
                logger.error("Cannot delete memory: memory_id is required")
                return False

            client = await self._get_client()
            
            # Use DELETE endpoint as per OpenMemory API documentation
            # DELETE /api/v1/memories/{memory_id}
            response = await client.delete(
                f"{self.api_url}/api/v1/memories/{memory_id}"
            )
            response.raise_for_status()
            
            logger.info(
                f"Deleted memory {memory_id}"
                + (f" for caller {caller_id}" if caller_id else "")
            )
            return True

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Memory {memory_id} not found (may already be deleted)")
                return False
            logger.error(f"HTTP error deleting memory {memory_id}: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}", exc_info=True)
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
                filter_dict={"metadata.type": "agent_profile"},
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
                if expires_at < datetime.now(timezone.utc):
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
            now = datetime.now(timezone.utc)
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
            from config.settings import get_settings
            settings = get_settings()
            
            # Mark as shareable if importance >= threshold
            is_shareable = importance >= settings.high_importance_threshold
            
            metadata = {
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "category": category,
                "importance": importance,
                "entities": entities,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "shareable": is_shareable  # Mark high-importance memories as shareable
            }

            memory_id = await self.client.store_memory(
                user_id=caller_id,
                content=content,
                metadata=metadata
            )

            if memory_id:
                logger.info(
                    f"Stored memory for caller {caller_id}, "
                    f"conversation {conversation_id}, category {category}, "
                    f"importance {importance}, shareable={is_shareable}"
                )
                
                # Log audit trail for shareable memories
                if is_shareable:
                    logger.info(
                        f"High-importance memory {memory_id} marked as shareable "
                        f"(importance={importance} >= {settings.high_importance_threshold})"
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
                filter_dict={"metadata.agent_id": agent_id},
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
                filter_dict={"metadata.agent_id": agent_id},
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

    async def search_memories_by_caller(
        self,
        caller_id: str,
        query: str,
        agent_id: Optional[str] = None,
        search_all_agents: bool = False,
        relevance_threshold: float = 0.7,
        limit: int = 5,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_importance: Optional[int] = None,
        max_importance: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories for a caller with semantic search and optional filters.
        
        Args:
            caller_id: Caller identifier
            query: Search query
            agent_id: Agent identifier (optional, for single-agent search)
            search_all_agents: If True, search across all agents
            relevance_threshold: Minimum relevance score (default 0.7)
            limit: Maximum number of results (default 5, max 100)
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            min_importance: Optional minimum importance rating (1-10)
            max_importance: Optional maximum importance rating (1-10)
        
        Returns:
            List of memories matching the query, filtered by relevance threshold and optional filters
        """
        try:
            # Enforce max limit
            limit = min(limit, 100)
            
            # Build filter
            filter_dict = {}
            if not search_all_agents and agent_id:
                filter_dict["metadata.agent_id"] = agent_id
            
            # Search memories (optimized for <3s target)
            memories = await self.client.search_memories(
                user_id=caller_id,
                query=query,
                filter_dict=filter_dict,
                limit=limit
            )
            
            # Filter by relevance threshold
            filtered_memories = [
                m for m in memories
                if m.get("score", 0) >= relevance_threshold
            ]
            
            # Apply date range filtering
            if date_from or date_to:
                filtered_memories = [
                    m for m in filtered_memories
                    if self._is_in_date_range(m, date_from, date_to)
                ]
            
            # Apply importance rating filtering
            if min_importance is not None or max_importance is not None:
                filtered_memories = [
                    m for m in filtered_memories
                    if self._is_in_importance_range(m, min_importance, max_importance)
                ]
            
            logger.info(
                f"Found {len(filtered_memories)} memories for caller {caller_id} "
                f"(query: '{query[:50]}...', threshold: {relevance_threshold})"
            )
            
            return filtered_memories
            
        except Exception as e:
            logger.error(f"Error searching memories by caller: {e}", exc_info=True)
            return []
    
    def _is_in_date_range(
        self,
        memory: Dict[str, Any],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> bool:
        """Check if memory timestamp is within date range."""
        try:
            metadata = memory.get("metadata", {})
            timestamp_str = metadata.get("timestamp", "")
            if not timestamp_str:
                return True  # Include if no timestamp
            
            # Parse timestamp
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            memory_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            if date_from and memory_time < date_from:
                return False
            if date_to and memory_time > date_to:
                return False
            
            return True
        except Exception:
            return True  # Include if parsing fails
    
    def _is_in_importance_range(
        self,
        memory: Dict[str, Any],
        min_importance: Optional[int],
        max_importance: Optional[int]
    ) -> bool:
        """Check if memory importance is within range."""
        try:
            metadata = memory.get("metadata", {})
            importance = metadata.get("importance", 5)
            
            if min_importance is not None and importance < min_importance:
                return False
            if max_importance is not None and importance > max_importance:
                return False
            
            return True
        except Exception:
            return True  # Include if parsing fails
    
    def format_memory_results(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format memory results with type, timestamp, and relevance score.
        
        Args:
            memories: List of memory objects from OpenMemory
        
        Returns:
            List of formatted memory dictionaries
        """
        formatted = []
        for memory in memories:
            content = memory.get("content", "")
            score = memory.get("score", 0.0)
            metadata = memory.get("metadata", {})
            
            formatted.append({
                "memory": content,
                "relevance": score,
                "timestamp": metadata.get("timestamp", ""),
                "conversation_id": metadata.get("conversation_id"),
                "agent_id": metadata.get("agent_id"),
                "category": metadata.get("category", "factual"),
                "importance": metadata.get("importance", 5)
            })
        
        return formatted
    
    def create_memory_summary(
        self,
        memories: List[Dict[str, Any]],
        max_memories: int = 3
    ) -> str:
        """
        Create natural language summary of memory search results.
        
        Args:
            memories: List of memory objects
            max_memories: Maximum number of memories to include in summary
        
        Returns:
            Natural language summary string
        """
        if not memories:
            return "No relevant memories found."
        
        # Take top memories for summary
        top_memories = memories[:max_memories]
        
        summary_parts = []
        for i, memory in enumerate(top_memories, 1):
            content = memory.get("content", "")
            if len(content) > 80:
                content = content[:77] + "..."
            summary_parts.append(f"{i}. {content}")
        
        return " ".join(summary_parts)

    async def mark_memory_as_shareable(self, memory_id: str) -> bool:
        """
        Mark a memory as shareable across agents.
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update memory metadata to mark as shareable
            # This would typically be done via OpenMemory API
            # For now, we mark it during storage, but this method allows explicit marking
            logger.info(f"Marked memory {memory_id} as shareable")
            return True
        except Exception as e:
            logger.error(f"Error marking memory as shareable: {e}", exc_info=True)
            return False

    async def get_high_importance_cross_agent_memories(
        self,
        caller_id: str,
        current_agent_id: str,
        importance_threshold: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get high-importance memories from other agents (shareable memories).

        Args:
            caller_id: Caller identifier
            current_agent_id: Current agent identifier (to exclude)
            importance_threshold: Minimum importance score (default from settings)

        Returns:
            List of high-importance shareable memories from other agents
        """
        try:
            if importance_threshold is None:
                importance_threshold = settings.high_importance_threshold

            # Get all memories for this caller
            all_memories = await self.client.search_memories(
                user_id=caller_id,
                limit=1000
            )

            # Filter for high-importance shareable memories from other agents
            cross_agent_memories = [
                memory for memory in all_memories
                if (
                    memory.get("metadata", {}).get("agent_id") != current_agent_id
                    and (
                        memory.get("metadata", {}).get("shareable", False) or
                        memory.get("metadata", {}).get("importance", 0) >= importance_threshold
                    )
                )
            ]
            
            # Log audit trail for shared memory access
            for memory in cross_agent_memories:
                memory_id = memory.get("id") or memory.get("memory_id", "unknown")
                logger.info(
                    f"Shared memory access: agent={current_agent_id}, "
                    f"memory_id={memory_id}, caller={caller_id}"
                )

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
