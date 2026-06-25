"""Shared relationship cache for material-recipe operations at service level."""
from typing import Any
from cachetools import TTLCache
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import CacheService

# Module-level L1 caches for relationship operations
_material_recipes_cache = None
_recipe_materials_cache = None
_cache_service = None


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


def get_cache_service():
    """Get or create the shared cache service for L2 caching."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def clear_all_caches():
    """Clear all relationship L1 caches."""
    global _material_recipes_cache, _recipe_materials_cache
    if _material_recipes_cache is not None:
        _material_recipes_cache.clear()
    if _recipe_materials_cache is not None:
        _recipe_materials_cache.clear()


def get_cached_data(key: str):
    """Get data from L1 cache (material_recipes_cache as default)."""
    cache = get_material_recipes_cache()
    return cache.get(key)


def set_cached_data(key: str, value: Any, ttl: int = None):
    """Set data in L1 cache (material_recipes_cache as default)."""
    cache = get_material_recipes_cache()
    cache[key] = value


def clear_pattern(project_id: str):
    """Clear all L2 caches matching the project pattern."""
    cache_service = get_cache_service()
    if settings.l2_caching:
        cache_service.delete_pattern(f"material_recipes:{project_id}:*")
        cache_service.delete_pattern(f"recipe_materials:{project_id}:*")
        cache_service.delete_pattern(f"constraint_resolution:*:{project_id}:*")
