"""
ElevenLabs webhook HMAC authentication module
"""

import hmac
import time
import logging
import secrets
from hashlib import sha256
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def verify_elevenlabs_webhook(
    request_body: bytes,
    signature_header: str,
    secret: str,
    tolerance_seconds: int = 30 * 60
) -> bool:
    """
    Verify ElevenLabs webhook HMAC signature.

    Args:
        request_body: Raw request body bytes
        signature_header: Value of elevenlabs-signature header
        secret: HMAC secret key
        tolerance_seconds: Maximum age of request (default 30 minutes)

    Returns:
        True if signature is valid, raises HTTPException if invalid

    Raises:
        HTTPException: 401 if signature is invalid or timestamp is too old

    Header format: t=timestamp,v0=hash
    """

    if not signature_header:
        logger.warning("Missing elevenlabs-signature header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing elevenlabs-signature header"
        )

    try:
        # Parse signature header
        parts = signature_header.split(",")
        if len(parts) != 2:
            logger.warning(f"Invalid signature header format: {signature_header}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature header format"
            )

        timestamp_part = parts[0]  # t=timestamp
        hash_part = parts[1]  # v0=hash

        if not timestamp_part.startswith("t="):
            logger.warning(f"Invalid timestamp format in header: {timestamp_part}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid timestamp format"
            )

        if not hash_part.startswith("v0="):
            logger.warning(f"Invalid hash format in header: {hash_part}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid hash format"
            )

        # Extract timestamp and hash
        timestamp_str = timestamp_part[2:]  # Remove "t="
        provided_hash = hash_part[3:].strip()  # Remove "v0=" and whitespace

        try:
            timestamp = int(timestamp_str)
        except ValueError:
            logger.warning(f"Invalid timestamp value: {timestamp_str}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid timestamp value"
            )

        # Validate timestamp (check if within tolerance)
        current_time = int(time.time())
        # Timestamp should be within the last 30 minutes (not too old)
        # Equivalent to: timestamp >= (current_time - tolerance_seconds)
        if timestamp < (current_time - tolerance_seconds):
            logger.warning(
                f"Timestamp too old: current={current_time}, provided={timestamp}, "
                f"difference={current_time - timestamp}s, tolerance={tolerance_seconds}s"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request timestamp too old"
            )

        # Validate HMAC signature
        full_payload_to_sign = f"{timestamp}.{request_body.decode('utf-8')}"
        
        # Debug logging (remove in production)
        logger.debug(f"Payload to sign: {full_payload_to_sign[:100]}...")
        logger.debug(f"Secret length: {len(secret)} bytes")
        logger.debug(f"Provided hash: {provided_hash[:20]}...")
        
        mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=full_payload_to_sign.encode("utf-8"),
            digestmod=sha256,
        )
        calculated_hash = mac.hexdigest()
        
        logger.debug(f"Calculated hash: {calculated_hash[:20]}...")

        # Use constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(calculated_hash, provided_hash):
            logger.warning(
                f"HMAC signature mismatch. "
                f"Expected: {calculated_hash}, Provided: {provided_hash}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        logger.info("Webhook signature validated successfully")
        return True

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating webhook signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature validation failed"
        )
