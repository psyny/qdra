"""Permission cache for user app and project permissions with L2 caching."""
import uuid
from typing import Any, Optional
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import get_cache_service



def get_app_permissions(user_id: uuid.UUID) -> Optional[dict]:
    """Get app permissions from cache (L2 only)."""
    key = str(user_id)
    
    # Try L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"app_permissions:{key}"
        cached = cache_service.get(l2_key)
        if cached is not None:
            return cached
    
    return None


def set_app_permissions(user_id: uuid.UUID, permissions: dict) -> None:
    """Set app permissions in cache (L2 only)."""
    key = str(user_id)
    
    # Set L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"app_permissions:{key}"
        cache_service.set(l2_key, permissions, settings.cache_permission_ttl)


def invalidate_app_permissions(user_id: uuid.UUID) -> None:
    """Invalidate app permissions for a user from L2 cache."""
    key = str(user_id)
    
    # Clear from L2
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"app_permissions:{key}"
        cache_service.delete(l2_key)


def get_project_permissions(user_id: uuid.UUID, project_id: uuid.UUID) -> Optional[dict]:
    """Get project permissions from cache (L2 only)."""
    key = f"{user_id}:{project_id}"
    
    # Try L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"project_permissions:{key}"
        cached = cache_service.get(l2_key)
        if cached is not None:
            return cached
    
    return None


def set_project_permissions(user_id: uuid.UUID, project_id: uuid.UUID, permissions: dict) -> None:
    """Set project permissions in cache (L2 only)."""
    key = f"{user_id}:{project_id}"
    
    # Set L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"project_permissions:{key}"
        cache_service.set(l2_key, permissions, settings.cache_permission_ttl)


def invalidate_project_permissions(user_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Invalidate project permissions for a user/project from L2 cache."""
    key = f"{user_id}:{project_id}"
    
    # Clear from L2
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"project_permissions:{key}"
        cache_service.delete(l2_key)


def invalidate_all_user_permissions(user_id: uuid.UUID) -> None:
    """Invalidate all permissions (app and project) for a user."""
    # Invalidate app permissions
    invalidate_app_permissions(user_id)
    
    # Invalidate all project permissions for the user from L2
    if settings.l2_caching:
        cache_service = get_cache_service()
        cache_service.delete_pattern(f"project_permissions:{user_id}:")
