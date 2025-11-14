"""
In-memory cache for fast memory retrieval during calls.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class MemoryCache:
    """
    Simple in-memory cache for caller memories.
    
    Cache structure:
    {
        "caller_id:agent_id": {
            "memories": [...],
            "timestamp": 1234567890,
            "ttl": 3600
        }
    }
    """
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize memory cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._cleanup_interval = 300  # Clean up every 5 minutes
        self._last_cleanup = time.time()
    
    def _get_cache_key(self, caller_id: str, agent_id: Optional[str] = None) -> str:
        """Generate cache key."""
        if agent_id:
            return f"{caller_id}:{agent_id}"
        return f"{caller_id}:*"
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        timestamp = cache_entry.get("timestamp", 0)
        ttl = cache_entry.get("ttl", self.default_ttl)
        return time.time() - timestamp > ttl
    
    def _cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            del self.cache[key]
            logger.debug(f"Removed expired cache entry: {key}")
        
        self._last_cleanup = current_time
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get(
        self,
        caller_id: str,
        agent_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached memories for caller/agent.
        
        Args:
            caller_id: Caller identifier
            agent_id: Optional agent identifier
            
        Returns:
            List of memories if cached and not expired, None otherwise
        """
        self._cleanup_expired()
        
        cache_key = self._get_cache_key(caller_id, agent_id)
        entry = self.cache.get(cache_key)
        
        if entry is None:
            return None
        
        if self._is_expired(entry):
            del self.cache[cache_key]
            logger.debug(f"Cache entry expired: {cache_key}")
            return None
        
        logger.debug(f"Cache hit: {cache_key}")
        return entry.get("memories", [])
    
    def set(
        self,
        caller_id: str,
        memories: List[Dict[str, Any]],
        agent_id: Optional[str] = None,
        ttl: Optional[int] = None
    ):
        """
        Cache memories for caller/agent.
        
        Args:
            caller_id: Caller identifier
            memories: List of memories to cache
            agent_id: Optional agent identifier
            ttl: Optional time-to-live in seconds (uses default if not provided)
        """
        self._cleanup_expired()
        
        cache_key = self._get_cache_key(caller_id, agent_id)
        
        self.cache[cache_key] = {
            "memories": memories,
            "timestamp": time.time(),
            "ttl": ttl or self.default_ttl
        }
        
        logger.debug(f"Cached {len(memories)} memories for {cache_key}")
    
    def invalidate(
        self,
        caller_id: str,
        agent_id: Optional[str] = None
    ):
        """
        Invalidate cache for caller/agent.
        
        Args:
            caller_id: Caller identifier
            agent_id: Optional agent identifier
        """
        cache_key = self._get_cache_key(caller_id, agent_id)
        
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.debug(f"Invalidated cache: {cache_key}")
        
        # Also invalidate agent-specific cache if agent_id provided
        if agent_id:
            wildcard_key = self._get_cache_key(caller_id, None)
            if wildcard_key in self.cache:
                del self.cache[wildcard_key]
                logger.debug(f"Invalidated wildcard cache: {wildcard_key}")
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._cleanup_expired()
        
        total_entries = len(self.cache)
        total_memories = sum(
            len(entry.get("memories", []))
            for entry in self.cache.values()
        )
        
        return {
            "total_entries": total_entries,
            "total_memories": total_memories,
            "default_ttl": self.default_ttl
        }


# Global cache instance
_memory_cache: Optional[MemoryCache] = None


def get_memory_cache() -> MemoryCache:
    """Get global memory cache instance."""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache

