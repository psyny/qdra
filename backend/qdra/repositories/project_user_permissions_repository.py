import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.project_user_permissions import ProjectUserPermissions


class ProjectUserPermissionsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_project(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Optional[ProjectUserPermissions]:
        """Get project permissions for a specific user and project."""
        return self.db.query(ProjectUserPermissions).filter(
            ProjectUserPermissions.user_id == user_id,
            ProjectUserPermissions.project_id == project_id
        ).first()

    def list_by_project(self, project_id: uuid.UUID) -> List[ProjectUserPermissions]:
        """List all permissions for a project."""
        return self.db.query(ProjectUserPermissions).filter(
            ProjectUserPermissions.project_id == project_id
        ).all()

    def list_by_user(self, user_id: uuid.UUID) -> List[ProjectUserPermissions]:
        """List all projects a user has permissions for."""
        return self.db.query(ProjectUserPermissions).filter(
            ProjectUserPermissions.user_id == user_id
        ).all()

    def create(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        can_access: bool = False,
        can_manage_project_users: bool = False,
        can_create_material: bool = False,
        can_edit_material: bool = False,
        can_delete_material: bool = False,
        can_create_recipe: bool = False,
        can_edit_recipe: bool = False,
        can_delete_recipe: bool = False,
        can_run_plan: bool = False,
    ) -> ProjectUserPermissions:
        """Create project permissions for a user."""
        permissions = ProjectUserPermissions(
            user_id=user_id,
            project_id=project_id,
            can_access=can_access,
            can_manage_project_users=can_manage_project_users,
            can_create_material=can_create_material,
            can_edit_material=can_edit_material,
            can_delete_material=can_delete_material,
            can_create_recipe=can_create_recipe,
            can_edit_recipe=can_edit_recipe,
            can_delete_recipe=can_delete_recipe,
            can_run_plan=can_run_plan,
        )
        self.db.add(permissions)
        self.db.commit()
        self.db.refresh(permissions)
        return permissions

    def update(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        can_access: Optional[bool] = None,
        can_manage_project_users: Optional[bool] = None,
        can_create_material: Optional[bool] = None,
        can_edit_material: Optional[bool] = None,
        can_delete_material: Optional[bool] = None,
        can_create_recipe: Optional[bool] = None,
        can_edit_recipe: Optional[bool] = None,
        can_delete_recipe: Optional[bool] = None,
        can_run_plan: Optional[bool] = None,
    ) -> Optional[ProjectUserPermissions]:
        """Update project permissions for a user."""
        permissions = self.get_by_user_and_project(user_id, project_id)
        if not permissions:
            return None

        if can_access is not None:
            permissions.can_access = can_access
        if can_manage_project_users is not None:
            permissions.can_manage_project_users = can_manage_project_users
        if can_create_material is not None:
            permissions.can_create_material = can_create_material
        if can_edit_material is not None:
            permissions.can_edit_material = can_edit_material
        if can_delete_material is not None:
            permissions.can_delete_material = can_delete_material
        if can_create_recipe is not None:
            permissions.can_create_recipe = can_create_recipe
        if can_edit_recipe is not None:
            permissions.can_edit_recipe = can_edit_recipe
        if can_delete_recipe is not None:
            permissions.can_delete_recipe = can_delete_recipe
        if can_run_plan is not None:
            permissions.can_run_plan = can_run_plan

        self.db.commit()
        self.db.refresh(permissions)
        return permissions

    def upsert(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        can_access: Optional[bool] = None,
        can_manage_project_users: Optional[bool] = None,
        can_create_material: Optional[bool] = None,
        can_edit_material: Optional[bool] = None,
        can_delete_material: Optional[bool] = None,
        can_create_recipe: Optional[bool] = None,
        can_edit_recipe: Optional[bool] = None,
        can_delete_recipe: Optional[bool] = None,
        can_run_plan: Optional[bool] = None,
    ) -> ProjectUserPermissions:
        """Create or update project permissions for a user."""
        permissions = self.get_by_user_and_project(user_id, project_id)
        
        if permissions:
            # Update existing
            if can_access is not None:
                permissions.can_access = can_access
            if can_manage_project_users is not None:
                permissions.can_manage_project_users = can_manage_project_users
            if can_create_material is not None:
                permissions.can_create_material = can_create_material
            if can_edit_material is not None:
                permissions.can_edit_material = can_edit_material
            if can_delete_material is not None:
                permissions.can_delete_material = can_delete_material
            if can_create_recipe is not None:
                permissions.can_create_recipe = can_create_recipe
            if can_edit_recipe is not None:
                permissions.can_edit_recipe = can_edit_recipe
            if can_delete_recipe is not None:
                permissions.can_delete_recipe = can_delete_recipe
            if can_run_plan is not None:
                permissions.can_run_plan = can_run_plan
            self.db.commit()
            self.db.refresh(permissions)
            return permissions
        else:
            # Create new with provided values or defaults
            return self.create(
                user_id=user_id,
                project_id=project_id,
                can_access=can_access or False,
                can_manage_project_users=can_manage_project_users or False,
                can_create_material=can_create_material or False,
                can_edit_material=can_edit_material or False,
                can_delete_material=can_delete_material or False,
                can_create_recipe=can_create_recipe or False,
                can_edit_recipe=can_edit_recipe or False,
                can_delete_recipe=can_delete_recipe or False,
                can_run_plan=can_run_plan or False,
            )

    def delete(self, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        """Remove a user from a project by deleting their permissions."""
        permissions = self.get_by_user_and_project(user_id, project_id)
        if not permissions:
            return False
        
        self.db.delete(permissions)
        self.db.commit()
        return True
