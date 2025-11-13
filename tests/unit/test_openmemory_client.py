"""
Unit tests for OpenMemoryClient.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.openmemory_client import OpenMemoryClient


@pytest.fixture
def openmemory_client():
    """Create OpenMemoryClient instance for testing."""
    with patch('backend.app.openmemory_client.get_settings') as mock_settings:
        mock_settings.return_value.openmemory_api_url = "http://localhost:8080"
        mock_settings.return_value.openmemory_api_key = "test_key"
        client = OpenMemoryClient()
        return client


@pytest.mark.asyncio
async def test_store_memory_success(openmemory_client):
    """Test successful memory storage."""
    with patch.object(openmemory_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"memory_id": "mem_123"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        result = await openmemory_client.store_memory(
            user_id="user_123",
            content="Test memory",
            metadata={"agent_id": "agent_123"}
        )
        
        assert result == "mem_123"
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_search_memories_success(openmemory_client):
    """Test successful memory search."""
    with patch.object(openmemory_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"memories": [{"content": "test", "score": 0.9}]}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        results = await openmemory_client.search_memories(
            user_id="user_123",
            query="test query"
        )
        
        assert len(results) == 1
        assert results[0]["content"] == "test"


@pytest.mark.asyncio
async def test_reinforce_memory_success(openmemory_client):
    """Test successful memory reinforcement."""
    with patch.object(openmemory_client, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        result = await openmemory_client.reinforce_memory("mem_123")
        
        assert result is True
        mock_client.post.assert_called_once()

