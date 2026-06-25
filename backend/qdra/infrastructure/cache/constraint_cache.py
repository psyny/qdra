"""Constraint resolution cache for material/recipe constraint matching with L1/L2 caching."""
import uuid
from typing import Any, List
from cachetools import TTLCache
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import CacheService

# Module-level L1 cache for constraint resolution
_constraint_cache = None
_cache_service = None


def get_constraint_cache():
    """Get or create the constraint resolution L1 cache."""
    global _constraint_cache
    if _constraint_cache is None:
        _constraint_cache = TTLCache(maxsize=settings.cache_constraint_size, ttl=settings.cache_constraint_ttl)
    return _constraint_cache


def get_cache_service():
    """Get or create the shared cache service for L2 caching."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def clear_all_constraint_caches():
    """Clear all constraint resolution L1 caches."""
    global _constraint_cache
    if _constraint_cache is not None:
        _constraint_cache.clear()


def get_constraint_resolution(cache_key: str) -> List[uuid.UUID]:
    """Get constraint resolution result from cache (L1 then L2)."""
    if not settings.l1_caching:
        return None
    
    # Try L1 cache
    cache = get_constraint_cache()
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    # Try L2 cache
    if settings.l2_caching:
        cache_service = get_cache_service()
        cached = cache_service.get(cache_key)
        if cached is not None:
            # Populate L1 cache
            result = [uuid.UUID(id_str) for id_str in cached]
            cache[cache_key] = result
            return result
    
    return None


def set_constraint_resolution(cache_key: str, entity_ids: List[uuid.UUID]) -> None:
    """Set constraint resolution result in cache (L1 and L2)."""
    if not settings.l1_caching:
        return
    
    # Set L1 cache
    cache = get_constraint_cache()
    cache[cache_key] = entity_ids
    
    # Set L2 cache
    if settings.l2_caching:
        cache_service = get_cache_service()
        serialized = [str(id) for id in entity_ids]
        cache_service.set(cache_key, serialized, settings.cache_constraint_ttl)


def invalidate_constraint_resolution(project_id: uuid.UUID) -> None:
    """Invalidate constraint resolution caches for a project from both L1 and L2."""
    # Clear all from L1 (brute force since TTLCache doesn't support pattern matching)
    if settings.l1_caching:
        cache = get_constraint_cache()
        keys_to_delete = [k for k in cache.keys() if str(project_id) in k]
        for key in keys_to_delete:
            cache.pop(key, None)
    
    # Clear from L2 using pattern
    if settings.l2_caching:
        cache_service = get_cache_service()
        cache_service.delete_pattern(f"constraint_resolution:*:{project_id}:*")
