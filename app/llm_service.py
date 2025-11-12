"""
LLM service for memory extraction and personalization.
"""

import logging
import json
from typing import List, Dict, Any
from datetime import datetime
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """Service for LLM operations."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

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
            prompt = self._create_memory_extraction_prompt(
                transcript, agent_id, caller_id, conversation_id
            )

            # Call appropriate LLM provider
            if self.provider == "openai":
                memories = await self._extract_with_openai(prompt)
            elif self.provider == "anthropic":
                memories = await self._extract_with_anthropic(prompt)
            else:
                logger.error(f"Unsupported LLM provider: {self.provider}")
                return []

            logger.info(
                f"Extracted {len(memories)} memories from conversation {conversation_id}"
            )
            return memories

        except Exception as e:
            logger.error(f"Error extracting memories: {e}", exc_info=True)
            return []

    def _create_memory_extraction_prompt(
        self,
        transcript: List[Dict[str, str]],
        agent_id: str,
        caller_id: str,
        conversation_id: str
    ) -> str:
        """Create prompt for memory extraction."""

        # Format transcript
        transcript_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
            for msg in transcript
        ])

        timestamp = datetime.utcnow().isoformat()

        return f"""Extract memories from this AI agent conversation for future reference.

Conversation Details:
- Agent ID: {agent_id}
- Caller ID: {caller_id}
- Conversation ID: {conversation_id}
- Timestamp: {timestamp}

Full Transcript:
{transcript_text}

Extract memories in these categories:
1. FACTUAL: Names, IDs, numbers, dates, locations, transactions, objective facts
2. PREFERENCES: User preferences, likes/dislikes, communication style, scheduling preferences
3. ISSUES: Problems mentioned, complaints, unresolved issues, follow-up needed
4. EMOTIONAL: Customer sentiment (satisfied, frustrated, neutral), tone of interaction
5. RELATIONAL: People or entities mentioned, relationships between concepts

Return ONLY a JSON array (no markdown, no explanation):
[
  {{
    "content": "Clear, concise, atomic memory statement",
    "category": "factual|preference|issue|emotional|relational",
    "importance": 1-10,
    "entities": ["entity1", "entity2"]
  }}
]

Rules:
- Each memory should be ONE atomic fact
- Be specific and factual
- Importance: 10=critical (account numbers, VIP status), 1=minor detail
- Extract 5-20 memories per conversation
- If nothing memorable, return empty array []
"""

    async def _extract_with_openai(self, prompt: str) -> List[Dict[str, Any]]:
        """Extract memories using OpenAI API."""
        try:
            import openai

            openai.api_key = self.api_key

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"} if "gpt-4" in self.model else None
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
                messages=[{"role": "user", "content": prompt}]
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
            import openai

            openai.api_key = self.api_key

            response = await openai.ChatCompletion.acreate(
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
