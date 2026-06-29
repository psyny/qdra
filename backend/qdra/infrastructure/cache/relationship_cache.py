"""Shared relationship cache for material-recipe operations at service level (L2 only)."""
from typing import Any
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import get_cache_service



def get_cached_data(key: str):
    """Get data from L2 cache."""
    if settings.l2_caching:
        cache_service = get_cache_service()
        cached = cache_service.get(key)
        if cached is not None:
            return cached
    return None


def set_cached_data(key: str, value: Any, ttl: int = None):
    """Set data in L2 cache."""
    if settings.l2_caching:
        cache_service = get_cache_service()
        cache_ttl = ttl if ttl is not None else settings.cache_relationship_ttl
        cache_service.set(key, value, cache_ttl)


def clear_pattern(project_id: str):
    """Clear all L2 caches matching the project pattern."""
    cache_service = get_cache_service()
    if settings.l2_caching:
        cache_service.delete_pattern(f"material_recipes:{project_id}:*")
        cache_service.delete_pattern(f"recipe_materials:{project_id}:*")
        cache_service.delete_pattern(f"constraint_resolution:*:{project_id}:*")
        cache_service.delete_pattern(f"param_values:{project_id}:*")
