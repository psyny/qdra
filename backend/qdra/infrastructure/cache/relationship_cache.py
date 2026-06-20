"""Shared relationship cache for material-recipe endpoints."""
from cachetools import TTLCache
from qdra.infrastructure.config.settings import settings

# Module-level L1 caches for relationship endpoints
_material_recipes_cache = None
_recipe_materials_cache = None


def get_material_recipes_cache():
    """Get or create the material recipes L1 cache."""
    global _material_recipes_cache
    if _material_recipes_cache is None:
        _material_recipes_cache = TTLCache(maxsize=1000, ttl=settings.cache_relationship_ttl)
    return _material_recipes_cache


def get_recipe_materials_cache():
    """Get or create the recipe materials L1 cache."""
    global _recipe_materials_cache
    if _recipe_materials_cache is None:
        _recipe_materials_cache = TTLCache(maxsize=1000, ttl=settings.cache_relationship_ttl)
    return _recipe_materials_cache


def clear_all_caches():
    """Clear all relationship L1 caches."""
    global _material_recipes_cache, _recipe_materials_cache
    if _material_recipes_cache is not None:
        _material_recipes_cache.clear()
    if _recipe_materials_cache is not None:
        _recipe_materials_cache.clear()
