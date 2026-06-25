"""Centralized cache invalidation controller.

This module provides a single source of truth for cache invalidation logic.
All cache invalidations should go through this controller, not directly to cache modules.
"""
import uuid
from typing import List

from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.relationship_cache import clear_all_caches, clear_pattern
from qdra.infrastructure.cache.entity_cache import invalidate_entity
from qdra.infrastructure.cache.permission_cache import (
    invalidate_app_permissions,
    invalidate_project_permissions,
    invalidate_all_user_permissions,
)
from qdra.infrastructure.cache.constraint_cache import (
    clear_all_constraint_caches,
    invalidate_constraint_resolution,
)


# ---------------------------------------------------------------------------
# Entity Events
# ---------------------------------------------------------------------------

def invalidate_entity(entity_id: uuid.UUID) -> None:
    """Invalidate a specific entity from cache.
    
    This is a low-level function for direct entity invalidation.
    For entity edits/deletes, prefer entities_edited() which also invalidates
    relationship and constraint caches.
    """
    from qdra.infrastructure.cache.entity_cache import invalidate_entity as cache_invalidate_entity
    cache_invalidate_entity(entity_id)


def entities_added(entity_ids: List[uuid.UUID]) -> None:
    """Invalidate all caches when entities are created.
    
    This invalidates:
    - Material↔Recipe Relationship Caches (L1 + L2)
    - Constraint Resolution Cache (L2)
    - Parameter value autocomplete cache (L1, via clear_all_caches)
    
    Note: Does NOT invalidate entity cache (new entities aren't cached yet).
    """
    if settings.l1_caching:
        clear_all_caches()
    if settings.l2_caching:
        # Get project_id from first entity (all entities in this call are in same project)
        # For now, we'll need the caller to handle project-level invalidation
        # or we can extend this to accept project_id
        pass


def entities_added_for_project(project_id: uuid.UUID) -> None:
    """Invalidate all caches when entities are created in a project.
    
    This is a convenience wrapper that accepts project_id directly.
    """
    if settings.l1_caching:
        clear_all_caches()
        clear_all_constraint_caches()
    if settings.l2_caching:
        clear_pattern(str(project_id))


def entities_edited(entity_ids: List[uuid.UUID], project_id: uuid.UUID) -> None:
    """Invalidate all caches when entities are edited or deleted.
    
    This invalidates:
    - All caches from entities_added()
    - Plus: Specific entity caches for each entity_id
    """
    # Invalidate relationship and constraint caches
    if settings.l1_caching:
        clear_all_caches()
        clear_all_constraint_caches()
    if settings.l2_caching:
        clear_pattern(str(project_id))
    
    # Invalidate specific entity caches
    for entity_id in entity_ids:
        invalidate_entity(entity_id)


# ---------------------------------------------------------------------------
# Recipe Events
# ---------------------------------------------------------------------------

def recipes_added(recipe_ids: List[uuid.UUID], project_id: uuid.UUID) -> None:
    """Invalidate all caches when recipes are created.
    
    Recipes are entities, so this uses the same invalidation as entities_added.
    """
    entities_added_for_project(project_id)


def recipes_edited(recipe_ids: List[uuid.UUID], project_id: uuid.UUID) -> None:
    """Invalidate all caches when recipes are edited or deleted.
    
    Recipes are entities, so this uses the same invalidation as entities_edited.
    """
    entities_edited(recipe_ids, project_id)


def recipe_slots_changed(recipe_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Invalidate caches when recipe slots are modified.
    
    This invalidates:
    - Material↔Recipe Relationship Caches (L1 + L2)
    - Constraint Resolution Cache (L1 + L2)
    """
    if settings.l1_caching:
        clear_all_caches()
        clear_all_constraint_caches()
    if settings.l2_caching:
        clear_pattern(str(project_id))


# ---------------------------------------------------------------------------
# Parameter Events
# ---------------------------------------------------------------------------

def entity_parameters_added(entity_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Invalidate caches when entity parameters are added.
    
    Same as entities_edited() for this entity.
    """
    entities_edited([entity_id], project_id)


def entity_parameters_deleted(entity_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Invalidate caches when entity parameters are deleted.
    
    Same as entities_edited() for this entity.
    """
    entities_edited([entity_id], project_id)


def recipe_parameters_changed(recipe_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Invalidate caches when recipe parameters are modified.
    
    Same as entities_edited() for this recipe.
    """
    entities_edited([recipe_id], project_id)


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
