# Root conftest.py - shared fixtures for all test types
# Integration-specific fixtures are in tests/integration/conftest.py
import os
from typing import Generator, Dict, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from qdra.db.session import get_db
from qdra.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://qdra:qdra@localhost:5432/qdra_test",
).replace("+asyncpg", "")

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def project_ctx(client: TestClient) -> Dict[str, Any]:
    """Create a project template with material+recipe entity types and a project."""
    tmpl = client.post("/project-templates", json={"name": "Test Template"}).json()
    tmpl_id = tmpl["id"]
    mat_type = client.post(
        f"/project-templates/{tmpl_id}/entity-types",
        json={"kind": "material", "name": "Material"},
    ).json()
    rec_type = client.post(
        f"/project-templates/{tmpl_id}/entity-types",
        json={"kind": "recipe", "name": "Recipe"},
    ).json()
    project = client.post(
        "/projects", json={"name": "Test Project", "project_template_id": tmpl_id}
    ).json()
    return {
        "project_id": project["id"],
        "template_id": tmpl_id,
        "material_type_id": mat_type["id"],
        "recipe_type_id": rec_type["id"],
    }

