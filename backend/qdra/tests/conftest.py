# Root conftest.py - shared fixtures for all test types
# Integration-specific fixtures are in tests/integration/conftest.py
import os
import uuid
from typing import Generator, Dict, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from db.session import get_db
from main import app
from infrastructure.security.permission_checker import (
    get_current_user_id,
    require_can_create_material,
    require_can_edit_material,
    require_can_delete_material,
    require_can_create_recipe,
    require_can_edit_recipe,
    require_can_delete_recipe,
    require_can_run_plan,
    require_can_manage_project_users,
)
from repositories.project_user_permissions_repository import ProjectUserPermissionsRepository

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://qdra:qdra@localhost:5432/qdra_test",
).replace("+asyncpg", "")

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(scope="session", autouse=True)
def setup_test_user():
    """Create test user with the hardcoded TEST_USER_ID once per test session using raw SQL."""
    session = TestSessionLocal()
    try:
        result = session.execute(
            text("SELECT id FROM users WHERE id = :id"),
            {"id": str(TEST_USER_ID)}
        ).first()
        if not result:
            # Remove any conflicting user with the same login name
            session.execute(
                text("DELETE FROM users WHERE login_name = 'test_user'")
            )
            session.execute(
                text("""
                    INSERT INTO users (id, login_name, password_hash, display_name, is_active)
                    VALUES (:id, 'test_user', 'test_hash', 'Test User', true)
                """),
                {"id": str(TEST_USER_ID)}
            )
            session.commit()
    finally:
        session.close()
    yield


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_current_user_id():
        return TEST_USER_ID

    def override_require_permission():
        return TEST_USER_ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[require_can_create_material] = override_require_permission
    app.dependency_overrides[require_can_edit_material] = override_require_permission
    app.dependency_overrides[require_can_delete_material] = override_require_permission
    app.dependency_overrides[require_can_create_recipe] = override_require_permission
    app.dependency_overrides[require_can_edit_recipe] = override_require_permission
    app.dependency_overrides[require_can_delete_recipe] = override_require_permission
    app.dependency_overrides[require_can_run_plan] = override_require_permission
    app.dependency_overrides[require_can_manage_project_users] = override_require_permission

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def project_ctx(client: TestClient) -> Dict[str, Any]:
    """Create a project template with material+recipe entity types and a project."""
    tmpl = client.post("/api/project-templates", json={"name": "Test Template"}).json()
    tmpl_id = tmpl["id"]
    mat_type = client.post(
        f"/api/project-templates/{tmpl_id}/entity-types",
        json={"kind": "material", "name": "Material"},
    ).json()
    rec_type = client.post(
        f"/api/project-templates/{tmpl_id}/entity-types",
        json={"kind": "recipe", "name": "Recipe"},
    ).json()
    project = client.post(
        "/api/projects", json={"name": "Test Project", "project_template_id": tmpl_id}
    ).json()
    project_id = project["id"]

    # Use a separate committed session so the FK to TEST_USER_ID is always satisfied
    # (the test's db session rolls back at teardown, but the user must exist when inserting)
    perm_session = TestSessionLocal()
    try:
        perm_repo = ProjectUserPermissionsRepository(perm_session)
        perm_repo.upsert(
            user_id=TEST_USER_ID,
            project_id=project_id,
            can_manage_project_users=True,
            can_create_material=True,
            can_edit_material=True,
            can_delete_material=True,
            can_create_recipe=True,
            can_edit_recipe=True,
            can_delete_recipe=True,
            can_run_plan=True,
        )
        perm_session.commit()
    finally:
        perm_session.close()

    return {
        "project_id": project_id,
        "template_id": tmpl_id,
        "material_type_id": mat_type["id"],
        "recipe_type_id": rec_type["id"],
    }

