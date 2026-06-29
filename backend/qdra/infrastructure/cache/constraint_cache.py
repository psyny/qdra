"""Constraint resolution cache for material/recipe constraint matching with L2 caching."""
import uuid
from typing import Any, List
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import get_cache_service



def get_constraint_resolution(cache_key: str) -> List[uuid.UUID]:
    """Get constraint resolution result from cache (L2 only)."""
    # Try L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        cached = cache_service.get(cache_key)
        if cached is not None:
            result = [uuid.UUID(id_str) for id_str in cached]
            return result
    
    return None


def set_constraint_resolution(cache_key: str, entity_ids: List[uuid.UUID]) -> None:
    """Set constraint resolution result in cache (L2 only)."""
    # Set L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        serialized = [str(id) for id in entity_ids]
        cache_service.set(cache_key, serialized, settings.cache_constraint_ttl)


def invalidate_constraint_resolution(project_id: uuid.UUID) -> None:
    """Invalidate constraint resolution caches for a project from L2."""
    # Clear from L2 using pattern
    if settings.l2_caching:
        cache_service = get_cache_service()
        cache_service.delete_pattern(f"constraint_resolution:*:{project_id}:*")
