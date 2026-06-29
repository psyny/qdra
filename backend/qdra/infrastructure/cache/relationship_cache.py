"""Shared relationship cache for material-recipe operations at service level."""
from typing import Any
from cachetools import TTLCache
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import get_cache_service

# Module-level L1 caches for relationship operations
_material_recipes_cache = None
_recipe_materials_cache = None


def get_material_recipes_cache():
    """Get or create the material recipes L1 cache."""
    global _material_recipes_cache
    if _material_recipes_cache is None:
        _material_recipes_cache = TTLCache(maxsize=settings.cache_relationship_size, ttl=settings.cache_relationship_ttl)
    return _material_recipes_cache


def get_recipe_materials_cache():
    """Get or create the recipe materials L1 cache."""
    global _recipe_materials_cache
    if _recipe_materials_cache is None:
        _recipe_materials_cache = TTLCache(maxsize=settings.cache_relationship_size, ttl=settings.cache_relationship_ttl)
    return _recipe_materials_cache


def clear_all_caches():
    """Clear all relationship L1 caches."""
    global _material_recipes_cache, _recipe_materials_cache
    if _material_recipes_cache is not None:
        _material_recipes_cache.clear()
    if _recipe_materials_cache is not None:
        _recipe_materials_cache.clear()


def get_cached_data(key: str):
    """Get data from L1 cache then L2 cache (material_recipes_cache as default)."""
    if settings.l1_caching:
        cache = get_material_recipes_cache()
        cached = cache.get(key)
        if cached is not None:
            return cached
    if settings.l2_caching:
        cache_service = get_cache_service()
        cached = cache_service.get(key)
        if cached is not None:
            return cached
    return None


def set_cached_data(key: str, value: Any, ttl: int = None):
    """Set data in L1 cache and L2 cache (material_recipes_cache as default)."""
    if settings.l1_caching:
        cache = get_material_recipes_cache()
        cache[key] = value
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
