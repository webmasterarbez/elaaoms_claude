"""
Background job processor for memory extraction.
"""

import logging
import asyncio
from queue import Queue, Empty
from threading import Thread
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import time
import json
import os

from app.openmemory_client import (
    OpenMemoryClient,
    AgentProfileManager,
    CallerMemoryManager
)
from app.elevenlabs_client import ElevenLabsClient
from app.llm_service import LLMService

logger = logging.getLogger(__name__)


class MemoryExtractionJob:
    """Memory extraction job data."""

    def __init__(
        self,
        conversation_id: str,
        agent_id: str,
        caller_id: str,
        transcript: List[Dict[str, str]],
        duration: int,
        status: str
    ):
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.caller_id = caller_id
        self.transcript = transcript
        self.duration = duration
        self.status = status
        self.created_at = datetime.now(timezone.utc)


class BackgroundJobProcessor:
    """Processes memory extraction jobs in the background."""

    def __init__(self):
        self.queue = Queue()
        self.worker_thread = None
        self.running = False

        # Initialize clients
        self.openmemory_client = OpenMemoryClient()
        self.agent_profile_manager = AgentProfileManager(self.openmemory_client)
        self.caller_memory_manager = CallerMemoryManager(self.openmemory_client)
        self.elevenlabs_client = ElevenLabsClient()
        self.llm_service = LLMService()

    def start(self):
        """Start the background worker thread."""
        if self.running:
            logger.warning("Background worker already running")
            return

        self.running = True
        self.worker_thread = Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("Background job processor started")

    def stop(self):
        """Stop the background worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Background job processor stopped")

    def enqueue_job(self, job: MemoryExtractionJob):
        """Add a job to the queue."""
        self.queue.put(job)
        logger.info(
            f"Enqueued memory extraction job for conversation {job.conversation_id}"
        )

    def _worker(self):
        """Worker thread that processes jobs from the queue."""
        logger.info("Background worker thread started")

        while self.running:
            try:
                # Get job from queue (blocking with timeout)
                try:
                    job = self.queue.get(timeout=1)
                except Empty:
                    continue

                # Process the job
                logger.info(f"Processing job for conversation {job.conversation_id}")
                asyncio.run(self._process_job(job))

                self.queue.task_done()

            except Exception as e:
                logger.error(f"Error in background worker: {e}", exc_info=True)

        logger.info("Background worker thread stopped")

    async def _process_job(self, job: MemoryExtractionJob):
        """
        Process a memory extraction job with retry logic.

        Steps:
        1. Fetch/update agent profile from ElevenLabs API
        2. Extract memories from transcript using LLM (with retry)
        3. Deduplicate and store memories in OpenMemory

        Retry logic: 3 attempts with exponential backoff (1min, 5min, 30min)
        """
        from config.settings import get_settings
        settings = get_settings()
        
        retry_delays = [60, 300, 1800]  # 1 minute, 5 minutes, 30 minutes
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Step 1: Fetch/update agent profile
                logger.info(f"Fetching agent profile for {job.agent_id}")
                await self._fetch_and_update_agent_profile(job.agent_id)

                # Step 2: Extract memories from transcript using LLM
                logger.info(
                    f"Extracting memories from conversation {job.conversation_id} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                extracted_memories = await self.llm_service.extract_memories(
                    transcript=job.transcript,
                    agent_id=job.agent_id,
                    caller_id=job.caller_id,
                    conversation_id=job.conversation_id
                )

                if not extracted_memories:
                    logger.warning(
                        f"No memories extracted from conversation {job.conversation_id}"
                    )
                    # This is not a failure - just no memories found
                    return

                # Step 3: Store memories with deduplication and retry
                logger.info(
                    f"Storing {len(extracted_memories)} memories "
                    f"for conversation {job.conversation_id}"
                )
                storage_result = await self._store_memories_with_deduplication(
                    caller_id=job.caller_id,
                    agent_id=job.agent_id,
                    conversation_id=job.conversation_id,
                    memories=extracted_memories
                )
                
                # Step 4: Invalidate cache for this caller/agent
                from app.memory_cache import get_memory_cache
                cache = get_memory_cache()
                cache.invalidate(job.caller_id, job.agent_id)
                logger.debug(f"Invalidated cache for {job.caller_id}:{job.agent_id}")

                stored_count = storage_result["stats"]["stored_count"]
                reinforced_count = storage_result["stats"]["reinforced_count"]
                failed_count = storage_result["stats"]["failed_count"]
                
                logger.info(
                    f"Memory storage complete for conversation {job.conversation_id}: "
                    f"{stored_count} new memories stored, {reinforced_count} existing reinforced, "
                    f"{failed_count} failed"
                )
                
                # Step 4: Validate stored memories if enabled
                if settings.memory_validation_enabled:
                    await self._validate_stored_memories(
                        caller_id=job.caller_id,
                        agent_id=job.agent_id,
                        conversation_id=job.conversation_id,
                        expected_count=len(extracted_memories),
                        storage_result=storage_result
                    )
                
                return  # Success - exit retry loop

            except Exception as e:
                logger.error(
                    f"Error processing job for conversation {job.conversation_id} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=True
                )
                
                # If this was the last attempt, save transcript for manual processing
                if attempt == max_retries - 1:
                    logger.error(
                        f"All {max_retries} retry attempts exhausted for conversation "
                        f"{job.conversation_id}. Saving transcript for manual processing."
                    )
                    await self._save_failed_transcript(job, settings)
                    return
                
                # Wait before retrying (exponential backoff)
                delay = retry_delays[attempt]
                logger.info(
                    f"Retrying in {delay} seconds (attempt {attempt + 2}/{max_retries})"
                )
                await asyncio.sleep(delay)
    
    async def _save_failed_transcript(
        self,
        job: MemoryExtractionJob,
        settings
    ) -> None:
        """
        Save transcript with extraction_failed status after retries exhausted.
        
        Args:
            job: Memory extraction job
            settings: Application settings
        """
        try:
            from app.storage import save_transcription_payload
            
            # Create payload with failed status
            failed_payload = {
                "conversation_id": job.conversation_id,
                "agent_id": job.agent_id,
                "caller_id": job.caller_id,
                "transcript": job.transcript,
                "duration": job.duration,
                "status": "extraction_failed",
                "extraction_attempts": 3,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": "Memory extraction failed after 3 retry attempts"
            }
            
            # Save to payloads directory
            file_path = save_transcription_payload(
                settings.elevenlabs_post_call_payload_path,
                job.conversation_id,
                failed_payload
            )
            
            logger.info(
                f"Saved failed transcript to {file_path} for manual processing"
            )
            
        except Exception as e:
            logger.error(
                f"Error saving failed transcript for conversation {job.conversation_id}: {e}",
                exc_info=True
            )

    async def _fetch_and_update_agent_profile(self, agent_id: str):
        """Fetch agent profile from ElevenLabs and update in OpenMemory if needed."""
        try:
            # Check if profile exists and is fresh
            existing_profile = await self.agent_profile_manager.get_agent_profile(agent_id)

            if existing_profile:
                logger.info(f"Agent profile for {agent_id} is cached and fresh")
                return

            # Fetch fresh profile from ElevenLabs API
            logger.info(f"Fetching fresh agent profile from ElevenLabs for {agent_id}")
            profile_data = await self.elevenlabs_client.get_agent_profile(agent_id)

            if not profile_data:
                logger.error(f"Failed to fetch agent profile for {agent_id}")
                return

            # Store in OpenMemory
            success = await self.agent_profile_manager.store_agent_profile(
                agent_id=agent_id,
                profile_data=profile_data
            )

            if success:
                logger.info(f"Successfully updated agent profile for {agent_id}")
            else:
                logger.error(f"Failed to store agent profile for {agent_id}")

        except Exception as e:
            logger.error(f"Error fetching/updating agent profile: {e}", exc_info=True)

    async def _store_memories_with_deduplication(
        self,
        caller_id: str,
        agent_id: str,
        conversation_id: str,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store memories with deduplication logic and retry mechanism.

        Returns:
            Dictionary with detailed results: {
                "stored": [memory_ids],
                "reinforced": [memory_ids],
                "failed": [{"memory": {...}, "error": str}],
                "stats": {
                    "stored_count": int,
                    "reinforced_count": int,
                    "failed_count": int,
                    "total_count": int
                }
            }
        """
        from config.settings import get_settings
        settings = get_settings()
        
        stored_memory_ids = []
        reinforced_memory_ids = []
        failed_memories = []
        
        # Step 1: Batch find similar memories (more efficient than one-by-one)
        logger.info(f"Batch checking for duplicates among {len(memories)} memories")
        similarity_threshold = settings.memory_similarity_threshold
        
        try:
            similar_memories_map = await self.caller_memory_manager.batch_find_similar_memories(
                caller_id=caller_id,
                agent_id=agent_id,
                memories=memories,
                similarity_threshold=similarity_threshold
            )
            logger.info(f"Batch deduplication complete: {len(similar_memories_map)} memories checked")
        except Exception as e:
            logger.warning(f"Batch deduplication failed, falling back to individual checks: {e}")
            similar_memories_map = {}
        
        # Step 2: Process each memory
        from app.memory_utils import get_content_hash
        
        for memory in memories:
            try:
                content = memory.get("content", "")
                category = memory.get("category", "factual")
                sector = memory.get("sector", "semantic")  # Get sector from extracted memory
                importance = memory.get("importance", 5)
                entities = memory.get("entities", [])

                if not content:
                    logger.warning("Skipping memory with empty content")
                    continue
                
                # Validate content - reject bad content before storage
                if not self._validate_memory_content(content):
                    logger.warning(
                        f"Rejecting memory with invalid content (system/config detected): "
                        f"{content[:100]}..."
                    )
                    failed_memories.append({
                        "memory": memory,
                        "error": "Content validation failed - system/config content detected"
                    })
                    continue

                # Check for similar existing memory using batch results
                content_hash = get_content_hash(content)
                similar_memory = similar_memories_map.get(content_hash)
                
                # Fallback to individual check if batch didn't find it
                if similar_memory is None and content_hash not in similar_memories_map:
                    logger.debug(f"Individual check for memory: {content[:50]}...")
                    similar_memory = await self.caller_memory_manager.find_similar_memory(
                        caller_id=caller_id,
                        agent_id=agent_id,
                        content=content,
                        similarity_threshold=similarity_threshold,
                        content_hash=content_hash
                    )

                if similar_memory:
                    # Check for conflicts (same content but different category/importance)
                    similar_content = similar_memory.get("content", "")
                    similar_category = similar_memory.get("metadata", {}).get("category", "")
                    similar_importance = similar_memory.get("metadata", {}).get("importance", 0)
                    
                    is_conflict = (
                        similar_content.lower() == content.lower() and
                        (similar_category != category or abs(similar_importance - importance) > 2)
                    )
                    
                    if is_conflict:
                        # Store conflicting memory with conflict marker (with retry)
                        logger.warning(
                            f"Conflict detected for caller {caller_id}: "
                            f"existing={similar_category}/{similar_importance}, "
                            f"new={category}/{importance}"
                        )
                        memory_id = await self._store_memory_with_retry(
                            caller_id=caller_id,
                            agent_id=agent_id,
                            conversation_id=conversation_id,
                            content=content,
                            category=category,
                            sector=sector,
                            importance=importance,
                            entities=entities
                        )
                        if memory_id:
                            stored_memory_ids.append(memory_id)
                            logger.debug(f"Stored conflicting memory: {memory_id}")
                        else:
                            failed_memories.append({
                                "memory": memory,
                                "error": "Failed to store conflicting memory after retries"
                            })
                    else:
                        # Reinforce existing memory instead of creating duplicate (with retry)
                        memory_id = similar_memory.get("id") or similar_memory.get("memory_id")
                        if memory_id:
                            success = await self._reinforce_memory_with_retry(memory_id)
                            if success:
                                reinforced_memory_ids.append(memory_id)
                                logger.debug(f"Reinforced existing memory: {memory_id}")
                            else:
                                failed_memories.append({
                                    "memory": memory,
                                    "error": "Failed to reinforce memory after retries"
                                })
                else:
                    # Store new memory (with retry)
                    memory_id = await self._store_memory_with_retry(
                        caller_id=caller_id,
                        agent_id=agent_id,
                        conversation_id=conversation_id,
                        content=content,
                        category=category,
                        importance=importance,
                        entities=entities
                    )

                    if memory_id:
                        stored_memory_ids.append(memory_id)
                        logger.debug(f"Stored new memory: {memory_id}")
                    else:
                        failed_memories.append({
                            "memory": memory,
                            "error": "Failed to store memory after retries"
                        })

            except Exception as e:
                logger.error(f"Error processing memory for storage: {e}", exc_info=True)
                failed_memories.append({
                    "memory": memory,
                    "error": str(e)
                })
                continue

        result = {
            "stored": stored_memory_ids,
            "reinforced": reinforced_memory_ids,
            "failed": failed_memories,
            "stats": {
                "stored_count": len(stored_memory_ids),
                "reinforced_count": len(reinforced_memory_ids),
                "failed_count": len(failed_memories),
                "total_count": len(memories)
            }
        }
        
        logger.info(
            f"Memory storage complete for conversation {conversation_id}: "
            f"{result['stats']['stored_count']} stored, "
            f"{result['stats']['reinforced_count']} reinforced, "
            f"{result['stats']['failed_count']} failed"
        )
        
        return result
    
    async def _store_memory_with_retry(
        self,
        caller_id: str,
        agent_id: str,
        conversation_id: str,
        content: str,
        category: str,
        sector: str,
        importance: int,
        entities: List[str]
    ) -> Optional[str]:
        """
        Store a memory with retry logic and exponential backoff.
        
        Args:
            caller_id: Caller identifier
            agent_id: Agent identifier
            conversation_id: Conversation identifier
            content: Memory content
            category: Memory category
            importance: Importance score
            entities: List of entities
        
        Returns:
            Memory ID if successful, None otherwise
        """
        from config.settings import get_settings
        settings = get_settings()
        
        max_attempts = settings.memory_storage_retry_attempts
        initial_delay = settings.memory_storage_retry_delay_seconds
        
        for attempt in range(max_attempts):
            try:
                memory_id = await self.caller_memory_manager.store_caller_memory(
                    caller_id=caller_id,
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                    content=content,
                    category=category,
                    sector=sector,
                    importance=importance,
                    entities=entities
                )
                
                if memory_id:
                    if attempt > 0:
                        logger.info(
                            f"Successfully stored memory after {attempt + 1} attempts: {memory_id}"
                        )
                    return memory_id
                else:
                    # Store returned None, retry
                    if attempt < max_attempts - 1:
                        delay = initial_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Memory storage returned None (attempt {attempt + 1}/{max_attempts}), "
                            f"retrying in {delay}s"
                        )
                        await asyncio.sleep(delay)
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    delay = initial_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Error storing memory (attempt {attempt + 1}/{max_attempts}): {e}, "
                        f"retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Failed to store memory after {max_attempts} attempts: {e}",
                        exc_info=True
                    )
        
        return None
    
    async def _reinforce_memory_with_retry(self, memory_id: str) -> bool:
        """
        Reinforce a memory with retry logic and exponential backoff.
        
        Args:
            memory_id: Memory identifier to reinforce
        
        Returns:
            True if successful, False otherwise
        """
        from config.settings import get_settings
        settings = get_settings()
        
        max_attempts = settings.memory_storage_retry_attempts
        initial_delay = settings.memory_storage_retry_delay_seconds
        
        for attempt in range(max_attempts):
            try:
                success = await self.openmemory_client.reinforce_memory(memory_id)
                
                if success:
                    if attempt > 0:
                        logger.info(
                            f"Successfully reinforced memory after {attempt + 1} attempts: {memory_id}"
                        )
                    return True
                else:
                    # Reinforce returned False, retry
                    if attempt < max_attempts - 1:
                        delay = initial_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Memory reinforcement returned False (attempt {attempt + 1}/{max_attempts}), "
                            f"retrying in {delay}s"
                        )
                        await asyncio.sleep(delay)
                    
            except Exception as e:
                if attempt < max_attempts - 1:
                    delay = initial_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Error reinforcing memory (attempt {attempt + 1}/{max_attempts}): {e}, "
                        f"retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Failed to reinforce memory after {max_attempts} attempts: {e}",
                        exc_info=True
                    )
        
        return False
    
    def _validate_memory_content(self, content: str) -> bool:
        """
        Validate memory content to reject system prompts, config, and bad content.
        
        Args:
            content: Memory content to validate
            
        Returns:
            True if content is valid, False if it should be rejected
        """
        import re
        
        if not content or len(content.strip()) < 3:
            return False
        
        content_lower = content.lower()
        
        # Reject JSON/config patterns
        json_pattern = re.compile(r'\{[^{}]*"[^{}]*"[^{}]*\}', re.IGNORECASE)
        if json_pattern.search(content) and len(content) < 500:
            # Short JSON snippets are likely config
            return False
        
        # Reject system/config keywords in short messages
        system_keywords = [
            "max_", "min_", "timeout", "config", "setting", "api", "endpoint",
            "json", "yaml", "xml", "markdown", "code", "function",
            "tool_call", "rag_retrieval", "llm_usage", "metadata"
        ]
        
        if len(content) < 200:
            has_system_keywords = any(keyword in content_lower for keyword in system_keywords)
            config_pattern = re.compile(r'(max_|min_|timeout|config|setting)', re.IGNORECASE)
            if has_system_keywords and config_pattern.search(content):
                return False
        
        # Reject markdown table patterns
        if "|" in content and "---" in content and content.count("|") > 3:
            return False
        
        # Reject code-like patterns with multiple braces
        if content.count("{") > 2 and content.count("}") > 2 and len(content) < 300:
            return False
        
        # Reject content that looks like agent profile data
        if "agent_profile" in content_lower or "elevenlabs_api" in content_lower:
            if len(content) < 500:  # Short mentions might be OK, but longer ones are likely profile data
                return False
        
        return True
    
    async def _validate_stored_memories(
        self,
        caller_id: str,
        agent_id: str,
        conversation_id: str,
        expected_count: int,
        storage_result: Dict[str, Any]
    ) -> None:
        """
        Validate that stored memories exist in OpenMemory.
        
        Args:
            caller_id: Caller identifier
            agent_id: Agent identifier
            conversation_id: Conversation identifier
            expected_count: Expected number of memories extracted
            storage_result: Result from _store_memories_with_deduplication
        """
        try:
            from config.settings import get_settings
            settings = get_settings()
            
            logger.info(
                f"Validating stored memories for conversation {conversation_id}"
            )
            
            # Query OpenMemory for all memories from this conversation
            stored_memories = await self.openmemory_client.search_memories(
                user_id=caller_id,
                filter_dict={"metadata.conversation_id": conversation_id},
                limit=1000  # Large limit to get all memories
            )
            
            stored_count = len(stored_memories)
            expected_stored = storage_result["stats"]["stored_count"]
            expected_reinforced = storage_result["stats"]["reinforced_count"]
            
            # Count memories that match this conversation
            conversation_memories = [
                m for m in stored_memories
                if m.get("metadata", {}).get("conversation_id") == conversation_id
            ]
            conversation_count = len(conversation_memories)
            
            logger.info(
                f"Validation results for conversation {conversation_id}: "
                f"Found {conversation_count} memories in OpenMemory, "
                f"Expected {expected_stored} new + {expected_reinforced} reinforced"
            )
            
            # Check for discrepancies
            if conversation_count < expected_stored:
                discrepancy = expected_stored - conversation_count
                logger.warning(
                    f"Memory validation discrepancy for conversation {conversation_id}: "
                    f"{discrepancy} memories expected but not found in OpenMemory. "
                    f"This may indicate storage failures."
                )
            elif conversation_count >= expected_stored:
                logger.info(
                    f"Memory validation passed for conversation {conversation_id}: "
                    f"All expected memories found in OpenMemory"
                )
            
            # Log failed memories if any
            if storage_result["stats"]["failed_count"] > 0:
                logger.warning(
                    f"Memory storage had {storage_result['stats']['failed_count']} failures "
                    f"for conversation {conversation_id}. "
                    f"Failed memories: {[f.get('error', 'Unknown error') for f in storage_result['failed']]}"
                )
                
        except Exception as e:
            logger.error(
                f"Error validating stored memories for conversation {conversation_id}: {e}",
                exc_info=True
            )


# Global job processor instance
_job_processor = None


def get_job_processor() -> BackgroundJobProcessor:
    """Get or create the global job processor instance."""
    global _job_processor
    if _job_processor is None:
        _job_processor = BackgroundJobProcessor()
    return _job_processor


def start_background_worker():
    """Start the background job processor."""
    processor = get_job_processor()
    processor.start()


def stop_background_worker():
    """Stop the background job processor."""
    processor = get_job_processor()
    processor.stop()
