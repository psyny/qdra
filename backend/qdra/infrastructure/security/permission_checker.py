import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from db.session import get_db
from infrastructure.security.jwt_handler import verify_token
from services.user_service import UserService


security = HTTPBearer()


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> uuid.UUID:
    """Extract user_id from JWT token."""
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user_id


def require_project_permission(permission_name: str):
    """Dependency factory to check if user has a specific project permission."""
    async def check_permission(
        user_id: uuid.UUID = Depends(get_current_user_id),
        project_id: uuid.UUID = None,
        db: Session = Depends(get_db)
    ) -> uuid.UUID:
        if project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id is required"
            )

        user_service = UserService(db)
        permissions = user_service.get_project_permissions(user_id, project_id)

        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project"
            )

        if not getattr(permissions, permission_name, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' is required"
            )

        return user_id

    return check_permission


def require_app_permission(permission_name: str):
    """Dependency factory to check if user has a specific app-level permission."""
    async def check_permission(
        user_id: uuid.UUID = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ) -> uuid.UUID:
        user_service = UserService(db)
        permissions = user_service.get_app_permissions(user_id)

        if not getattr(permissions, permission_name, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' is required"
            )

        return user_id

    return check_permission


# Convenience dependencies for common project permissions
require_can_create_material = require_project_permission("can_create_material")
require_can_edit_material = require_project_permission("can_edit_material")
require_can_delete_material = require_project_permission("can_delete_material")
require_can_create_recipe = require_project_permission("can_create_recipe")
require_can_edit_recipe = require_project_permission("can_edit_recipe")
require_can_delete_recipe = require_project_permission("can_delete_recipe")
require_can_run_plan = require_project_permission("can_run_plan")
require_can_manage_project_users = require_project_permission("can_manage_project_users")

# Convenience dependencies for common app permissions
require_can_manage_users = require_app_permission("can_manage_users")
require_can_create_projects = require_app_permission("can_create_projects")
require_can_edit_projects = require_app_permission("can_edit_projects")
require_can_delete_projects = require_app_permission("can_delete_projects")
require_can_create_templates = require_app_permission("can_create_templates")
require_can_edit_templates = require_app_permission("can_edit_templates")
require_can_delete_templates = require_app_permission("can_delete_templates")
