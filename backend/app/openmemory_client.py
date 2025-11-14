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
            
            if not content:
                logger.error("Cannot store memory: content is required")
                return None
            
            # Validate required metadata fields
            required_fields = ["agent_id", "conversation_id"]
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"Missing required metadata field: {field}")
            
            # Build payload according to OpenMemory API spec
            # See: https://openmemory.cavira.app/docs/api/add-memory
            payload = {
                "content": content,
                "user_id": user_id,
                "metadata": metadata
            }
            
            # Extract tags from metadata if present, or create from category/entities
            tags = []
            if "tags" in metadata:
                tags = metadata.get("tags", [])
            elif "category" in metadata:
                tags.append(metadata["category"])
            if "entities" in metadata:
                tags.extend(metadata.get("entities", []))
            
            if tags:
                payload["tags"] = tags

            client = await self._get_client()
            response = await client.post(
                f"{self.api_url}/memory/add",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            # OpenMemory returns "id", not "memory_id"
            memory_id = result.get("id")
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
            # Build payload according to OpenMemory API spec
            # Query endpoint: POST /memory/query
            # See: https://openmemory.cavira.app/docs/api/query
            payload = {
                "query": query or "",  # Required field (empty string for all memories)
                "k": limit  # Use 'k' not 'limit' per API spec
            }
            
            # Build filters object for proper user isolation
            filters = {}
            
            # Always filter by user_id for proper isolation
            if user_id:
                filters["user_id"] = user_id
            
            # Add metadata filters if provided
            # OpenMemory query API accepts metadata filters in filters object
            if filter_dict:
                # Handle nested metadata filters (e.g., "metadata.agent_id" -> "agent_id")
                metadata_filters = {}
                for key, value in filter_dict.items():
                    if key.startswith("metadata."):
                        # Extract the actual metadata key (remove "metadata." prefix)
                        meta_key = key.replace("metadata.", "")
                        metadata_filters[meta_key] = value
                    elif key not in ["query", "k", "user_id", "filters"]:
                        # Include other filter keys that aren't top-level fields
                        metadata_filters[key] = value
                
                if metadata_filters:
                    # Add metadata filters to filters object
                    # Note: OpenMemory may support nested metadata filters differently
                    # For now, we'll add them as separate filter conditions
                    for key, value in metadata_filters.items():
                        filters[key] = value
            
            # Add filters to payload if we have any
            if filters:
                payload["filters"] = filters

            client = await self._get_client()
            response = await client.post(
                f"{self.api_url}/memory/query",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            # OpenMemory returns memories in different format
            # Check for common response formats (matches, memories, results, data)
            memory_list = result.get("matches", result.get("memories", result.get("results", result.get("data", []))))
            logger.debug(f"Found {len(memory_list)} memories for user {user_id}")
            
            # OpenMemory /memory/query doesn't return metadata, so we need to fetch full details
            # for each memory to get metadata. Fetch in parallel for efficiency.
            if memory_list:
                import asyncio
                async def fetch_full_memory(mem: Dict[str, Any]) -> Dict[str, Any]:
                    """Fetch full memory details including metadata."""
                    memory_id = mem.get("id")
                    if not memory_id:
                        return mem  # Return as-is if no ID
                    
                    try:
                        # GET /memory/{id} returns full memory with metadata
                        mem_response = await client.get(f"{self.api_url}/memory/{memory_id}")
                        mem_response.raise_for_status()
                        full_memory = mem_response.json()
                        # Merge query result fields (score, salience) with full memory
                        full_memory["score"] = mem.get("score")
                        full_memory["salience"] = mem.get("salience")
                        return full_memory
                    except Exception as e:
                        logger.warning(f"Failed to fetch full details for memory {memory_id}: {e}")
                        return mem  # Return query result as fallback
                
                # Fetch full details for all memories in parallel
                tasks = [fetch_full_memory(mem) for mem in memory_list]
                memories = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter out exceptions and return valid memories
                valid_memories = []
                for mem in memories:
                    if isinstance(mem, Exception):
                        logger.warning(f"Error fetching memory: {mem}")
                    else:
                        valid_memories.append(mem)
                
                return valid_memories
            
            return []

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

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing memory in OpenMemory.

        Args:
            memory_id: Memory identifier
            content: New content for the memory (optional, regenerates embeddings if provided)
            tags: Updated tags array (optional, replaces all tags)
            metadata: Updated or additional metadata (optional, merged with existing)

        Returns:
            Updated memory object if successful, None otherwise
        """
        try:
            if not memory_id:
                logger.error("Cannot update memory: memory_id is required")
                return None

            # Build payload with only provided fields
            payload = {}
            if content is not None:
                payload["content"] = content
            if tags is not None:
                payload["tags"] = tags
            if metadata is not None:
                payload["metadata"] = metadata

            if not payload:
                logger.warning("No fields provided to update")
                return None

            client = await self._get_client()
            
            # Use PATCH endpoint as per OpenMemory API documentation
            # PATCH /memory/{memory_id}
            response = await client.patch(
                f"{self.api_url}/memory/{memory_id}",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                f"Updated memory {memory_id} "
                f"(fields: {', '.join(payload.keys())})"
            )
            return result

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Memory {memory_id} not found")
                return None
            logger.error(f"HTTP error updating memory {memory_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}", exc_info=True)
            return None

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
            # DELETE /memory/{memory_id}
            response = await client.delete(
                f"{self.api_url}/memory/{memory_id}"
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
        entities: List[str],
        sector: str = "semantic"
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
            from app.memory_utils import get_content_hash, prepare_memory_for_storage
            settings = get_settings()
            
            # Mark as shareable if importance >= threshold
            is_shareable = importance >= settings.high_importance_threshold
            
            # Prepare memory with content hash
            memory_data = prepare_memory_for_storage(
                content=content,
                category=category,
                sector=sector,
                importance=importance,
                entities=entities,
                caller_id=caller_id,
                agent_id=agent_id,
                conversation_id=conversation_id
            )
            
            metadata = memory_data["metadata"]
            metadata["shareable"] = is_shareable
            metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Store memory with tags
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
        similarity_threshold: float = 0.85,
        content_hash: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find similar existing memory for deduplication.
        
        Uses content hash for exact duplicate detection (fast) and
        semantic search for similar memories.

        Args:
            caller_id: Caller identifier
            agent_id: Agent identifier
            content: Memory content to check
            similarity_threshold: Minimum similarity score
            content_hash: Optional pre-computed content hash

        Returns:
            Similar memory if found, None otherwise
        """
        try:
            from app.memory_utils import get_content_hash
            
            # Step 1: Check for exact duplicate using content hash (fast)
            if content_hash is None:
                content_hash = get_content_hash(content)
            
            # Query by content hash in metadata
            hash_memories = await self.client.search_memories(
                user_id=caller_id,
                query="",  # Empty query, using filters only
                filter_dict={
                    "metadata.agent_id": agent_id,
                    "metadata.content_hash": content_hash
                },
                limit=1
            )
            
            if hash_memories:
                logger.info(
                    f"Found exact duplicate (hash match) for caller {caller_id}"
                )
                return hash_memories[0]
            
            # Step 2: Check for similar memory using semantic search
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
    
    async def batch_find_similar_memories(
        self,
        caller_id: str,
        agent_id: str,
        memories: List[Dict[str, Any]],
        similarity_threshold: float = 0.85
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Batch find similar memories for multiple extracted memories.
        
        This is more efficient than calling find_similar_memory N times.
        
        Args:
            caller_id: Caller identifier
            agent_id: Agent identifier
            memories: List of extracted memories with 'content' field
            similarity_threshold: Minimum similarity score
            
        Returns:
            Dictionary mapping memory content hash to similar memory (if found)
        """
        from app.memory_utils import get_content_hash
        import asyncio
        
        try:
            # Step 1: Get all content hashes
            memory_hashes = {}
            for memory in memories:
                content = memory.get("content", "")
                if content:
                    content_hash = get_content_hash(content)
                    memory_hashes[content_hash] = memory
            
            # Step 2: Query all existing memories for this caller/agent
            # We'll get all memories and match by hash and semantic similarity
            all_existing = await self.client.search_memories(
                user_id=caller_id,
                query="",  # Empty query to get all
                filter_dict={"metadata.agent_id": agent_id},
                limit=1000  # Get all memories for comparison
            )
            
            # Step 3: Build hash index of existing memories
            existing_by_hash = {}
            for existing in all_existing:
                metadata = existing.get("metadata", {})
                if isinstance(metadata, dict):
                    existing_hash = metadata.get("content_hash")
                    if existing_hash:
                        existing_by_hash[existing_hash] = existing
            
            # Step 4: Match by hash first (exact duplicates)
            results = {}
            for content_hash, memory in memory_hashes.items():
                if content_hash in existing_by_hash:
                    # Exact duplicate found
                    results[content_hash] = existing_by_hash[content_hash]
                else:
                    # No exact match, will need semantic search
                    results[content_hash] = None
            
            # Step 5: For memories without hash match, do semantic search
            # (This could be optimized further with batch semantic search if API supports it)
            for content_hash, memory in memory_hashes.items():
                if results[content_hash] is None:
                    # Do individual semantic search for this memory
                    similar = await self.find_similar_memory(
                        caller_id=caller_id,
                        agent_id=agent_id,
                        content=memory.get("content", ""),
                        similarity_threshold=similarity_threshold,
                        content_hash=content_hash
                    )
                    results[content_hash] = similar
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch_find_similar_memories: {e}", exc_info=True)
            # Fallback: return empty results
            return {get_content_hash(m.get("content", "")): None for m in memories}

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
            
            # Build filter - always exclude agent profiles and only get conversation memories
            filter_dict = {
                "metadata.type": "conversation_memory"  # Only conversation memories, not agent profiles
            }
            if not search_all_agents and agent_id:
                filter_dict["metadata.agent_id"] = agent_id
            
            # Search memories (optimized for <3s target)
            # user_id is now properly filtered via filters.user_id in search_memories()
            memories = await self.client.search_memories(
                user_id=caller_id,
                query=query,
                filter_dict=filter_dict,
                limit=limit
            )
            
            # Post-filter to ensure no agent profiles slip through
            # Also filter by relevance threshold
            filtered_memories = []
            for m in memories:
                # Skip agent profiles (defensive check)
                metadata = m.get("metadata", {})
                if isinstance(metadata, dict):
                    mem_type = metadata.get("type")
                    if mem_type == "agent_profile":
                        continue
                    # Only include conversation_memory type (or legacy memories without type)
                    if mem_type and mem_type != "conversation_memory":
                        continue
                
                # Filter by relevance threshold
                score = m.get("score", 0)
                if score >= relevance_threshold:
                    filtered_memories.append(m)
            
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
        Mark a memory as shareable across agents by updating its metadata.
        
        Args:
            memory_id: Memory identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update memory metadata to mark as shareable using the update API
            result = await self.client.update_memory(
                memory_id=memory_id,
                metadata={"shareable": True}
            )
            
            if result:
                logger.info(f"Marked memory {memory_id} as shareable")
                return True
            else:
                logger.warning(f"Failed to mark memory {memory_id} as shareable")
                return False
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
