"""
Unit tests for authentication and HMAC validation.
"""

import pytest
import hmac
import time
import hashlib
from fastapi import HTTPException
from backend.app.auth import verify_elevenlabs_webhook


def test_verify_webhook_valid_signature():
    """Test valid HMAC signature verification."""
    secret = "a" * 32  # 32 bytes minimum
    body = b'{"test": "data"}'
    timestamp = str(int(time.time()))
    
    # Create valid signature
    payload = f"{timestamp}.{body.decode('utf-8')}"
    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256
    )
    signature = mac.hexdigest()
    signature_header = f"t={timestamp},v0={signature}"
    
    # Should not raise
    result = verify_elevenlabs_webhook(
        request_body=body,
        signature_header=signature_header,
        secret=secret
    )
    assert result is True


def test_verify_webhook_missing_header():
    """Test missing signature header."""
    with pytest.raises(HTTPException) as exc_info:
        verify_elevenlabs_webhook(
            request_body=b"test",
            signature_header=None,
            secret="test_secret"
        )
    assert exc_info.value.status_code == 401


def test_verify_webhook_invalid_signature():
    """Test invalid HMAC signature."""
    secret = "a" * 32
    body = b'{"test": "data"}'
    timestamp = str(int(time.time()))
    signature_header = f"t={timestamp},v0=invalid_hash"
    
    with pytest.raises(HTTPException) as exc_info:
        verify_elevenlabs_webhook(
            request_body=body,
            signature_header=signature_header,
            secret=secret
        )
    assert exc_info.value.status_code == 401


def test_verify_webhook_old_timestamp():
    """Test old timestamp rejection."""
    secret = "a" * 32
    body = b'{"test": "data"}'
    old_timestamp = str(int(time.time()) - 2000)  # 2000 seconds ago
    
    payload = f"{old_timestamp}.{body.decode('utf-8')}"
    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256
    )
    signature = mac.hexdigest()
    signature_header = f"t={old_timestamp},v0={signature}"
    
    with pytest.raises(HTTPException) as exc_info:
        verify_elevenlabs_webhook(
            request_body=body,
            signature_header=signature_header,
            secret=secret,
            tolerance_seconds=1800  # 30 minutes
        )
    assert exc_info.value.status_code == 401

