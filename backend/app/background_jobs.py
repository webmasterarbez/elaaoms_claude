"""
Background job processor for memory extraction.
"""

import logging
import asyncio
from queue import Queue, Empty
from threading import Thread
from typing import Dict, Any, List
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

                # Step 3: Store memories with deduplication
                logger.info(
                    f"Storing {len(extracted_memories)} memories "
                    f"for conversation {job.conversation_id}"
                )
                stored_count, reinforced_count = await self._store_memories_with_deduplication(
                    caller_id=job.caller_id,
                    agent_id=job.agent_id,
                    conversation_id=job.conversation_id,
                    memories=extracted_memories
                )

                logger.info(
                    f"Memory extraction complete for conversation {job.conversation_id}: "
                    f"{stored_count} new memories stored, {reinforced_count} existing reinforced"
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
    ) -> tuple[int, int]:
        """
        Store memories with deduplication logic.

        Returns:
            Tuple of (stored_count, reinforced_count)
        """
        stored_count = 0
        reinforced_count = 0

        for memory in memories:
            try:
                content = memory.get("content", "")
                category = memory.get("category", "factual")
                importance = memory.get("importance", 5)
                entities = memory.get("entities", [])

                if not content:
                    logger.warning("Skipping memory with empty content")
                    continue

                # Check for similar existing memory
                from config.settings import get_settings
                similarity_threshold = get_settings().memory_similarity_threshold
                
                similar_memory = await self.caller_memory_manager.find_similar_memory(
                    caller_id=caller_id,
                    agent_id=agent_id,
                    content=content,
                    similarity_threshold=similarity_threshold
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
                        # Store conflicting memory with conflict marker
                        logger.warning(
                            f"Conflict detected for caller {caller_id}: "
                            f"existing={similar_category}/{similar_importance}, "
                            f"new={category}/{importance}"
                        )
                        memory_id = await self.caller_memory_manager.store_caller_memory(
                            caller_id=caller_id,
                            agent_id=agent_id,
                            conversation_id=conversation_id,
                            content=content,
                            category=category,
                            importance=importance,
                            entities=entities
                        )
                        # Mark as conflict in metadata
                        if memory_id:
                            stored_count += 1
                            logger.debug(f"Stored conflicting memory: {memory_id}")
                    else:
                        # Reinforce existing memory instead of creating duplicate
                        memory_id = similar_memory.get("id") or similar_memory.get("memory_id")
                        if memory_id:
                            await self.openmemory_client.reinforce_memory(memory_id)
                            reinforced_count += 1
                            logger.debug(f"Reinforced existing memory: {memory_id}")
                else:
                    # Store new memory
                    memory_id = await self.caller_memory_manager.store_caller_memory(
                        caller_id=caller_id,
                        agent_id=agent_id,
                        conversation_id=conversation_id,
                        content=content,
                        category=category,
                        importance=importance,
                        entities=entities
                    )

                    if memory_id:
                        stored_count += 1
                        logger.debug(f"Stored new memory: {memory_id}")

            except Exception as e:
                logger.error(f"Error storing memory: {e}", exc_info=True)
                continue

        return stored_count, reinforced_count


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
