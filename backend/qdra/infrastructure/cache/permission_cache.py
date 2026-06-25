"""Permission cache for user app and project permissions with L1/L2 caching."""
import uuid
from typing import Any, Optional
from cachetools import TTLCache
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.cache_service import get_cache_service

# Module-level L1 caches for permission operations
_app_permissions_cache = None
_project_permissions_cache = None


def get_app_permissions_cache():
    """Get or create the app permissions L1 cache."""
    global _app_permissions_cache
    if _app_permissions_cache is None:
        _app_permissions_cache = TTLCache(maxsize=settings.cache_permission_size, ttl=settings.cache_permission_ttl)
    return _app_permissions_cache


def get_project_permissions_cache():
    """Get or create the project permissions L1 cache."""
    global _project_permissions_cache
    if _project_permissions_cache is None:
        _project_permissions_cache = TTLCache(maxsize=settings.cache_permission_project_size, ttl=settings.cache_permission_ttl)
    return _project_permissions_cache


def clear_all_permission_caches():
    """Clear all permission L1 caches."""
    global _app_permissions_cache, _project_permissions_cache
    if _app_permissions_cache is not None:
        _app_permissions_cache.clear()
    if _project_permissions_cache is not None:
        _project_permissions_cache.clear()


def get_app_permissions(user_id: uuid.UUID) -> Optional[dict]:
    """Get app permissions from cache (L1 then L2)."""
    key = str(user_id)
    
    # Try L1 cache if enabled
    if settings.l1_caching:
        cache = get_app_permissions_cache()
        cached = cache.get(key)
        if cached is not None:
            return cached
    
    # Try L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"app_permissions:{key}"
        cached = cache_service.get(l2_key)
        if cached is not None:
            return cached
    
    return None


def set_app_permissions(user_id: uuid.UUID, permissions: dict) -> None:
    """Set app permissions in cache (L1 and L2)."""
    key = str(user_id)
    
    # Set L1 cache if enabled
    if settings.l1_caching:
        cache = get_app_permissions_cache()
        cache[key] = permissions
    
    # Set L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"app_permissions:{key}"
        cache_service.set(l2_key, permissions, settings.cache_permission_ttl)


def invalidate_app_permissions(user_id: uuid.UUID) -> None:
    """Invalidate app permissions for a user from both L1 and L2 caches."""
    key = str(user_id)
    
    # Clear from L1
    if settings.l1_caching:
        cache = get_app_permissions_cache()
        cache.pop(key, None)
    
    # Clear from L2
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"app_permissions:{key}"
        cache_service.delete(l2_key)


def get_project_permissions(user_id: uuid.UUID, project_id: uuid.UUID) -> Optional[dict]:
    """Get project permissions from cache (L1 then L2)."""
    key = f"{user_id}:{project_id}"
    
    # Try L1 cache if enabled
    if settings.l1_caching:
        cache = get_project_permissions_cache()
        cached = cache.get(key)
        if cached is not None:
            return cached
    
    # Try L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"project_permissions:{key}"
        cached = cache_service.get(l2_key)
        if cached is not None:
            return cached
    
    return None


def set_project_permissions(user_id: uuid.UUID, project_id: uuid.UUID, permissions: dict) -> None:
    """Set project permissions in cache (L1 and L2)."""
    key = f"{user_id}:{project_id}"
    
    # Set L1 cache if enabled
    if settings.l1_caching:
        cache = get_project_permissions_cache()
        cache[key] = permissions
    
    # Set L2 cache if enabled
    if settings.l2_caching:
        cache_service = get_cache_service()
        l2_key = f"project_permissions:{key}"
        cache_service.set(l2_key, permissions, settings.cache_permission_ttl)


def invalidate_project_permissions(user_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Invalidate project permissions for a user/project from both L1 and L2 caches."""
    key = f"{user_id}:{project_id}"
    
    # Clear from L1
    if settings.l1_caching:
        cache = get_project_permissions_cache()
        cache.pop(key, None)
    
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
        cache_service.delete_pattern(f"project_permissions:{user_id}:*")
    
    # Clear all project permissions from L1 (brute force since TTLCache doesn't support pattern matching)
    if settings.l1_caching:
        cache = get_project_permissions_cache()
        keys_to_delete = [k for k in cache.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_delete:
            cache.pop(key, None)
