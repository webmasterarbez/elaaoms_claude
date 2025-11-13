"""
Unit tests for LLMService.
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.app.llm_service import LLMService


@pytest.fixture
def llm_service():
    """Create LLMService instance for testing."""
    with patch('backend.app.llm_service.get_settings') as mock_settings:
        mock_settings.return_value.llm_provider = "openai"
        mock_settings.return_value.llm_api_key = "test_key"
        mock_settings.return_value.llm_model = "gpt-4-turbo"
        mock_settings.return_value.llm_timeout_seconds = 30
        service = LLMService()
        return service


def test_estimate_tokens(llm_service):
    """Test token estimation."""
    text = "This is a test" * 100  # 1400 characters
    tokens = llm_service._estimate_tokens(text)
    assert tokens == 350  # 1400 / 4


def test_chunk_transcript_short(llm_service):
    """Test chunking short transcript."""
    transcript = [{"role": "user", "message": "Hello"}]
    chunks = llm_service._chunk_transcript(transcript, max_tokens=10000)
    assert len(chunks) == 1
    assert chunks[0] == transcript


def test_chunk_transcript_long(llm_service):
    """Test chunking long transcript."""
    # Create a long transcript
    transcript = [{"role": "user", "message": "A" * 5000}] * 10
    chunks = llm_service._chunk_transcript(transcript, max_tokens=10000)
    assert len(chunks) > 1


def test_validate_memory_response_valid(llm_service):
    """Test validation of valid memory response."""
    memories = [
        {
            "content": "Customer prefers email",
            "category": "preference",
            "importance": 7,
            "entities": ["email"]
        }
    ]
    validated = llm_service._validate_memory_response(memories)
    assert len(validated) == 1
    assert validated[0]["category"] == "preference"


def test_validate_memory_response_invalid_category(llm_service):
    """Test validation with invalid category."""
    memories = [
        {
            "content": "Test",
            "category": "invalid",
            "importance": 5,
            "entities": []
        }
    ]
    validated = llm_service._validate_memory_response(memories)
    assert len(validated) == 1
    assert validated[0]["category"] == "factual"  # Defaulted


def test_validate_memory_response_invalid_importance(llm_service):
    """Test validation with invalid importance."""
    memories = [
        {
            "content": "Test",
            "category": "factual",
            "importance": 15,  # Invalid (>10)
            "entities": []
        }
    ]
    validated = llm_service._validate_memory_response(memories)
    assert len(validated) == 1
    assert validated[0]["importance"] == 5  # Defaulted

