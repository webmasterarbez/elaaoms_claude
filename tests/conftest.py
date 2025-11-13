"""
Pytest configuration and fixtures for ELAAOMS tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('backend.config.settings.get_settings') as mock_get:
        settings = Settings(
            app_name="ELAAOMS Test",
            app_version="0.1.0",
            debug=True,
            log_level="DEBUG",
            elevenlabs_post_call_hmac_key="a" * 32,  # 32 bytes minimum
            elevenlabs_api_key="test_key",
            openmemory_api_url="http://localhost:8080",
            openmemory_api_key="test_key",
            llm_provider="openai",
            llm_api_key="test_key",
            llm_model="gpt-4-turbo",
            llm_timeout_seconds=30
        )
        mock_get.return_value = settings
        yield settings

