#!/usr/bin/env python3
"""
HMAC Signature Generator for Testing ElevenLabs Webhooks

This utility generates valid HMAC-SHA256 signatures for testing webhook endpoints
that require ElevenLabs-style HMAC authentication.

Usage:
    python utility/generate_hmac.py <payload_file.json>
    python utility/generate_hmac.py --payload '{"key": "value"}'
    python utility/generate_hmac.py --help

The script will output:
    - The elevenlabs-signature header value
    - A complete curl command ready to use
"""

import argparse
import hmac
import json
import sys
import time
from hashlib import sha256
from pathlib import Path


def generate_hmac_signature(payload: str, secret: str, timestamp: int = None) -> str:
    """
    Generate HMAC-SHA256 signature for ElevenLabs webhooks.

    Args:
        payload: JSON payload as string
        secret: HMAC secret key
        timestamp: Unix timestamp (defaults to current time)

    Returns:
        elevenlabs-signature header value (format: t=timestamp,v0=hash)
    """
    if timestamp is None:
        timestamp = int(time.time())

    # Create the payload to sign: timestamp.payload
    full_payload_to_sign = f"{timestamp}.{payload}"

    # Generate HMAC-SHA256 hash
    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=full_payload_to_sign.encode("utf-8"),
        digestmod=sha256,
    )
    calculated_hash = mac.hexdigest()

    # Return in ElevenLabs format
    return f"t={timestamp},v0={calculated_hash}"


def generate_curl_command(
    url: str,
    payload: str,
    signature: str,
    endpoint: str = "/webhook/post-call"
) -> str:
    """Generate a complete curl command."""
    # Escape payload for shell
    payload_escaped = payload.replace('"', '\\"')

    curl_cmd = f"""curl -X POST {url}{endpoint} \\
  -H "Content-Type: application/json" \\
  -H "elevenlabs-signature: {signature}" \\
  -d '{payload}'"""

    return curl_cmd


def main():
    parser = argparse.ArgumentParser(
        description="Generate HMAC-SHA256 signatures for ElevenLabs webhooks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate signature for a JSON file
  python utility/generate_hmac.py payload.json

  # Generate signature from inline JSON
  python utility/generate_hmac.py --payload '{"type":"post_call_transcription","data":{}}'

  # Use custom secret and URL
  python utility/generate_hmac.py payload.json --secret my_secret --url http://localhost:8000

  # Generate with specific timestamp (for testing)
  python utility/generate_hmac.py payload.json --timestamp 1234567890
        """
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="JSON payload file path"
    )

    parser.add_argument(
        "-p", "--payload",
        help="JSON payload as string (alternative to file)"
    )

    parser.add_argument(
        "-s", "--secret",
        default="your_hmac_secret_key",
        help="HMAC secret key (default: your_hmac_secret_key)"
    )

    parser.add_argument(
        "-t", "--timestamp",
        type=int,
        help="Unix timestamp (default: current time)"
    )

    parser.add_argument(
        "-u", "--url",
        default="http://localhost:8000",
        help="Base URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "-e", "--endpoint",
        default="/webhook/post-call",
        help="Endpoint path (default: /webhook/post-call)"
    )

    parser.add_argument(
        "--no-curl",
        action="store_true",
        help="Don't generate curl command, only show signature"
    )

    args = parser.parse_args()

    # Get payload
    if args.payload:
        payload_str = args.payload
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        with open(file_path, 'r') as f:
            payload_str = f.read().strip()
    else:
        print("Error: Must provide either a file or --payload argument", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Validate JSON
    try:
        payload_dict = json.loads(payload_str)
        # Re-serialize to ensure consistent formatting
        payload_str = json.dumps(payload_dict, separators=(',', ':'))
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON payload: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate signature
    signature = generate_hmac_signature(
        payload=payload_str,
        secret=args.secret,
        timestamp=args.timestamp
    )

    # Output results
    print("=" * 70)
    print("HMAC-SHA256 Signature Generated")
    print("=" * 70)
    print()
    print(f"Payload: {payload_str[:80]}{'...' if len(payload_str) > 80 else ''}")
    print(f"Secret:  {args.secret}")
    print(f"Header:  elevenlabs-signature: {signature}")
    print()

    if not args.no_curl:
        print("=" * 70)
        print("Complete cURL Command")
        print("=" * 70)
        print()
        curl_cmd = generate_curl_command(
            url=args.url,
            payload=payload_str,
            signature=signature,
            endpoint=args.endpoint
        )
        print(curl_cmd)
        print()

    print("=" * 70)
    print("✅ Ready to test!")
    print("=" * 70)


if __name__ == "__main__":
    main()
