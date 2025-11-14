#!/usr/bin/env python3
"""
Test OpenMemory Direct Add Memory API with conversation transcript.

This script tests sending a conversation transcript directly to OpenMemory's
/memory/add endpoint to see how it stores the content.

Usage:
    python utility/test_openmemory_add.py <conversation_id> [--chunked]
    python utility/test_openmemory_add.py conv_01k04qved0ej19h9h0ddcgqnbz
    python utility/test_openmemory_add.py conv_01k04qved0ej19h9h0ddcgqnbz --chunked

Options:
    --chunked: Split transcript into interaction-level chunks (one memory per user/agent turn pair)

Environment Variables:
    OPENMEMORY_API_URL: OpenMemory API URL (default: http://localhost:8080)
    OPENMEMORY_API_KEY: OpenMemory API key (optional, for authentication)
"""

import os
import sys
import json
import logging
import requests
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

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


def create_chunks_from_transcript(transcript: list) -> List[Dict[str, Any]]:
    """
    Create interaction-level chunks from transcript.
    
    Each chunk contains a user message and the following agent response.
    
    Args:
        transcript: List of message objects
        
    Returns:
        List of chunk dictionaries with content and metadata
    """
    chunks = []
    current_chunk = []
    chunk_index = 0
    
    for i, msg in enumerate(transcript):
        role = msg.get("role", "").lower()
        message = msg.get("message", "")
        
        if not message:
            continue
        
        current_chunk.append(f"{role.upper()}: {message}")
        
        # Create chunk after agent response (or at end)
        if role == "agent" or i == len(transcript) - 1:
            if current_chunk:
                chunk_content = "\n\n".join(current_chunk)
                chunks.append({
                    "content": chunk_content,
                    "chunk_index": chunk_index,
                    "message_count": len(current_chunk)
                })
                chunk_index += 1
                current_chunk = []
    
    return chunks


def add_memory_to_openmemory(
    content: str,
    user_id: str,
    metadata: Dict[str, Any],
    api_url: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """
    Add a single memory to OpenMemory.
    
    Args:
        content: Memory content
        user_id: User identifier
        metadata: Memory metadata
        api_url: OpenMemory API URL
        api_key: OpenMemory API key
        
    Returns:
        Memory result dict or None if failed
    """
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    payload = {
        "content": content,
        "user_id": user_id,
        "metadata": metadata
    }
    
    # Add tags from metadata - include test approach tag for easy filtering
    tags = []
    if "tags" in metadata:
        tags = metadata.get("tags", [])
    elif "category" in metadata:
        tags.append(metadata["category"])
    
    # Always add test approach tag for comparison
    test_approach = metadata.get("test_approach", "unknown")
    tags.append(f"test_{test_approach}")
    tags.append("transcription")
    tags.append(metadata.get("conversation_id", "unknown"))
    
    if tags:
        payload["tags"] = tags
    
    try:
        response = requests.post(
            f"{api_url}/memory/add",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "memory_id": result.get("id"),
                "sectors": result.get("sectors", []),
                "primary_sector": result.get("primary_sector")
            }
        else:
            logger.error(f"Failed to add memory: {response.status_code} - {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        logger.error(f"Error adding memory: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def test_direct_add(conversation_id: str, transcript: list, caller_id: str, agent_id: str, chunked: bool = False) -> Dict[str, Any]:
    """
    Test OpenMemory direct add endpoint.
    
    Args:
        conversation_id: Conversation identifier
        transcript: Transcript array
        caller_id: Caller identifier
        agent_id: Agent identifier
        chunked: If True, split into interaction chunks
        
    Returns:
        Result dictionary with memory IDs and information
    """
    api_url = os.getenv("OPENMEMORY_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("OPENMEMORY_API_KEY", "")
    
    approach = "chunked_add" if chunked else "direct_add"
    
    if chunked:
        # Create chunks
        chunks = create_chunks_from_transcript(transcript)
        logger.info(f"Created {len(chunks)} chunks from transcript")
        
        memory_results = []
        for chunk in chunks:
            metadata = {
                "test_approach": approach,
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "caller_id": caller_id,
                "chunk_index": chunk["chunk_index"],
                "message_count": chunk["message_count"],
                "source": "elevenlabs_transcription",
                "extraction_method": "openmemory_auto_chunked"
            }
            
            result = add_memory_to_openmemory(
                content=chunk["content"],
                user_id=caller_id,
                metadata=metadata,
                api_url=api_url,
                api_key=api_key
            )
            
            if result and result.get("success"):
                memory_results.append(result)
                logger.info(f"Added chunk {chunk['chunk_index']}: memory_id={result.get('memory_id')}")
            else:
                logger.warning(f"Failed to add chunk {chunk['chunk_index']}: {result.get('error', 'Unknown error')}")
        
        return {
            "success": len(memory_results) > 0,
            "approach": approach,
            "total_chunks": len(chunks),
            "successful_memories": len(memory_results),
            "memory_ids": [r.get("memory_id") for r in memory_results if r.get("memory_id")],
            "sectors": [r.get("primary_sector") for r in memory_results if r.get("primary_sector")]
        }
    else:
        # Send entire transcript as one memory
        transcript_text = format_transcript_as_text(transcript)
        
        metadata = {
            "test_approach": approach,
            "conversation_id": conversation_id,
            "agent_id": agent_id,
            "caller_id": caller_id,
            "transcript_items": len(transcript),
            "source": "elevenlabs_transcription",
            "extraction_method": "openmemory_auto_full"
        }
        
        logger.info(f"Sending full transcript to OpenMemory /memory/add")
        logger.info(f"Transcript length: {len(transcript_text)} characters")
        
        result = add_memory_to_openmemory(
            content=transcript_text,
            user_id=caller_id,
            metadata=metadata,
            api_url=api_url,
            api_key=api_key
        )
        
        if result and result.get("success"):
            return {
                "success": True,
                "approach": approach,
                "memory_id": result.get("memory_id"),
                "sectors": result.get("sectors", []),
                "primary_sector": result.get("primary_sector")
            }
        else:
            return {
                "success": False,
                "approach": approach,
                "error": result.get("error", "Unknown error") if result else "No result"
            }


def main():
    """Main entry point."""
    load_env_file()
    
    parser = argparse.ArgumentParser(
        description="Test OpenMemory Direct Add Memory API with conversation transcript"
    )
    parser.add_argument(
        "conversation_id",
        help="Conversation ID to test"
    )
    parser.add_argument(
        "--chunked",
        action="store_true",
        help="Split transcript into interaction-level chunks (one memory per turn pair)"
    )
    
    args = parser.parse_args()
    conversation_id = args.conversation_id
    chunked = args.chunked
    
    logger.info(f"Testing OpenMemory Direct Add for conversation: {conversation_id}")
    logger.info(f"Mode: {'Chunked (interaction-level)' if chunked else 'Full transcript'}")
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
    
    if caller_id == "unknown":
        logger.warning("Caller ID not found, using 'unknown'")
    
    # Test direct add
    result = test_direct_add(conversation_id, transcript, caller_id, agent_id, chunked=chunked)
    
    # Print results
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: OpenMemory Direct Add ({result.get('approach', 'unknown')})")
    print("=" * 80)
    
    if result.get("success"):
        print(f"✅ Successfully added memory/memories")
        
        if chunked:
            print(f"\nChunked Approach:")
            print(f"  Total chunks created: {result.get('total_chunks', 0)}")
            print(f"  Successful memories: {result.get('successful_memories', 0)}")
            print(f"\nMemory IDs created:")
            for i, mem_id in enumerate(result.get("memory_ids", [])[:20], 1):
                print(f"  {i}. {mem_id}")
            if len(result.get("memory_ids", [])) > 20:
                print(f"  ... and {len(result.get('memory_ids', [])) - 20} more")
            
            sectors = result.get("sectors", [])
            if sectors:
                from collections import Counter
                sector_counts = Counter(sectors)
                print(f"\nSector Classification:")
                for sector, count in sector_counts.most_common():
                    print(f"  {sector}: {count}")
        else:
            print(f"\nFull Transcript Approach:")
            print(f"  Memory ID: {result.get('memory_id')}")
            if result.get("primary_sector"):
                print(f"  Primary Sector: {result.get('primary_sector')}")
            if result.get("sectors"):
                print(f"  Sectors: {', '.join(result.get('sectors', []))}")
        
        print(f"\nTagged with: test_approach={result.get('approach')}")
    else:
        print(f"❌ Failed to add memory")
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

