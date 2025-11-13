"""
Security tests for API key masking in logs.
"""

import pytest
import logging
from backend.config.logging import APIKeyMaskingFilter


class TestAPIKeyMasking:
    """Test API key masking in log messages."""
    
    def test_openai_key_masking(self):
        """Test OpenAI API key masking."""
        filter_obj = APIKeyMaskingFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API key: sk-1234567890abcdef1234567890abcdef",
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        # Should be masked to 8 characters
        assert "sk-1234..." in record.msg
        assert "sk-1234567890abcdef1234567890abcdef" not in record.msg
    
    def test_elevenlabs_key_masking(self):
        """Test ElevenLabs API key masking."""
        filter_obj = APIKeyMaskingFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Key: elevenlabs_abc123xyz789def456ghi012jkl345",
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        # Should be masked
        assert "elevenl..." in record.msg
        assert "elevenlabs_abc123xyz789def456ghi012jkl345" not in record.msg
    
    def test_generic_long_key_masking(self):
        """Test generic long key masking."""
        filter_obj = APIKeyMaskingFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Token: abcdefghijklmnopqrstuvwxyz1234567890ABCDEF",
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        # Should be masked to 8 characters
        assert "abcdefg..." in record.msg

