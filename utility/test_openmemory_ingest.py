#!/usr/bin/env python3
"""
Test OpenMemory Multimodal Ingestion API with conversation transcript.

This script tests sending a conversation transcript to OpenMemory's
/memory/ingest endpoint to see how it automatically processes and stores memories.

Usage:
    python utility/test_openmemory_ingest.py <conversation_id>
    python utility/test_openmemory_ingest.py conv_01k04qved0ej19h9h0ddcgqnbz

Environment Variables:
    OPENMEMORY_API_URL: OpenMemory API URL (default: http://localhost:8080)
    OPENMEMORY_API_KEY: OpenMemory API key (optional, for authentication)
"""

import os
import sys
import json
import logging
import requests
import base64
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_env_file() -> None:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip('"').strip("'")
                    os.environ[key.strip()] = value
        logger.debug("Loaded environment variables from .env file")


def load_conversation_payload(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load conversation payload from disk.
    
    Args:
        conversation_id: Conversation identifier
        
    Returns:
        Conversation payload dict or None if not found
    """
    payload_path = Path(__file__).parent.parent / "backend" / "data" / "payloads" / conversation_id
    transcript_file = payload_path / f"{conversation_id}_transcription.json"
    
    if not transcript_file.exists():
        logger.error(f"Conversation file not found: {transcript_file}")
        return None
    
    try:
        with open(transcript_file, "r") as f:
            data = json.load(f)
        logger.info(f"Loaded conversation payload from {transcript_file}")
        return data
    except Exception as e:
        logger.error(f"Error loading conversation payload: {e}")
        return None


def format_transcript_as_text(transcript: list) -> str:
    """
    Format transcript array as plain text.
    
    Args:
        transcript: List of message objects
        
    Returns:
        Formatted text string
    """
    lines = []
    for msg in transcript:
        role = msg.get("role", "unknown")
        message = msg.get("message", "")
        if message:
            lines.append(f"{role.upper()}: {message}")
    
    return "\n\n".join(lines)


def format_transcript_as_html(transcript: list) -> str:
    """
    Format transcript array as HTML for ingestion.
    
    OpenMemory /memory/ingest typically supports HTML, DOCX, PDF formats.
    
    Args:
        transcript: List of message objects
        
    Returns:
        Formatted HTML string
    """
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head><title>Conversation Transcript</title></head><body>",
        "<h1>Conversation Transcript</h1>",
        "<div class='transcript'>"
    ]
    
    for msg in transcript:
        role = msg.get("role", "unknown")
        message = msg.get("message", "")
        if message:
            # Escape HTML entities
            message_escaped = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_parts.append(f"<p class='{role}'><strong>{role.upper()}:</strong> {message_escaped}</p>")
    
    html_parts.extend([
        "</div>",
        "</body></html>"
    ])
    
    return "\n".join(html_parts)


def test_multimodal_ingest(conversation_id: str, transcript: list, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test OpenMemory multimodal ingestion endpoint.
    
    Args:
        conversation_id: Conversation identifier
        transcript: List of transcript message objects
        metadata: Additional metadata to include
        
    Returns:
        Result dictionary with memory IDs and information
    """
    api_url = os.getenv("OPENMEMORY_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("OPENMEMORY_API_KEY", "")
    
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Format transcript as HTML (OpenMemory ingest supports HTML, DOCX, PDF)
    transcript_html = format_transcript_as_html(transcript)
    
    # Encode transcript as base64 for ingestion
    transcript_bytes = transcript_html.encode('utf-8')
    transcript_base64 = base64.b64encode(transcript_bytes).decode('utf-8')
    
    # Build payload for multimodal ingestion
    # See: https://openmemory.cavira.app/docs/api/add-memory (Multimodal Ingestion section)
    # Note: OpenMemory /memory/ingest supports HTML, DOCX, PDF, not plain text
    caller_id = metadata.get("caller_id", "unknown")
    
    # Based on OpenMemory source code analysis:
    # - Content type matching is case-insensitive string matching
    # - Supported types: "pdf", "docx", "html", "md", "markdown", "txt", "text"
    # - HTML uses turndown library to convert HTML to Markdown
    # - Use lowercase "html" (not "text/html" MIME type)
    payload = {
        "content_type": "html",  # Lowercase string, not MIME type
        "data": transcript_base64,
        "metadata": {
            **metadata,
            "test_approach": "ingest",  # Tag to identify this test
            "conversation_id": conversation_id,
            "source": "elevenlabs_transcription",
            "extraction_method": "openmemory_auto"
        }
    }
    
    # Note: According to source code, ingest API accepts:
    # - content_type: lowercase string ("html", "pdf", "docx", etc.)
    # - data: base64-encoded string or raw text
    # - metadata: custom object
    # - config: optional (force_root, sec_sz, lg_thresh)
    
    logger.info(f"Sending transcript to OpenMemory /memory/ingest")
    logger.info(f"Format: HTML (content_type: html - lowercase string, not MIME type)")
    logger.info(f"Transcript items: {len(transcript)}")
    logger.info(f"HTML length: {len(transcript_html)} characters")
    logger.info(f"Base64 length: {len(transcript_base64)} characters")
    logger.info(f"Note: OpenMemory will convert HTML to Markdown using turndown library")
    
    try:
        response = requests.post(
            f"{api_url}/memory/ingest",
            json=payload,
            headers=headers,
            timeout=60  # Longer timeout for ingestion
        )
        
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully ingested transcript")
            logger.info(f"Response: {json.dumps(result, indent=2, default=str)}")
            return {
                "success": True,
                "response": result,
                "memory_ids": result.get("memory_ids", []),
                "root_memory_id": result.get("rootMemoryId"),
                "child_memory_ids": result.get("childMemoryIds", [])
            }
        else:
            error_text = response.text
            logger.error(f"Ingestion failed: {response.status_code}")
            logger.error(f"Response: {error_text}")
            
            # Check for different error types
            if "Unsupported content type" in error_text:
                logger.warning("=" * 80)
                logger.warning("NOTE: Content type may be incorrect.")
                logger.warning("OpenMemory expects lowercase strings: 'html', 'pdf', 'docx', etc.")
                logger.warning("Not MIME types like 'text/html' or 'application/pdf'")
                logger.warning("=" * 80)
            elif "OpenAI" in error_text or "batch" in error_text.lower():
                logger.warning("=" * 80)
                logger.warning("NOTE: Ingestion processing succeeded, but embedding creation failed.")
                logger.warning("This indicates:")
                logger.warning("  - Content type is correct (HTML accepted)")
                logger.warning("  - HTML → Markdown conversion worked")
                logger.warning("  - But OpenAI embedding API call failed")
                logger.warning("This may be an OpenMemory configuration issue (OpenAI API key, quota, etc.)")
                logger.warning("=" * 80)
            
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_text
            }
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main entry point."""
    load_env_file()
    
    if len(sys.argv) < 2:
        logger.error("Usage: python utility/test_openmemory_ingest.py <conversation_id>")
        sys.exit(1)
    
    conversation_id = sys.argv[1]
    
    logger.info(f"Testing OpenMemory Multimodal Ingestion for conversation: {conversation_id}")
    logger.info("=" * 80)
    
    # Load conversation payload
    payload = load_conversation_payload(conversation_id)
    if not payload:
        logger.error(f"Failed to load conversation payload for {conversation_id}")
        sys.exit(1)
    
    # Extract transcript
    transcript = payload.get("data", {}).get("transcript", [])
    if not transcript:
        logger.error("No transcript found in payload")
        sys.exit(1)
    
    logger.info(f"Found {len(transcript)} transcript items")
    
    # Extract metadata
    agent_id = payload.get("data", {}).get("agent_id", "unknown")
    caller_id = None
    dynamic_vars = payload.get("data", {}).get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    if not dynamic_vars:
        dynamic_vars = payload.get("data", {}).get("dynamic_variables", {})
    caller_id = dynamic_vars.get("system__caller_id", "unknown")
    
    metadata = {
        "agent_id": agent_id,
        "caller_id": caller_id,
        "conversation_id": conversation_id,
        "transcript_items": len(transcript)
    }
    
    # Test ingestion (pass transcript list directly - will be formatted as HTML inside)
    result = test_multimodal_ingest(conversation_id, transcript, metadata)
    
    # Print results
    print("\n" + "=" * 80)
    print("TEST RESULTS: OpenMemory Multimodal Ingestion")
    print("=" * 80)
    
    if result.get("success"):
        print(f"✅ Successfully ingested transcript")
        print(f"\nMemory IDs created:")
        if result.get("root_memory_id"):
            print(f"  Root Memory ID: {result.get('root_memory_id')}")
        if result.get("child_memory_ids"):
            print(f"  Child Memory IDs ({len(result.get('child_memory_ids', []))}):")
            for i, mem_id in enumerate(result.get("child_memory_ids", [])[:10], 1):
                print(f"    {i}. {mem_id}")
            if len(result.get("child_memory_ids", [])) > 10:
                print(f"    ... and {len(result.get('child_memory_ids', [])) - 10} more")
        if result.get("memory_ids"):
            print(f"  Total Memory IDs: {len(result.get('memory_ids', []))}")
        print(f"\nTagged with: test_approach=ingest")
        print(f"\nFull response saved above in logs")
    else:
        print(f"❌ Ingestion failed")
        print(f"Status: {result.get('status_code', 'N/A')}")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"\n" + "=" * 80)
        print("NOTE: If ingestion failed, check:")
        print("  - Content type should be lowercase: 'html' (not 'text/html')")
        print("  - Data should be base64-encoded HTML string")
        print("  - OpenMemory converts HTML to Markdown using turndown")
        print("\nAlternative: Test /memory/add approaches:")
        print("  python utility/test_openmemory_add.py <conversation_id>")
        print("  python utility/test_openmemory_add.py <conversation_id> --chunked")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()

