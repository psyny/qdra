import uuid
from typing import Optional

from sqlalchemy.orm import Session

from models.user_app_permissions import UserAppPermissions


class UserAppPermissionsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserAppPermissions]:
        """Get app permissions for a user."""
        return self.db.query(UserAppPermissions).filter(UserAppPermissions.user_id == user_id).first()

    def create(
        self,
        user_id: uuid.UUID,
        can_manage_users: bool = False,
        can_create_projects: bool = False,
        can_edit_projects: bool = False,
        can_delete_projects: bool = False,
        can_create_templates: bool = False,
        can_edit_templates: bool = False,
        can_delete_templates: bool = False,
    ) -> UserAppPermissions:
        """Create app permissions for a user."""
        permissions = UserAppPermissions(
            user_id=user_id,
            can_manage_users=can_manage_users,
            can_create_projects=can_create_projects,
            can_edit_projects=can_edit_projects,
            can_delete_projects=can_delete_projects,
            can_create_templates=can_create_templates,
            can_edit_templates=can_edit_templates,
            can_delete_templates=can_delete_templates,
        )
        self.db.add(permissions)
        self.db.commit()
        self.db.refresh(permissions)
        return permissions

    def update(
        self,
        user_id: uuid.UUID,
        can_manage_users: Optional[bool] = None,
        can_create_projects: Optional[bool] = None,
        can_edit_projects: Optional[bool] = None,
        can_delete_projects: Optional[bool] = None,
        can_create_templates: Optional[bool] = None,
        can_edit_templates: Optional[bool] = None,
        can_delete_templates: Optional[bool] = None,
    ) -> Optional[UserAppPermissions]:
        """Update app permissions for a user."""
        permissions = self.get_by_user_id(user_id)
        if not permissions:
            return None

        if can_manage_users is not None:
            permissions.can_manage_users = can_manage_users
        if can_create_projects is not None:
            permissions.can_create_projects = can_create_projects
        if can_edit_projects is not None:
            permissions.can_edit_projects = can_edit_projects
        if can_delete_projects is not None:
            permissions.can_delete_projects = can_delete_projects
        if can_create_templates is not None:
            permissions.can_create_templates = can_create_templates
        if can_edit_templates is not None:
            permissions.can_edit_templates = can_edit_templates
        if can_delete_templates is not None:
            permissions.can_delete_templates = can_delete_templates

        self.db.commit()
        self.db.refresh(permissions)
        return permissions

    def ensure_exists(self, user_id: uuid.UUID) -> UserAppPermissions:
        """Ensure a user has app permissions row, creating with defaults if missing."""
        permissions = self.get_by_user_id(user_id)
        if not permissions:
            permissions = self.create(user_id)
        return permissions
