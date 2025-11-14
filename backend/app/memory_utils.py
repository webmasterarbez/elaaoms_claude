"""
Utility functions for memory processing.
"""

import hashlib
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def get_content_hash(content: str) -> str:
    """
    Generate a content hash for duplicate detection.
    
    Normalizes content by:
    - Converting to lowercase
    - Stripping whitespace
    - Removing punctuation (optional, for fuzzy matching)
    
    Args:
        content: Memory content string
        
    Returns:
        SHA256 hash hex string
    """
    if not content:
        return ""
    
    # Normalize: lowercase, strip whitespace
    normalized = content.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Generate hash
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def normalize_content_for_hash(content: str) -> str:
    """
    Normalize content for hash comparison (more aggressive normalization).
    
    This allows fuzzy duplicate detection (e.g., "John Smith" vs "john smith").
    
    Args:
        content: Memory content string
        
    Returns:
        Normalized string
    """
    if not content:
        return ""
    
    # Lowercase
    normalized = content.lower()
    
    # Remove punctuation (optional - comment out if you want exact matches)
    # normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Strip
    normalized = normalized.strip()
    
    return normalized


def extract_sector_from_memory(memory: Dict[str, Any]) -> str:
    """
    Extract HSG sector from memory metadata or content.
    
    Args:
        memory: Memory dictionary
        
    Returns:
        Sector name (episodic, semantic, procedural, emotional, reflective)
    """
    # Check metadata first
    metadata = memory.get("metadata", {})
    if isinstance(metadata, dict):
        sector = metadata.get("sector")
        if sector:
            return sector.lower()
    
    # Check top-level
    sector = memory.get("sector")
    if sector:
        return sector.lower()
    
    # Default to semantic
    return "semantic"


def prepare_memory_for_storage(
    content: str,
    category: str,
    sector: str,
    importance: int,
    entities: List[str],
    caller_id: str,
    agent_id: str,
    conversation_id: str
) -> Dict[str, Any]:
    """
    Prepare memory dictionary for storage in OpenMemory.
    
    Args:
        content: Memory content
        category: Memory category
        sector: HSG sector
        importance: Importance score (1-10)
        entities: List of entities
        caller_id: Caller identifier
        agent_id: Agent identifier
        conversation_id: Conversation identifier
        
    Returns:
        Prepared memory dictionary
    """
    content_hash = get_content_hash(content)
    
    metadata = {
        "caller_id": caller_id,
        "agent_id": agent_id,
        "conversation_id": conversation_id,
        "category": category,
        "sector": sector,
        "importance": importance,
        "entities": entities,
        "content_hash": content_hash,
        "type": "conversation_memory"
    }
    
    # Tags for filtering
    tags = [
        category,
        sector,
        "conversation_memory"
    ]
    
    # Add importance-based tags
    if importance >= 8:
        tags.append("high_importance")
    if importance >= 9:
        tags.append("shareable")
    
    return {
        "content": content,
        "user_id": caller_id,
        "metadata": metadata,
        "tags": tags
    }

