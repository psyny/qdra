import uuid
import pytest
from sqlalchemy.orm import Session

from services.user_service import UserService
from schemas.user_schemas import UserCreate, UserUpdate, UserAppPermissionsUpdate, ProjectUserPermissionsUpdate
from repositories.user_repository import UserRepository
from repositories.user_app_permissions_repository import UserAppPermissionsRepository
from repositories.project_user_permissions_repository import ProjectUserPermissionsRepository
from infrastructure.security.password_hasher import hash_password, verify_password


def test_create_user_hashes_password(db: Session):
    """Test that password is hashed when creating a user."""
    user_repo = UserRepository(db)
    user = user_repo.create(
        login_name="testuser",
        password="plainpassword",
        display_name="Test User",
    )
    
    # Password should not be stored as plain text
    assert user.password_hash != "plainpassword"
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password(db: Session):
    """Test password verification."""
    plain_password = "mypassword123"
    hashed = hash_password(plain_password)
    
    assert verify_password(plain_password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_user_duplicate_login_name(db: Session):
    """Test that duplicate login names are rejected."""
    user_repo = UserRepository(db)
    
    # Create first user
    user_repo.create(
        login_name="testuser",
        password="password1",
        display_name="Test User 1",
    )
    
    # Try to create duplicate
    with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
        user_repo.create(
            login_name="testuser",
            password="password2",
            display_name="Test User 2",
        )


def test_create_user_defaults_to_active(db: Session):
    """Test that new users default to is_active=True."""
    user_repo = UserRepository(db)
    user = user_repo.create(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    
    assert user.is_active is True


def test_update_user_display_name(db: Session):
    """Test updating user display name."""
    user_repo = UserRepository(db)
    user = user_repo.create(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    
    updated = user_repo.update(user.id, display_name="Updated Name")
    assert updated.display_name == "Updated Name"


def test_update_user_password(db: Session):
    """Test updating user password and rehashing."""
    user_repo = UserRepository(db)
    user = user_repo.create(
        login_name="testuser",
        password="oldpassword",
        display_name="Test User",
    )
    
    old_hash = user.password_hash
    updated = user_repo.update(user.id, password="newpassword")
    
    assert updated.password_hash != old_hash
    assert verify_password("newpassword", updated.password_hash) is True
    assert verify_password("oldpassword", updated.password_hash) is False


def test_deactivate_user(db: Session):
    """Test deactivating a user."""
    user_repo = UserRepository(db)
    user = user_repo.create(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    
    assert user.is_active is True
    
    deactivated = user_repo.deactivate(user.id)
    assert deactivated.is_active is False


def test_list_users_excludes_inactive(db: Session):
    """Test that list_users excludes inactive users by default."""
    user_repo = UserRepository(db)
    
    user1 = user_repo.create(
        login_name="user1",
        password="password",
        display_name="User 1",
    )
    user2 = user_repo.create(
        login_name="user2",
        password="password",
        display_name="User 2",
    )
    
    # Deactivate user2
    user_repo.deactivate(user2.id)
    
    active_users = user_repo.list_all(include_inactive=False)
    assert len(active_users) == 1
    assert active_users[0].id == user1.id
    
    all_users = user_repo.list_all(include_inactive=True)
    assert len(all_users) == 2


def test_first_user_gets_all_app_permissions(db: Session):
    """Test that the first user gets all app-level permissions."""
    user_service = UserService(db)
    
    # Create first user
    user_data = UserCreate(
        login_name="admin",
        password="password",
        display_name="Admin User",
    )
    user = user_service.create_user(user_data)
    
    # Check app permissions
    app_perms = user_service.get_app_permissions(user.id)
    
    assert app_perms.can_manage_users is True
    assert app_perms.can_create_projects is True
    assert app_perms.can_edit_projects is True
    assert app_perms.can_delete_projects is True
    assert app_perms.can_create_templates is True
    assert app_perms.can_edit_templates is True
    assert app_perms.can_delete_templates is True


def test_second_user_gets_no_app_permissions(db: Session):
    """Test that subsequent users get no app-level permissions."""
    user_service = UserService(db)
    
    # Create first user (admin)
    admin_data = UserCreate(
        login_name="admin",
        password="password",
        display_name="Admin User",
    )
    user_service.create_user(admin_data)
    
    # Create second user
    user_data = UserCreate(
        login_name="regular",
        password="password",
        display_name="Regular User",
    )
    user = user_service.create_user(user_data)
    
    # Check app permissions
    app_perms = user_service.get_app_permissions(user.id)
    
    assert app_perms.can_manage_users is False
    assert app_perms.can_create_projects is False
    assert app_perms.can_edit_projects is False
    assert app_perms.can_delete_projects is False
    assert app_perms.can_create_templates is False
    assert app_perms.can_edit_templates is False
    assert app_perms.can_delete_templates is False


def test_update_app_permissions(db: Session):
    """Test updating individual app permission flags."""
    user_service = UserService(db)
    
    # Create a user
    user_data = UserCreate(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    user = user_service.create_user(user_data)
    
    # Update some permissions
    update_data = UserAppPermissionsUpdate(
        can_create_projects=True,
        can_edit_projects=True,
    )
    updated = user_service.update_app_permissions(user.id, update_data)
    
    assert updated.can_create_projects is True
    assert updated.can_edit_projects is True
    assert updated.can_manage_users is False  # Should remain False


def test_create_project_permissions(db: Session):
    """Test creating project permissions for a user."""
    from repositories.project_repository import ProjectRepository
    from repositories.project_template_repository import ProjectTemplateRepository
    
    user_service = UserService(db)
    project_repo = ProjectRepository(db)
    template_repo = ProjectTemplateRepository(db)
    
    # Create a user
    user_data = UserCreate(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    user = user_service.create_user(user_data)
    
    # Create a template and project
    template = template_repo.create(name="Test Template")
    project = project_repo.create(name="Test Project", project_template_id=template.id)
    
    # Create project permissions
    perms_data = ProjectUserPermissionsUpdate(
        can_create_material=True,
        can_edit_material=True,
    )
    perms = user_service.upsert_project_permissions(user.id, project.id, perms_data)
    
    assert perms.user_id == user.id
    assert perms.project_id == project.id
    assert perms.can_create_material is True
    assert perms.can_edit_material is True
    assert perms.can_create_recipe is False  # Default


def test_cannot_create_duplicate_project_permissions(db: Session):
    """Test that duplicate (user_id, project_id) rows are prevented."""
    from repositories.project_repository import ProjectRepository
    from repositories.project_template_repository import ProjectTemplateRepository
    
    project_perms_repo = ProjectUserPermissionsRepository(db)
    user_repo = UserRepository(db)
    project_repo = ProjectRepository(db)
    template_repo = ProjectTemplateRepository(db)
    
    # Create user and project
    user = user_repo.create(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    template = template_repo.create(name="Test Template")
    project = project_repo.create(name="Test Project", project_template_id=template.id)
    
    # Create permissions
    project_perms_repo.create(user.id, project.id, can_create_material=True)
    
    # Try to create duplicate - should fail or update
    with pytest.raises(Exception):
        project_perms_repo.create(user.id, project.id, can_create_recipe=True)


def test_upsert_project_permissions(db: Session):
    """Test that upsert creates or updates as needed."""
    from repositories.project_repository import ProjectRepository
    from repositories.project_template_repository import ProjectTemplateRepository
    
    user_service = UserService(db)
    project_repo = ProjectRepository(db)
    template_repo = ProjectTemplateRepository(db)
    
    # Create user and project
    user_data = UserCreate(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    user = user_service.create_user(user_data)
    template = template_repo.create(name="Test Template")
    project = project_repo.create(name="Test Project", project_template_id=template.id)
    
    # Upsert to create
    perms_data = ProjectUserPermissionsUpdate(can_create_material=True)
    perms = user_service.upsert_project_permissions(user.id, project.id, perms_data)
    assert perms.can_create_material is True
    
    # Upsert to update
    perms_data = ProjectUserPermissionsUpdate(can_create_material=False, can_edit_material=True)
    perms = user_service.upsert_project_permissions(user.id, project.id, perms_data)
    assert perms.can_create_material is False
    assert perms.can_edit_material is True


def test_list_project_users(db: Session):
    """Test listing users for a project."""
    from repositories.project_repository import ProjectRepository
    from repositories.project_template_repository import ProjectTemplateRepository
    
    user_service = UserService(db)
    project_repo = ProjectRepository(db)
    template_repo = ProjectTemplateRepository(db)
    
    # Create users and project
    user1_data = UserCreate(login_name="user1", password="password", display_name="User 1")
    user1 = user_service.create_user(user1_data)
    
    user2_data = UserCreate(login_name="user2", password="password", display_name="User 2")
    user2 = user_service.create_user(user2_data)
    
    template = template_repo.create(name="Test Template")
    project = project_repo.create(name="Test Project", project_template_id=template.id)
    
    # Add users to project
    user_service.upsert_project_permissions(user1.id, project.id, ProjectUserPermissionsUpdate(can_create_material=True))
    user_service.upsert_project_permissions(user2.id, project.id, ProjectUserPermissionsUpdate(can_edit_material=True))
    
    # List project users
    project_users = user_service.list_project_users(project.id)
    assert len(project_users) == 2
    
    user_ids = {u.user_id for u in project_users}
    assert user1.id in user_ids
    assert user2.id in user_ids


def test_list_user_projects(db: Session):
    """Test listing projects for a user."""
    from repositories.project_repository import ProjectRepository
    from repositories.project_template_repository import ProjectTemplateRepository
    
    user_service = UserService(db)
    project_repo = ProjectRepository(db)
    template_repo = ProjectTemplateRepository(db)
    
    # Create user and projects
    user_data = UserCreate(login_name="testuser", password="password", display_name="Test User")
    user = user_service.create_user(user_data)
    
    template = template_repo.create(name="Test Template")
    project1 = project_repo.create(name="Project 1", project_template_id=template.id)
    project2 = project_repo.create(name="Project 2", project_template_id=template.id)
    
    # Add user to projects
    user_service.upsert_project_permissions(user.id, project1.id, ProjectUserPermissionsUpdate(can_create_material=True))
    user_service.upsert_project_permissions(user.id, project2.id, ProjectUserPermissionsUpdate(can_edit_material=True))
    
    # List user projects
    user_projects = user_service.list_user_projects(user.id)
    assert len(user_projects) == 2
    
    project_ids = {p.project_id for p in user_projects}
    assert project1.id in project_ids
    assert project2.id in project_ids


def test_remove_user_from_project(db: Session):
    """Test removing a user from a project."""
    from repositories.project_repository import ProjectRepository
    from repositories.project_template_repository import ProjectTemplateRepository
    
    user_service = UserService(db)
    project_repo = ProjectRepository(db)
    template_repo = ProjectTemplateRepository(db)
    
    # Create user and project
    user_data = UserCreate(login_name="testuser", password="password", display_name="Test User")
    user = user_service.create_user(user_data)
    template = template_repo.create(name="Test Template")
    project = project_repo.create(name="Test Project", project_template_id=template.id)
    
    # Add user to project
    user_service.upsert_project_permissions(user.id, project.id, ProjectUserPermissionsUpdate(can_create_material=True))
    
    # Verify user is in project
    assert user_service.get_project_permissions(user.id, project.id) is not None
    
    # Remove user from project
    user_service.remove_user_from_project(user.id, project.id)
    
    # Verify user is removed
    assert user_service.get_project_permissions(user.id, project.id) is None


def test_ensure_app_permissions_row(db: Session):
    """Test that ensure_app_permissions_row creates row if missing."""
    app_perms_repo = UserAppPermissionsRepository(db)
    user_repo = UserRepository(db)
    
    # Create user without app permissions (manually)
    user = user_repo.create(
        login_name="testuser",
        password="password",
        display_name="Test User",
    )
    
    # Ensure permissions row exists
    perms = app_perms_repo.ensure_exists(user.id)
    
    assert perms is not None
    assert perms.user_id == user.id
    assert perms.can_manage_users is False  # Default
