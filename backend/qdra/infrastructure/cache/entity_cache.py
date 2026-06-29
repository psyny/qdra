"""Entity cache for storing entity data, parameters, and slots with L2 caching.

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
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import get_cache_service



# ---------------------------------------------------------------------------
# entity: prefix (base entity + image metadata, no params, no slots)
# ---------------------------------------------------------------------------

def get_entity_base(entity_id: uuid.UUID) -> Optional[Dict]:
    """Get base entity fields + image metadata from cache (L2 only).

    Returns dict with: id, project_id, entity_type_id, group, kind,
    created_at, updated_at, image (metadata only, no url).
    """
    key = str(entity_id)
    if settings.l2_caching:
        cached = get_cache_service().get(f"entity:{key}")
        if cached is not None:
            return cached
    return None


def set_entity_base(entity_id: uuid.UUID, data: Dict) -> None:
    """Set base entity fields + image metadata in cache (L2 only)."""
    key = str(entity_id)
    if settings.l2_caching:
        get_cache_service().set(f"entity:{key}", data, settings.cache_entity_ttl)


# ---------------------------------------------------------------------------
# params: prefix (parameters list only)
# ---------------------------------------------------------------------------

def get_entity_params(entity_id: uuid.UUID) -> Optional[List]:
    """Get entity parameters list from cache (L2 only)."""
    key = str(entity_id)
    if settings.l2_caching:
        cached = get_cache_service().get(f"params:{key}")
        if cached is not None:
            return cached
    return None


def set_entity_params(entity_id: uuid.UUID, data: List) -> None:
    """Set entity parameters list in cache (L2 only)."""
    key = str(entity_id)
    if settings.l2_caching:
        get_cache_service().set(f"params:{key}", data, settings.cache_entity_ttl)


# ---------------------------------------------------------------------------
# slots: prefix (slots list only, recipe entities only)
# ---------------------------------------------------------------------------

def get_entity_slots(entity_id: uuid.UUID) -> Optional[List]:
    """Get entity slots list from cache (L2 only)."""
    key = str(entity_id)
    if settings.l2_caching:
        cached = get_cache_service().get(f"slots:{key}")
        if cached is not None:
            return cached
    return None


def set_entity_slots(entity_id: uuid.UUID, data: List) -> None:
    """Set entity slots list in cache (L2 only)."""
    key = str(entity_id)
    if settings.l2_caching:
        get_cache_service().set(f"slots:{key}", data, settings.cache_entity_ttl)


# ---------------------------------------------------------------------------
# Invalidation (all 3 keys)
# ---------------------------------------------------------------------------

def invalidate_entity(entity_id: uuid.UUID) -> None:
    """Invalidate all entity-related cache entries for a single entity (L2 only).

    Clears entity:, params:, and slots: keys for the given entity_id.
    """
    key = str(entity_id)
    if settings.l2_caching:
        svc = get_cache_service()
        svc.delete(f"entity:{key}")
        svc.delete(f"params:{key}")
        svc.delete(f"slots:{key}")


# ---------------------------------------------------------------------------
# Bulk clear helper
# ---------------------------------------------------------------------------

def clear_all_entity_related_caches() -> None:
    """Clear all entity-related L2 patterns.

    This is used by project_templates.py for project-wide template changes.
    """
    if settings.l2_caching:
        svc = get_cache_service()
        svc.delete_pattern("entity:*")
        svc.delete_pattern("params:*")
        svc.delete_pattern("slots:*")
