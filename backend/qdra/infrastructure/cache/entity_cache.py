"""Entity cache for storing entity data, parameters, and slots with L1/L2 caching.

This module provides the only access point for entity cache operations.
All cache reads/writes must go through the named functions below.
No other part of the codebase should call get_entity_cache() directly for read/write.

Access contract:
- entity_service.py: reads and writes all 3 prefixes via these functions
- invalidation_controller.py: calls invalidate_entity() for event-driven invalidation
- project_templates.py: calls clear_all_entity_related_caches() for bulk clears
- Everyone else: goes through entity_service.py or invalidation_controller.py
"""
import uuid
from typing import Any, Dict, List, Optional
from cachetools import TTLCache
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import get_cache_service

# Module-level L1 cache for entity data
_entity_cache = None


def get_entity_cache():
    """Get or create the entity L1 cache.

    This is exported for clear_all_entity_caches() only.
    Do not use this for direct read/write operations.
    """
    global _entity_cache
    if _entity_cache is None:
        _entity_cache = TTLCache(maxsize=settings.cache_entity_size, ttl=settings.cache_entity_ttl)
    return _entity_cache


def clear_all_entity_caches():
    """Clear all entity L1 caches."""
    global _entity_cache
    if _entity_cache is not None:
        _entity_cache.clear()


# ---------------------------------------------------------------------------
# entity: prefix (base entity + image metadata, no params, no slots)
# ---------------------------------------------------------------------------

def get_entity_base(entity_id: uuid.UUID) -> Optional[Dict]:
    """Get base entity fields + image metadata from cache (L1 then L2).

    Returns dict with: id, project_id, entity_type_id, group, kind,
    created_at, updated_at, image (metadata only, no url).
    """
    print(f"[DEBUG] get_entity_base({entity_id}): L1 enabled={settings.l1_caching}, L2 enabled={settings.l2_caching}")
    key = str(entity_id)
    if settings.l1_caching:
        cached = get_entity_cache().get(f"entity:{key}")
        if cached is not None:
            print(f"[DEBUG] get_entity_base({entity_id}): L1 cache HIT")
            return cached
        print(f"[DEBUG] get_entity_base({entity_id}): L1 cache MISS")
    if settings.l2_caching:
        cached = get_cache_service().get(f"entity:{key}")
        if cached is not None:
            print(f"[DEBUG] get_entity_base({entity_id}): L2 cache HIT")
            return cached
        print(f"[DEBUG] get_entity_base({entity_id}): L2 cache MISS")
    print(f"[DEBUG] get_entity_base({entity_id}): NO cache hit")
    return None


def set_entity_base(entity_id: uuid.UUID, data: Dict) -> None:
    """Set base entity fields + image metadata in cache (L1 and L2)."""
    key = str(entity_id)
    if settings.l1_caching:
        get_entity_cache()[f"entity:{key}"] = data
    if settings.l2_caching:
        get_cache_service().set(f"entity:{key}", data, settings.cache_entity_ttl)


# ---------------------------------------------------------------------------
# params: prefix (parameters list only)
# ---------------------------------------------------------------------------

def get_entity_params(entity_id: uuid.UUID) -> Optional[List]:
    """Get entity parameters list from cache (L1 then L2)."""
    key = str(entity_id)
    if settings.l1_caching:
        cached = get_entity_cache().get(f"params:{key}")
        if cached is not None:
            return cached
    if settings.l2_caching:
        cached = get_cache_service().get(f"params:{key}")
        if cached is not None:
            return cached
    return None


def set_entity_params(entity_id: uuid.UUID, data: List) -> None:
    """Set entity parameters list in cache (L1 and L2)."""
    key = str(entity_id)
    if settings.l1_caching:
        get_entity_cache()[f"params:{key}"] = data
    if settings.l2_caching:
        get_cache_service().set(f"params:{key}", data, settings.cache_entity_ttl)


# ---------------------------------------------------------------------------
# slots: prefix (slots list only, recipe entities only)
# ---------------------------------------------------------------------------

def get_entity_slots(entity_id: uuid.UUID) -> Optional[List]:
    """Get entity slots list from cache (L1 then L2)."""
    key = str(entity_id)
    if settings.l1_caching:
        cached = get_entity_cache().get(f"slots:{key}")
        if cached is not None:
            return cached
    if settings.l2_caching:
        cached = get_cache_service().get(f"slots:{key}")
        if cached is not None:
            return cached
    return None


def set_entity_slots(entity_id: uuid.UUID, data: List) -> None:
    """Set entity slots list in cache (L1 and L2)."""
    key = str(entity_id)
    if settings.l1_caching:
        get_entity_cache()[f"slots:{key}"] = data
    if settings.l2_caching:
        get_cache_service().set(f"slots:{key}", data, settings.cache_entity_ttl)


# ---------------------------------------------------------------------------
# Invalidation (all 3 keys)
# ---------------------------------------------------------------------------

def invalidate_entity(entity_id: uuid.UUID) -> None:
    """Invalidate all entity-related cache entries for a single entity (L1 and L2).

    Clears entity:, params:, and slots: keys for the given entity_id.
    """
    key = str(entity_id)
    if settings.l1_caching:
        cache = get_entity_cache()
        cache.pop(f"entity:{key}", None)
        cache.pop(f"params:{key}", None)
        cache.pop(f"slots:{key}", None)
    if settings.l2_caching:
        svc = get_cache_service()
        svc.delete(f"entity:{key}")
        svc.delete(f"params:{key}")
        svc.delete(f"slots:{key}")


# ---------------------------------------------------------------------------
# Bulk clear helper
# ---------------------------------------------------------------------------

def clear_all_entity_related_caches() -> None:
    """Clear all entity-related L1 caches and L2 patterns.

    This is used by project_templates.py for project-wide template changes.
    """
    clear_all_entity_caches()
    if settings.l2_caching:
        svc = get_cache_service()
        svc.delete_pattern("entity:*")
        svc.delete_pattern("params:*")
        svc.delete_pattern("slots:*")
