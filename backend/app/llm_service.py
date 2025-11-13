"""
LLM service for memory extraction and personalization.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """Service for LLM operations."""

    def __init__(self, organization_id: Optional[str] = None):
        """
        Initialize LLM service.
        
        Args:
            organization_id: Optional organization ID for per-organization provider selection
        """
        # For now, use global setting (per-organization config can be added later)
        self.provider = settings.llm_provider
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout_seconds
        self.organization_id = organization_id

    async def extract_memories(
        self,
        transcript: List[Dict[str, str]],
        agent_id: str,
        caller_id: str,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract memories from conversation transcript using LLM.

        Args:
            transcript: List of message objects with role and message
            agent_id: Agent identifier
            caller_id: Caller identifier
            conversation_id: Conversation identifier

        Returns:
            List of extracted memory objects
        """
        try:
            # Chunk long conversations (>10K tokens)
            chunks = self._chunk_transcript(transcript, max_tokens=10000)
            
            all_memories = []
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                logger.info(
                    f"Processing chunk {i+1}/{len(chunks)} for conversation {conversation_id}"
                )
                
                # Check if we need json_object format (for GPT-4 models)
                use_json_object = "gpt-4" in self.model.lower()
                
                prompt = self._create_memory_extraction_prompt(
                    chunk, agent_id, caller_id, conversation_id, use_json_object=use_json_object
                )

                # Select provider (with fallback support)
                selected_provider = self._select_provider()
                
                # Try primary provider with fallback
                chunk_memories = await self._extract_with_fallback(prompt, selected_provider)
                
                # Validate response
                validated_chunk_memories = self._validate_memory_response(chunk_memories)
                
                # Apply privacy filters
                from .privacy import get_privacy_filter
                privacy_filter = get_privacy_filter()
                
                filtered_memories = []
                for memory in validated_chunk_memories:
                    if privacy_filter.should_redact_memory(memory):
                        # Redact sensitive information
                        content = memory.get("content", "")
                        memory["content"] = privacy_filter.filter_sensitive_info(content)
                        memory["metadata"] = memory.get("metadata", {})
                        memory["metadata"]["privacy_filtered"] = True
                        logger.info("Applied privacy filter to memory")
                    filtered_memories.append(memory)
                
                all_memories.extend(filtered_memories)
            
            logger.info(
                f"Extracted {len(all_memories)} validated memories from conversation {conversation_id} "
                f"({len(chunks)} chunks)"
            )
            return all_memories

        except Exception as e:
            logger.error(f"Error extracting memories: {e}", exc_info=True)
            return []
    
    def _select_provider(self) -> str:
        """
        Select LLM provider based on configuration.
        
        Returns:
            Provider name (openai or anthropic)
        """
        if self.provider == "auto":
            # Auto-select: prefer OpenAI if available, fallback to Anthropic
            # For now, default to OpenAI (can be enhanced with availability checks)
            logger.info("Auto provider selection: using OpenAI")
            return "openai"
        elif self.provider in ["openai", "anthropic"]:
            return self.provider
        else:
            logger.warning(f"Unknown provider {self.provider}, defaulting to OpenAI")
            return "openai"
    
    async def _extract_with_fallback(
        self,
        prompt: str,
        primary_provider: str
    ) -> List[Dict[str, Any]]:
        """
        Extract memories with automatic fallback to alternative provider on failure.
        
        Args:
            prompt: Extraction prompt
            primary_provider: Primary provider to try first
        
        Returns:
            List of extracted memories
        """
        # Determine fallback provider
        fallback_provider = "anthropic" if primary_provider == "openai" else "openai"
        
        # Try primary provider
        try:
            if primary_provider == "openai":
                memories = await self._extract_with_openai(prompt)
            else:
                memories = await self._extract_with_anthropic(prompt)
            
            if memories:
                logger.info(f"Successfully extracted memories using {primary_provider}")
                return memories
        except Exception as e:
            logger.warning(
                f"Primary provider {primary_provider} failed: {e}. "
                f"Falling back to {fallback_provider}"
            )
        
        # Try fallback provider
        try:
            if fallback_provider == "openai":
                memories = await self._extract_with_openai(prompt)
            else:
                memories = await self._extract_with_anthropic(prompt)
            
            if memories:
                logger.info(f"Successfully extracted memories using fallback {fallback_provider}")
                return memories
        except Exception as e:
            logger.error(f"Fallback provider {fallback_provider} also failed: {e}")
        
        return []
    
    def _validate_memory_response(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate memory response using Pydantic models.
        
        Args:
            memories: Raw memory list from LLM
        
        Returns:
            Validated memory list
        """
        from pydantic import ValidationError
        
        validated = []
        valid_categories = ["factual", "preference", "issue", "emotional", "relational"]
        
        for memory in memories:
            try:
                # Validate required fields
                if not isinstance(memory, dict):
                    logger.warning(f"Invalid memory format (not dict): {memory}")
                    continue
                
                content = memory.get("content", "")
                category = memory.get("category", "factual")
                importance = memory.get("importance", 5)
                entities = memory.get("entities", [])
                
                # Validate content
                if not content or not isinstance(content, str):
                    logger.warning(f"Invalid memory content: {content}")
                    continue
                
                # Validate category
                if category not in valid_categories:
                    logger.warning(f"Invalid category {category}, defaulting to factual")
                    category = "factual"
                
                # Validate importance (1-10)
                if not isinstance(importance, int) or importance < 1 or importance > 10:
                    logger.warning(f"Invalid importance {importance}, defaulting to 5")
                    importance = 5
                
                # Validate entities
                if not isinstance(entities, list):
                    entities = []
                
                validated.append({
                    "content": content,
                    "category": category,
                    "importance": importance,
                    "entities": entities
                })
                
            except Exception as e:
                logger.warning(f"Error validating memory: {e}, skipping")
                continue
        
        return validated

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters).
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def _chunk_transcript(
        self,
        transcript: List[Dict[str, str]],
        max_tokens: int = 10000
    ) -> List[List[Dict[str, str]]]:
        """
        Chunk long conversations for memory extraction.
        
        Args:
            transcript: Full transcript
            max_tokens: Maximum tokens per chunk
        
        Returns:
            List of transcript chunks
        """
        if not transcript:
            return []
        
        # Estimate total tokens
        full_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
            for msg in transcript
        ])
        total_tokens = self._estimate_tokens(full_text)
        
        # If under limit, return as single chunk
        if total_tokens <= max_tokens:
            return [transcript]
        
        # Split into chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for msg in transcript:
            msg_text = f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
            msg_tokens = self._estimate_tokens(msg_text)
            
            if current_tokens + msg_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [msg]
                current_tokens = msg_tokens
            else:
                current_chunk.append(msg)
                current_tokens += msg_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Split transcript into {len(chunks)} chunks (total tokens: {total_tokens})")
        return chunks

    def _create_memory_extraction_prompt(
        self,
        transcript: List[Dict[str, str]],
        agent_id: str,
        caller_id: str,
        conversation_id: str,
        use_json_object: bool = False
    ) -> str:
        """Create prompt for memory extraction."""

        # Format transcript
        transcript_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
            for msg in transcript
        ])

        timestamp = datetime.now(timezone.utc).isoformat()

        # Format response based on whether we're using json_object format
        if use_json_object:
            response_format = """Return ONLY a JSON object (no markdown, no explanation):
{{
  "memories": [
    {{
      "content": "Clear, concise, atomic memory statement",
      "category": "factual|preference|issue|emotional|relational",
      "importance": 1-10,
      "entities": ["entity1", "entity2"]
    }}
  ]
}}"""
        else:
            response_format = """Return ONLY a JSON array (no markdown, no explanation):
[
  {{
    "content": "Clear, concise, atomic memory statement",
    "category": "factual|preference|issue|emotional|relational",
    "importance": 1-10,
    "entities": ["entity1", "entity2"]
  }}
]"""

        return f"""Extract memories from this AI agent conversation for future reference.

Conversation Details:
- Agent ID: {agent_id}
- Caller ID: {caller_id}
- Conversation ID: {conversation_id}
- Timestamp: {timestamp}

Full Transcript:
{transcript_text}

Extract memories in these categories:
1. FACTUAL: Names (FIRST AND LAST names separately), IDs, numbers, dates, locations, transactions, objective facts
2. PREFERENCES: User preferences, likes/dislikes, communication style, scheduling preferences
3. ISSUES: Problems mentioned, complaints, unresolved issues, follow-up needed
4. EMOTIONAL: Customer sentiment (satisfied, frustrated, neutral), tone of interaction
5. RELATIONAL: People or entities mentioned, relationships between concepts

{response_format}

Rules:
- Each memory should be ONE atomic fact
- Be specific and factual
- IMPORTANT: Extract BOTH first name AND last name as SEPARATE memories if both are mentioned
- Names are high importance (8-9): Extract "Caller's first name is [name]" and "Caller's last name is [name]" separately
- If a name is spelled out (e.g., "3-B-R-E-E-T"), extract it as the actual name (e.g., "Breet")
- Importance: 10=critical (account numbers, VIP status), 8-9=names, 1=minor detail
- Extract 5-20 memories per conversation
- If nothing memorable, return empty array [] or {{"memories": []}}
"""

    async def _extract_with_openai(self, prompt: str) -> List[Dict[str, Any]]:
        """Extract memories using OpenAI API."""
        try:
            from openai import AsyncOpenAI
            import httpx

            client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=httpx.Timeout(self.timeout, connect=10.0)
            )

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"} if "gpt-4" in self.model else None,
                timeout=self.timeout
            )

            content = response.choices[0].message.content.strip()

            # Try to parse JSON
            try:
                # Handle markdown code blocks
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()

                # Parse JSON
                result = json.loads(content)

                # Handle different response formats
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    # Check for common wrapper keys
                    for key in ["memories", "results", "data"]:
                        if key in result and isinstance(result[key], list):
                            return result[key]
                    return [result]
                else:
                    logger.error(f"Unexpected result type: {type(result)}")
                    return []

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}\nContent: {content}")
                return []

        except Exception as e:
            logger.error(f"Error with OpenAI API: {e}", exc_info=True)
            return []

    async def _extract_with_anthropic(self, prompt: str) -> List[Dict[str, Any]]:
        """Extract memories using Anthropic API."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            response = await client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout
            )

            content = response.content[0].text.strip()

            # Parse JSON response
            try:
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()

                result = json.loads(content)

                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    for key in ["memories", "results", "data"]:
                        if key in result and isinstance(result[key], list):
                            return result[key]
                    return [result]
                else:
                    return []

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return []

        except Exception as e:
            logger.error(f"Error with Anthropic API: {e}", exc_info=True)
            return []

    async def generate_personalized_first_message(
        self,
        agent_profile: Dict[str, Any],
        last_conv_memories: List[Dict[str, Any]],
        cross_agent_memories: List[Dict[str, Any]]
    ) -> str:
        """
        Generate personalized first message for returning caller.

        Args:
            agent_profile: Agent profile from ElevenLabs
            last_conv_memories: Memories from last conversation
            cross_agent_memories: High-importance memories from other agents

        Returns:
            Personalized first message
        """
        try:
            # If no previous memories, use default
            if not last_conv_memories:
                default_msg = agent_profile.get("first_message", "Hello! How can I help you today?")
                logger.info("No previous memories, using default first message")
                return default_msg

            prompt = self._create_first_message_prompt(
                agent_profile, last_conv_memories, cross_agent_memories
            )

            # Call LLM
            if self.provider == "openai":
                first_message = await self._generate_with_openai(prompt)
            elif self.provider == "anthropic":
                first_message = await self._generate_with_anthropic(prompt)
            else:
                logger.error(f"Unsupported LLM provider: {self.provider}")
                return agent_profile.get("first_message", "Hello!")

            logger.info("Generated personalized first message")
            return first_message

        except Exception as e:
            logger.error(f"Error generating first message: {e}", exc_info=True)
            return agent_profile.get("first_message", "Hello! How can I help you today?")

    def _create_first_message_prompt(
        self,
        agent_profile: Dict[str, Any],
        last_conv_memories: List[Dict[str, Any]],
        cross_agent_memories: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for first message personalization."""

        # Format last conversation memories
        last_conv_text = "\n".join([
            f"- {m.get('content', '')}"
            for m in last_conv_memories
        ]) if last_conv_memories else "None"

        # Format cross-agent memories
        cross_agent_text = "\n".join([
            f"- {m.get('content', '')} (importance: {m.get('metadata', {}).get('importance', 0)})"
            for m in cross_agent_memories
        ]) if cross_agent_memories else "None"

        agent_name = agent_profile.get("name", "AI Assistant")
        default_first_message = agent_profile.get("first_message", "Hello!")
        system_prompt = agent_profile.get("system_prompt", "")[:200]

        return f"""Personalize the first message for an AI agent calling back a customer.

Agent Info:
- Name: {agent_name}
- Default First Message: {default_first_message}
- System Prompt Summary: {system_prompt}...

Caller's Last Conversation:
{last_conv_text}

High-Priority Context from Other Interactions:
{cross_agent_text}

Task: Generate a warm, personalized first message (20-40 words) that:
1. Naturally acknowledges previous interactions
2. References relevant context without overwhelming the caller
3. Maintains the agent's tone and purpose
4. Feels conversational and human, not robotic

Return ONLY the first message text (no JSON, no explanation).
"""

    async def _generate_with_openai(self, prompt: str) -> str:
        """Generate first message using OpenAI."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error with OpenAI API: {e}", exc_info=True)
            return ""

    async def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate first message using Anthropic."""
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            response = await client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Error with Anthropic API: {e}", exc_info=True)
            return ""
