"""Redis cache service for shared caching across services."""
import json
import redis
from typing import Optional, Any
from qdra.infrastructure.config.settings import settings


class CacheService:
    """Redis cache service with JSON serialization."""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            value = self.redis_client.get(key)
            if value is not None:
                return json.loads(value)
        except Exception:
            pass
        return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set a value in cache with TTL."""
        try:
            serialized = json.dumps(value)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False


# Singleton instance
_cache_service_instance = None


def get_cache_service() -> CacheService:
    """Get the singleton cache service instance."""
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
    return _cache_service_instance
