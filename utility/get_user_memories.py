#!/usr/bin/env python3
"""
Retrieve all memories for a specific user from OpenMemory.

Usage:
    python utility/get_user_memories.py [caller_id]
    python utility/get_user_memories.py +16125082017
    python utility/get_user_memories.py +16125082017 --json

Environment Variables:
    OPENMEMORY_API_URL: OpenMemory API URL (default: http://localhost:8080)
    OPENMEMORY_API_KEY: OpenMemory API key (optional, for authentication)
"""

import json
import sys
import os
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG to see all details
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
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key.strip()] = value
        logger.debug("Loaded environment variables from .env file")
    else:
        logger.warning(f".env file not found at {env_path}")


def get_all_memories_for_user(caller_id: str, json_output: bool = False):
    """
    Retrieve all memories for a specific user from OpenMemory.
    
    Args:
        caller_id: User identifier (phone number)
        json_output: If True, output only JSON
    """
    # Get OpenMemory configuration
    api_url = os.getenv("OPENMEMORY_API_URL", "http://localhost:8080")
    api_key = os.getenv("OPENMEMORY_API_KEY", "")
    
    # Remove trailing slash from URL
    api_url = api_url.rstrip("/")
    
    try:
        if not json_output:
            print(f"Retrieving all memories for user: {caller_id}")
            print(f"OpenMemory URL: {api_url}")
            print("-" * 80)
        
        # Prepare request
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            if not json_output:
                logger.debug(f"Using API key (length: {len(api_key)})")
        else:
            if not json_output:
                logger.warning("No OPENMEMORY_API_KEY found - authentication may fail")
        
        # Query to get all memories using correct OpenMemory API format
        # See: https://openmemory.cavira.app/docs/api/query
        payload = {
            "query": "",  # Required field (empty string for all memories)
            "k": 1000,  # Use 'k' not 'limit' per API spec
            "filters": {
                "user_id": caller_id,  # Proper user isolation
                "tags": []  # We'll filter by type in post-processing
            }
        }
        
        if not json_output:
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            logger.debug(f"Request URL: {api_url}/memory/query")
        
        response = requests.post(
            f"{api_url}/memory/query",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if not json_output:
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
        
        response.raise_for_status()
        result = response.json()
        
        if not json_output:
            logger.debug(f"Response keys: {list(result.keys())}")
            logger.debug(f"Response sample: {json.dumps(result, indent=2, default=str)[:500]}")
        
        # OpenMemory returns memories in different formats
        # Try multiple possible response formats
        memory_list = []
        if isinstance(result, list):
            memory_list = result
        elif isinstance(result, dict):
            # Check all possible response format keys
            memory_list = result.get("matches", result.get("memories", result.get("results", result.get("data", []))))
            # Also check if the response has a different structure
            if not memory_list and "data" in result:
                data = result["data"]
                if isinstance(data, list):
                    memory_list = data
                elif isinstance(data, dict):
                    memory_list = data.get("matches", data.get("memories", []))
        
        if not json_output:
            print(f"\nFound {len(memory_list)} memories for user {caller_id}")
            print("Fetching full memory details (including metadata)...\n")
        
        # OpenMemory /memory/query doesn't return metadata, so we need to fetch full details
        # for each memory to get metadata
        memories = []
        for mem in memory_list:
            memory_id = mem.get("id")
            if not memory_id:
                memories.append(mem)  # Skip if no ID
                continue
            
            try:
                # GET /memory/{id} returns full memory with metadata
                mem_response = requests.get(
                    f"{api_url}/memory/{memory_id}",
                    headers=headers,
                    timeout=30
                )
                mem_response.raise_for_status()
                full_memory = mem_response.json()
                # Merge query result fields (score, salience) with full memory
                if "score" in mem:
                    full_memory["score"] = mem.get("score")
                if "salience" in mem:
                    full_memory["salience"] = mem.get("salience")
                
                # Filter out agent profiles - only include conversation memories
                metadata = full_memory.get("metadata", {})
                if isinstance(metadata, dict):
                    mem_type = metadata.get("type")
                    if mem_type == "agent_profile":
                        # Skip agent profiles
                        continue
                    # Only include conversation_memory type (or legacy memories without type)
                    if mem_type and mem_type != "conversation_memory":
                        continue
                
                memories.append(full_memory)
            except Exception as e:
                logger.warning(f"Failed to fetch full details for memory {memory_id}: {e}")
                # Use query result as fallback, but still filter agent profiles
                metadata = mem.get("metadata", {})
                if isinstance(metadata, dict) and metadata.get("type") == "agent_profile":
                    continue
                memories.append(mem)
        
        if not memories:
            if json_output:
                print(json.dumps({
                    "user_id": caller_id,
                    "total_memories": 0,
                    "memories": []
                }, indent=2))
            else:
                print("No memories found for this user.")
            return
        
        # Group by conversation
        # Handle both old format (no metadata) and new format (with metadata)
        by_conversation = {}
        for mem in memories:
            # Try to get metadata - could be None, empty dict, or full dict
            metadata = mem.get("metadata")
            if metadata is None:
                metadata = {}
            elif not isinstance(metadata, dict):
                metadata = {}
            
            conv_id = metadata.get("conversation_id", "unknown")
            if conv_id not in by_conversation:
                by_conversation[conv_id] = []
            by_conversation[conv_id].append(mem)
        
        # Calculate statistics
        categories = {}
        agents = {}
        importance_counts = {i: 0 for i in range(1, 11)}
        
        for mem in memories:
            # Handle metadata that might be None or missing
            metadata = mem.get("metadata")
            if metadata is None:
                metadata = {}
            elif not isinstance(metadata, dict):
                metadata = {}
            
            cat = metadata.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            
            agent = metadata.get("agent_id", "unknown")
            agents[agent] = agents.get(agent, 0) + 1
            
            importance = metadata.get("importance", 0)
            if 1 <= importance <= 10:
                importance_counts[importance] = importance_counts.get(importance, 0) + 1
        
        if json_output:
            # Output JSON format
            output = {
                "user_id": caller_id,
                "total_memories": len(memories),
                "total_conversations": len(by_conversation),
                "statistics": {
                    "by_category": categories,
                    "by_agent": agents,
                    "by_importance": {str(k): v for k, v in importance_counts.items() if v > 0}
                },
                "memories": [
                    {
                        "id": mem.get("id") or mem.get("memory_id", "unknown"),
                        "content": mem.get("content", ""),
                        "metadata": mem.get("metadata") or {},
                        "score": mem.get("score")
                    }
                    for mem in memories
                ],
                "grouped_by_conversation": {
                    conv_id: [
                        {
                            "id": m.get("id") or m.get("memory_id"),
                            "content": m.get("content"),
                            "metadata": m.get("metadata") or {},
                            "score": m.get("score")
                        }
                        for m in conv_memories
                    ]
                    for conv_id, conv_memories in by_conversation.items()
                }
            }
            print(json.dumps(output, indent=2, default=str))
        else:
            # Display formatted output
            print(f"Memories grouped by conversation ({len(by_conversation)} conversations):\n")
            
            for conv_id, conv_memories in sorted(by_conversation.items()):
                print(f"\n{'='*80}")
                print(f"Conversation: {conv_id} ({len(conv_memories)} memories)")
                print(f"{'='*80}")
                
                for i, mem in enumerate(conv_memories, 1):
                    memory_id = mem.get("id") or mem.get("memory_id", "unknown")
                    content = mem.get("content", "")
                    metadata = mem.get("metadata") or {}
                    category = metadata.get("category", "unknown")
                    importance = metadata.get("importance", 0)
                    timestamp = metadata.get("timestamp", "unknown")
                    agent_id = metadata.get("agent_id", "unknown")
                    score = mem.get("score")
                    
                    print(f"\n[{i}] Memory ID: {memory_id}")
                    print(f"    Content: {content}")
                    print(f"    Category: {category}")
                    print(f"    Importance: {importance}/10")
                    print(f"    Agent: {agent_id}")
                    print(f"    Timestamp: {timestamp}")
                    if score is not None:
                        print(f"    Relevance Score: {score:.3f}")
                    if metadata.get("entities"):
                        print(f"    Entities: {', '.join(metadata.get('entities', []))}")
            
            # Summary statistics
            print(f"\n\n{'='*80}")
            print("SUMMARY STATISTICS")
            print(f"{'='*80}")
            print(f"Total memories: {len(memories)}")
            print(f"Total conversations: {len(by_conversation)}")
            
            print(f"\nBy category:")
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                print(f"  {cat}: {count}")
            
            print(f"\nBy agent:")
            for agent, count in sorted(agents.items(), key=lambda x: -x[1]):
                print(f"  {agent}: {count}")
            
            print(f"\nBy importance:")
            for imp, count in sorted([(k, v) for k, v in importance_counts.items() if v > 0], 
                                   key=lambda x: -x[1]):
                print(f"  {imp}/10: {count} memories")
        
        # Save to JSON file
        output_file = f"memories_{caller_id.replace('+', '')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "user_id": caller_id,
                "total_memories": len(memories),
                "total_conversations": len(by_conversation),
                "statistics": {
                    "by_category": categories,
                    "by_agent": agents,
                    "by_importance": {str(k): v for k, v in importance_counts.items() if v > 0}
                },
                "memories": memories,
                "grouped_by_conversation": {
                    conv_id: [
                        {
                            "id": m.get("id") or m.get("memory_id"),
                            "content": m.get("content"),
                            "metadata": m.get("metadata"),
                            "score": m.get("score")
                        }
                        for m in conv_memories
                    ]
                    for conv_id, conv_memories in by_conversation.items()
                }
            }, f, indent=2, default=str)
        
        if not json_output:
            print(f"\n\nFull data saved to: {output_file}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to OpenMemory API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        if json_output:
            print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


def main():
    """Main entry point."""
    load_env_file()
    
    caller_id = "+16125082017"
    json_output = False
    
    # Parse command line arguments
    args = sys.argv[1:]
    if "--json" in args:
        json_output = True
        args.remove("--json")
    
    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)
    
    if args:
        caller_id = args[0]
    
    if not caller_id.startswith("+"):
        logger.warning(f"Caller ID should start with '+', got: {caller_id}")
    
    get_all_memories_for_user(caller_id, json_output=json_output)


if __name__ == "__main__":
    main()

