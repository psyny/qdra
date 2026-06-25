"""Entity cache for storing entity data, parameters, and slots together with L1/L2 caching."""
import uuid
from typing import Any, Dict, List, Optional
from cachetools import TTLCache
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import CacheService

# Module-level L1 cache for entity data
_entity_cache = None
_cache_service = None


def get_entity_cache():
    """Get or create the entity L1 cache."""
    global _entity_cache
    if _entity_cache is None:
        _entity_cache = TTLCache(maxsize=1000, ttl=settings.cache_entity_local_ttl)
    return _entity_cache


def get_cache_service():
    """Get or create the shared cache service for L2 caching."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def clear_all_entity_caches():
    """Clear all entity L1 caches."""
    global _entity_cache
    if _entity_cache is not None:
        _entity_cache.clear()


def get_entity_with_data(entity_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Get entity with parameters and slots from cache (L1 then L2)."""
    if not settings.l1_caching:
        return None
    
    # Try L1 cache
    cache = get_entity_cache()
    key = str(entity_id)
    cached = cache.get(key)
    if cached is not None:
        return cached
    
    # Try L2 cache
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"entity:{key}"
        cached = cache_service.get(l2_key)
        if cached is not None:
            # Populate L1 cache
            cache[key] = cached
            return cached
    
    return None


def set_entity_with_data(entity_id: uuid.UUID, data: Dict[str, Any]) -> None:
    """Set entity with parameters and slots in cache (L1 and L2)."""
    if not settings.l1_caching:
        return
    
    key = str(entity_id)
    
    # Set L1 cache
    cache = get_entity_cache()
    cache[key] = data
    
    # Set L2 cache
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"entity:{key}"
        cache_service.set(l2_key, data, settings.cache_entity_redis_ttl)


def invalidate_entity(entity_id: uuid.UUID) -> None:
    """Invalidate entity with parameters and slots from both L1 and L2 caches."""
    key = str(entity_id)
    
    # Clear from L1
    if settings.l1_caching:
        cache = get_entity_cache()
        cache.pop(key, None)
    
    # Clear from L2
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"entity:{key}"
        cache_service.delete(l2_key)
