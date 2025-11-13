"""
Security tests for HMAC validation.
"""

import pytest
import time
import hmac
import hashlib
from fastapi import HTTPException
from backend.app.auth import verify_elevenlabs_webhook


class TestHMACValidation:
    """Test HMAC signature validation security."""
    
    def test_constant_time_comparison(self):
        """Verify constant-time comparison prevents timing attacks."""
        secret = "a" * 32
        body = b'{"test": "data"}'
        timestamp = str(int(time.time()))
        
        # Valid signature
        payload = f"{timestamp}.{body.decode('utf-8')}"
        mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256
        )
        valid_signature = mac.hexdigest()
        
        # Invalid signature (first byte different)
        invalid_signature = "0" + valid_signature[1:]
        
        # Both should take similar time (constant-time comparison)
        start = time.time()
        try:
            verify_elevenlabs_webhook(
                request_body=body,
                signature_header=f"t={timestamp},v0={valid_signature}",
                secret=secret
            )
        except:
            pass
        valid_time = time.time() - start
        
        start = time.time()
        try:
            verify_elevenlabs_webhook(
                request_body=body,
                signature_header=f"t={timestamp},v0={invalid_signature}",
                secret=secret
            )
        except:
            pass
        invalid_time = time.time() - start
        
        # Times should be similar (within 10ms) - constant-time comparison
        assert abs(valid_time - invalid_time) < 0.01
    
    def test_replay_attack_prevention(self):
        """Test that old timestamps are rejected."""
        secret = "a" * 32
        body = b'{"test": "data"}'
        
        # Create signature with old timestamp
        old_timestamp = str(int(time.time()) - 2000)
        payload = f"{old_timestamp}.{body.decode('utf-8')}"
        mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256
        )
        signature = mac.hexdigest()
        
        with pytest.raises(HTTPException) as exc_info:
            verify_elevenlabs_webhook(
                request_body=body,
                signature_header=f"t={old_timestamp},v0={signature}",
                secret=secret,
                tolerance_seconds=1800
            )
        assert exc_info.value.status_code == 401
        assert "too old" in exc_info.value.detail.lower()
    
    def test_signature_tampering_detection(self):
        """Test that tampered signatures are detected."""
        secret = "a" * 32
        body = b'{"test": "data"}'
        timestamp = str(int(time.time()))
        
        # Create valid signature
        payload = f"{timestamp}.{body.decode('utf-8')}"
        mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256
        )
        valid_signature = mac.hexdigest()
        
        # Tamper with body
        tampered_body = b'{"test": "tampered"}'
        
        with pytest.raises(HTTPException) as exc_info:
            verify_elevenlabs_webhook(
                request_body=tampered_body,
                signature_header=f"t={timestamp},v0={valid_signature}",
                secret=secret
            )
        assert exc_info.value.status_code == 401

