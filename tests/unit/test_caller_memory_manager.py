"""
Unit tests for CallerMemoryManager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.openmemory_client import CallerMemoryManager, OpenMemoryClient


@pytest.fixture
def caller_memory_manager():
    """Create CallerMemoryManager instance for testing."""
    mock_client = MagicMock(spec=OpenMemoryClient)
    manager = CallerMemoryManager(mock_client)
    return manager


@pytest.mark.asyncio
async def test_store_caller_memory(caller_memory_manager):
    """Test storing caller memory."""
    caller_memory_manager.client.store_memory = AsyncMock(return_value="mem_123")
    
    result = await caller_memory_manager.store_caller_memory(
        caller_id="+15551234567",
        agent_id="agent_123",
        conversation_id="conv_123",
        content="Test memory",
        category="factual",
        importance=7,
        entities=["test"]
    )
    
    assert result == "mem_123"
    caller_memory_manager.client.store_memory.assert_called_once()


@pytest.mark.asyncio
async def test_find_similar_memory(caller_memory_manager):
    """Test finding similar memory."""
    similar_memory = {
        "id": "mem_123",
        "content": "Similar content",
        "score": 0.9
    }
    caller_memory_manager.client.search_memories = AsyncMock(
        return_value=[similar_memory]
    )
    
    result = await caller_memory_manager.find_similar_memory(
        caller_id="+15551234567",
        agent_id="agent_123",
        content="Similar content",
        similarity_threshold=0.85
    )
    
    assert result == similar_memory


@pytest.mark.asyncio
async def test_get_last_conversation_memories(caller_memory_manager):
    """Test getting last conversation memories."""
    memories = [
        {
            "metadata": {
                "conversation_id": "conv_1",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        },
        {
            "metadata": {
                "conversation_id": "conv_2",
                "timestamp": "2024-01-02T00:00:00Z"
            }
        }
    ]
    caller_memory_manager.client.search_memories = AsyncMock(return_value=memories)
    
    result = await caller_memory_manager.get_last_conversation_memories(
        caller_id="+15551234567",
        agent_id="agent_123"
    )
    
    assert len(result) > 0


def test_format_context_json(caller_memory_manager):
    """Test formatting context as JSON."""
    memories = [
        {
            "content": "Factual memory",
            "metadata": {"category": "factual"}
        },
        {
            "content": "Preference memory",
            "metadata": {"category": "preference"}
        }
    ]
    
    context = caller_memory_manager.format_context_json(memories)
    
    assert "memories" in context
    assert "preferences" in context
    assert "relationship_insights" in context
    assert len(context["memories"]["factual"]) > 0


def test_create_memory_summary(caller_memory_manager):
    """Test creating memory summary."""
    memories = [
        {"content": "First memory"},
        {"content": "Second memory"},
        {"content": "Third memory"}
    ]
    
    summary = caller_memory_manager.create_memory_summary(memories)
    
    assert "First memory" in summary
    assert "Second memory" in summary
    assert isinstance(summary, str)

