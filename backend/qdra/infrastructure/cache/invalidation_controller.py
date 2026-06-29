"""Centralized cache invalidation controller.

This module provides a single source of truth for cache invalidation logic.
All cache invalidations should go through this controller, not directly to cache modules.
"""
import uuid
from typing import List

from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.relationship_cache import clear_pattern
from qdra.infrastructure.cache.entity_cache import invalidate_entity
from qdra.infrastructure.cache.permission_cache import (
    invalidate_app_permissions,
    invalidate_project_permissions,
    invalidate_all_user_permissions,
)
from qdra.infrastructure.cache.constraint_cache import (
    invalidate_constraint_resolution,
)


# ---------------------------------------------------------------------------
# Entity Events
# ---------------------------------------------------------------------------

def entities_added(entity_ids: List[uuid.UUID], project_id: uuid.UUID) -> None:
    """Invalidate caches when entities are created (Case #1).
    
    This invalidates:
    - Material↔Recipe Relationship Caches (L2)
    - Constraint Resolution Cache (L2)
    
    Note: Does NOT invalidate entity cache (new entities aren't cached yet).
    
    Args:
        entity_ids: List of entity IDs that were created
        project_id: Project ID where entities were created
    """
    if settings.l2_caching:
        clear_pattern(str(project_id))


def entities_changed(entity_ids: List[uuid.UUID], project_id: uuid.UUID) -> None:
    """Invalidate caches when entities are changed (Case #2).
    
    This is called when entities are edited, deleted, or when their
    parameters/slots are modified.
    
    This invalidates:
    - All caches from entities_added() (Relationship + Constraint caches)
    - Plus: Specific entity caches for each entity_id
    
    Args:
        entity_ids: List of entity IDs that were changed
        project_id: Project ID where entities were changed
    """
    # Invalidate relationship and constraint caches
    if settings.l2_caching:
        clear_pattern(str(project_id))
    
    # Invalidate specific entity caches
    for entity_id in entity_ids:
        invalidate_entity(entity_id)


# ---------------------------------------------------------------------------
# Permission Events
# ---------------------------------------------------------------------------

def user_permissions_changed(user_id: uuid.UUID) -> None:
    """Invalidate all permission caches for a user."""
    invalidate_all_user_permissions(user_id)


def project_permissions_changed(user_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Invalidate project permissions for a user."""
    invalidate_project_permissions(user_id, project_id)


# ---------------------------------------------------------------------------
# Constraint Events
# ---------------------------------------------------------------------------

def constraint_resolution_changed(project_id: uuid.UUID) -> None:
    """Invalidate constraint resolution caches for a project."""
    invalidate_constraint_resolution(project_id)
