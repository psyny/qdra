import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from repositories.user_repository import UserRepository
from repositories.user_app_permissions_repository import UserAppPermissionsRepository
from repositories.project_user_permissions_repository import ProjectUserPermissionsRepository
from schemas.user_schemas import UserCreate, UserUpdate, UserRead, UserAppPermissionsUpdate, UserAppPermissionsRead, ProjectUserPermissionsUpdate, ProjectUserPermissionsRead
from models.user import User
from models.user_app_permissions import UserAppPermissions
from models.project_user_permissions import ProjectUserPermissions


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.app_perms_repo = UserAppPermissionsRepository(db)
        self.project_perms_repo = ProjectUserPermissionsRepository(db)

    def create_user(self, user_data: UserCreate) -> UserRead:
        """Create a new user with hashed password and app permissions.
        
        If this is the first user in the database, grant all app-level permissions.
        Otherwise, grant no app-level permissions.
        """
        # Check if this is the first user
        is_first_user = self.user_repo.count_all() == 0
        
        # Create the user
        user = self.user_repo.create(
            login_name=user_data.login_name,
            password=user_data.password,
            display_name=user_data.display_name,
        )
        
        # Create app permissions
        if is_first_user:
            # First user gets all permissions
            app_perms = self.app_perms_repo.create(
                user_id=user.id,
                can_manage_users=True,
                can_create_projects=True,
                can_edit_projects=True,
                can_delete_projects=True,
                can_create_templates=True,
                can_edit_templates=True,
                can_delete_templates=True,
            )
        else:
            # Subsequent users get no permissions
            app_perms = self.app_perms_repo.create(user_id=user.id)
        
        return UserRead.model_validate(user)

    def get_user(self, user_id: uuid.UUID) -> Optional[UserRead]:
        """Get a user by ID."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return UserRead.model_validate(user)

    def get_user_by_login_name(self, login_name: str) -> Optional[User]:
        """Get a user by login name (returns model with password hash for auth)."""
        return self.user_repo.get_by_login_name(login_name)

    def list_users(self, include_inactive: bool = False) -> List[UserRead]:
        """List all users."""
        users = self.user_repo.list_all(include_inactive=include_inactive)
        return [UserRead.model_validate(user) for user in users]

    def update_user(self, user_id: uuid.UUID, update_data: UserUpdate) -> Optional[UserRead]:
        """Update a user's fields."""
        user = self.user_repo.update(
            user_id=user_id,
            login_name=update_data.login_name,
            display_name=update_data.display_name,
            password=update_data.password,
            is_active=update_data.is_active,
        )
        if not user:
            return None
        return UserRead.model_validate(user)

    def deactivate_user(self, user_id: uuid.UUID) -> Optional[UserRead]:
        """Deactivate a user."""
        user = self.user_repo.deactivate(user_id)
        if not user:
            return None
        return UserRead.model_validate(user)

    def set_last_login_at(self, user_id: uuid.UUID, timestamp: datetime) -> None:
        """Set the last login timestamp for a user."""
        self.user_repo.set_last_login_at(user_id, timestamp)

    def get_app_permissions(self, user_id: uuid.UUID) -> UserAppPermissionsRead:
        """Get app-level permissions for a user."""
        perms = self.app_perms_repo.get_by_user_id(user_id)
        if not perms:
            # Ensure permissions row exists
            perms = self.app_perms_repo.ensure_exists(user_id)
        return UserAppPermissionsRead.model_validate(perms)

    def update_app_permissions(self, user_id: uuid.UUID, update_data: UserAppPermissionsUpdate) -> UserAppPermissionsRead:
        """Update app-level permissions for a user."""
        perms = self.app_perms_repo.update(
            user_id=user_id,
            can_manage_users=update_data.can_manage_users,
            can_create_projects=update_data.can_create_projects,
            can_edit_projects=update_data.can_edit_projects,
            can_delete_projects=update_data.can_delete_projects,
            can_create_templates=update_data.can_create_templates,
            can_edit_templates=update_data.can_edit_templates,
            can_delete_templates=update_data.can_delete_templates,
        )
        if not perms:
            # Create if doesn't exist
            perms = self.app_perms_repo.ensure_exists(user_id)
        return UserAppPermissionsRead.model_validate(perms)

    def ensure_app_permissions_row(self, user_id: uuid.UUID) -> UserAppPermissionsRead:
        """Ensure a user has an app permissions row."""
        perms = self.app_perms_repo.ensure_exists(user_id)
        return UserAppPermissionsRead.model_validate(perms)

    def get_project_permissions(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Optional[ProjectUserPermissionsRead]:
        """Get project permissions for a user."""
        perms = self.project_perms_repo.get_by_user_and_project(user_id, project_id)
        if not perms:
            return None
        return ProjectUserPermissionsRead.model_validate(perms)

    def list_project_users(self, project_id: uuid.UUID) -> List[ProjectUserPermissionsRead]:
        """List all users with permissions for a project."""
        perms = self.project_perms_repo.list_by_project(project_id)
        return [ProjectUserPermissionsRead.model_validate(p) for p in perms]

    def list_user_projects(self, user_id: uuid.UUID) -> List[ProjectUserPermissionsRead]:
        """List all projects a user has permissions for."""
        perms = self.project_perms_repo.list_by_user(user_id)
        return [ProjectUserPermissionsRead.model_validate(p) for p in perms]

    def upsert_project_permissions(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        update_data: ProjectUserPermissionsUpdate,
    ) -> ProjectUserPermissionsRead:
        """Create or update project permissions for a user."""
        perms = self.project_perms_repo.upsert(
            user_id=user_id,
            project_id=project_id,
            can_manage_project_users=update_data.can_manage_project_users,
            can_create_material=update_data.can_create_material,
            can_edit_material=update_data.can_edit_material,
            can_delete_material=update_data.can_delete_material,
            can_create_recipe=update_data.can_create_recipe,
            can_edit_recipe=update_data.can_edit_recipe,
            can_delete_recipe=update_data.can_delete_recipe,
            can_run_plan=update_data.can_run_plan,
        )
        return ProjectUserPermissionsRead.model_validate(perms)

    def remove_user_from_project(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        """Remove a user from a project by deleting their permissions."""
        self.project_perms_repo.delete(user_id, project_id)
