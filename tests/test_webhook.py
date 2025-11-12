"""
Test webhook script for ElevenLabs post-call webhooks.
Generates valid HMAC signatures and sends test payloads.
"""

import requests
import hmac
import json
import time
import base64
from hashlib import sha256
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path so we can import config module
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

settings = get_settings()


def generate_hmac_signature(payload_dict: dict, secret: str) -> tuple:
    """
    Generate valid HMAC-SHA256 signature for webhook testing.

    Returns:
        tuple: (timestamp, signature_header)
    """
    timestamp = int(time.time())
    payload_json = json.dumps(payload_dict)
    full_payload = f"{timestamp}.{payload_json}"

    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=full_payload.encode("utf-8"),
        digestmod=sha256,
    )
    signature = "v0=" + mac.hexdigest()
    signature_header = f"t={timestamp},{signature}"

    return timestamp, signature_header


def test_transcription_webhook(base_url: str = "http://localhost:8000"):
    """Test post_call_transcription webhook"""
    if not settings.elevenlabs_post_call_hmac_key:
        print("ERROR: ELEVENLABS_POST_CALL_HMAC_KEY not set in .env")
        return False

    # Create ElevenLabs-style webhook payload
    conversation_id = f"test_conv_transcription_{int(time.time())}"
    payload = {
        "type": "post_call_transcription",
        "data": {
            "conversation_id": conversation_id,
            "conversation_initiation_client_data": {
                "dynamic_variables": {
                    "system__caller_id": "+16129782029",
                    "system__agent_id": "agent_test_123"
                }
            },
            "transcript": [
                {
                    "role": "agent",
                    "agent_id": "agent_test_123",
                    "message": "Hello, how can I help you today?",
                    "source_medium": "phone"
                },
                {
                    "role": "user",
                    "message": "I need assistance with my account.",
                    "source_medium": "phone"
                },
                {
                    "role": "agent",
                    "agent_id": "agent_test_123",
                    "message": "I'd be happy to help. Let me look into that for you.",
                    "source_medium": "phone"
                }
            ],
            "status": "completed",
            "duration": 120
        }
    }

    timestamp, signature = generate_hmac_signature(payload, settings.elevenlabs_post_call_hmac_key)

    headers = {
        "Content-Type": "application/json",
        "elevenlabs-signature": signature
    }

    try:
        response = requests.post(
            f"{base_url}/webhook/post-call",
            json=payload,
            headers=headers
        )
        print(f"\n✓ Transcription Webhook Test")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"  Error: {response.text}")
            return False

    except Exception as e:
        print(f"\n✗ Transcription Webhook Test Failed")
        print(f"  Error: {str(e)}")
        return False


def test_audio_webhook(base_url: str = "http://localhost:8000"):
    """Test post_call_audio webhook with base64-encoded audio"""
    if not settings.elevenlabs_post_call_hmac_key:
        print("ERROR: ELEVENLABS_POST_CALL_HMAC_KEY not set in .env")
        return False

    # Create a small dummy MP3 content (not a real MP3, but valid base64)
    # In real use, this would be actual MP3 data
    dummy_audio = b"ID3\x04\x00\x00\x00\x00\x00\x00"  # MP3 header
    audio_base64 = base64.b64encode(dummy_audio).decode('utf-8')

    conversation_id = f"test_conv_audio_{int(time.time())}"
    payload = {
        "type": "post_call_audio",
        "data": {
            "conversation_id": conversation_id,
            "full_audio": audio_base64
        }
    }

    timestamp, signature = generate_hmac_signature(payload, settings.elevenlabs_post_call_hmac_key)

    headers = {
        "Content-Type": "application/json",
        "elevenlabs-signature": signature
    }

    try:
        response = requests.post(
            f"{base_url}/webhook/post-call",
            json=payload,
            headers=headers
        )
        print(f"\n✓ Audio Webhook Test")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"  Error: {response.text}")
            return False

    except Exception as e:
        print(f"\n✗ Audio Webhook Test Failed")
        print(f"  Error: {str(e)}")
        return False


def test_failure_webhook(base_url: str = "http://localhost:8000"):
    """Test call_initiation_failure webhook"""
    if not settings.elevenlabs_post_call_hmac_key:
        print("ERROR: ELEVENLABS_POST_CALL_HMAC_KEY not set in .env")
        return False

    conversation_id = f"test_conv_failure_{int(time.time())}"
    payload = {
        "type": "call_initiation_failure",
        "data": {
            "agent_id": "agent_test_123",
            "conversation_id": conversation_id,
            "failure_reason": "Connection timeout - test error",
            "metadata": {
                "type": "sip",
                "body": {
                    "sip_status_code": 408,
                    "error_reason": "Request Timeout"
                }
            }
        }
    }

    timestamp, signature = generate_hmac_signature(payload, settings.elevenlabs_post_call_hmac_key)

    headers = {
        "Content-Type": "application/json",
        "elevenlabs-signature": signature
    }

    try:
        response = requests.post(
            f"{base_url}/webhook/post-call",
            json=payload,
            headers=headers
        )
        print(f"\n✓ Failure Webhook Test")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"  Error: {response.text}")
            return False

    except Exception as e:
        print(f"\n✗ Failure Webhook Test Failed")
        print(f"  Error: {str(e)}")
        return False


def test_health_check(base_url: str = "http://localhost:8000"):
    """Test health check endpoint"""
    try:
        response = requests.get(f"{base_url}/health")
        print(f"\n✓ Health Check")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200

    except Exception as e:
        print(f"\n✗ Health Check Failed")
        print(f"  Error: {str(e)}")
        return False


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"Testing webhook service at: {base_url}")
    print(f"Using HMAC key: {settings.elevenlabs_post_call_hmac_key[:20]}..." if settings.elevenlabs_post_call_hmac_key else "No HMAC key configured")
    print("=" * 60)

    results = []
    results.append(("Health Check", test_health_check(base_url)))
    results.append(("Transcription Webhook", test_transcription_webhook(base_url)))
    results.append(("Audio Webhook", test_audio_webhook(base_url)))
    results.append(("Failure Webhook", test_failure_webhook(base_url)))

    print("\n" + "=" * 60)
    print("Test Summary:")
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")

    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)
