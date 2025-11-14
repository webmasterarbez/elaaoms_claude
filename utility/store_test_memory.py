#!/usr/bin/env python3
"""
Store a test memory in OpenMemory.

This script stores a simple memory using direct HTTP requests to OpenMemory API.

Usage:
    python utility/store_test_memory.py "Memory content here"
    python utility/store_test_memory.py "Testing OpenMemory MCP integration in Cursor"

Environment Variables:
    OPENMEMORY_API_URL: OpenMemory API URL (default: http://localhost:8080)
    OPENMEMORY_API_KEY: OpenMemory API key (optional, for authentication)
"""

import os
import sys
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any

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
    else:
        logger.warning(f".env file not found at {env_path}")


def store_memory(content: str) -> Optional[str]:
    """
    Store a memory in OpenMemory using direct API call.
    
    Args:
        content: Memory content to store
        
    Returns:
        Memory ID if successful, None otherwise
    """
    # Load environment variables
    load_env_file()
    
    # Get API configuration
    api_url = os.getenv("OPENMEMORY_API_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("OPENMEMORY_API_KEY", "")
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Use test values for MCP integration testing
    user_id = "test_user_mcp"
    metadata = {
        "agent_id": "test_agent_mcp",
        "conversation_id": "test_conv_mcp",
        "source": "mcp_test",
        "type": "test_memory",
        "category": "test"
    }
    
    # Build payload
    payload = {
        "content": content,
        "user_id": user_id,
        "metadata": metadata,
        "tags": ["mcp_test", "cursor_integration"]
    }
    
    logger.info(f"Storing memory: {content}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"API URL: {api_url}")
    logger.info(f"Metadata: {metadata}")
    
    try:
        response = requests.post(
            f"{api_url}/memory/add",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            memory_id = result.get("id")
            logger.info(f"✅ Successfully stored memory with ID: {memory_id}")
            return memory_id
        else:
            logger.error(f"❌ Failed to store memory: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error storing memory: {e}", exc_info=True)
        return None


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python utility/store_test_memory.py \"Memory content here\"")
        sys.exit(1)
    
    content = sys.argv[1]
    
    if not content:
        logger.error("Memory content cannot be empty")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("Storing test memory in OpenMemory")
    logger.info("=" * 80)
    
    # Store the memory
    memory_id = store_memory(content)
    
    if memory_id:
        print("\n" + "=" * 80)
        print(f"✅ SUCCESS: Memory stored with ID: {memory_id}")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ FAILED: Could not store memory")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()

