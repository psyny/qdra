# Test Philosophy

## Overview

Qdra uses a three-tier testing strategy to ensure code quality and system reliability. Tests are organized by type and each component follows a consistent structure.

---

## Test Types

### Unit Tests

**Definition**: Tests that run in isolation without external dependencies.

**Requirements**:
- No containers required
- No database required
- No external services required
- Only minimal local setup needed (e.g., Python venv)

**Purpose**: Verify individual functions, classes, and modules work correctly in isolation.

**Execution**: Run from local development environment with minimal dependencies.

---

### Integration Tests

**Definition**: Tests that verify multiple components work together.

**Requirements**:
- Container ecosystem must be running (docker-compose)
- Database and other services accessible
- Tests interact with real external systems

**Purpose**: Verify that components integrate correctly and that the system behaves as expected when connected to real services.

**Execution**: Run against running Docker containers.

---

### End-to-End (E2E) Tests

**Definition**: Tests that verify the entire system flow from user perspective.

**Requirements**:
- Container ecosystem must be running
- Full system stack deployed
- Tests simulate real user workflows

**Purpose**: Verify complete user journeys and system behavior end-to-end.

**Execution**: Run against fully deployed system.

---

## Test Organization

Each component's test directory should follow this structure:

```text
tests/
  unit/           # Unit tests (no external dependencies)
  integration/    # Integration tests (containers required)
  e2e/            # End-to-end tests (full system required)
```

---

## Component-Specific Guidelines

### Python Backend

#### Unit Tests

**Setup**:
- Create Python virtual environment in component directory
- Install dependencies into venv
- Run tests from venv

**Execution**:
```bash
cd backend/qdra
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
pytest tests/unit/ -v
```

**What to test**:
- Pure functions (e.g., constraint matcher logic)
- Service layer business logic with mocked repositories
- Repository layer with mocked database sessions
- Schema validation
- Utility functions

#### Integration Tests

**Setup**:
- Start Docker containers: `docker-compose up -d`
- Run migrations
- Execute tests

**Execution**:
```bash
docker-compose up -d postgres redis
# Run migrations
cd backend/qdra
pytest tests/integration/ -v
```

**What to test**:
- API endpoints with real database
- Database operations
- Service layer with real repositories
- Multi-component interactions

#### E2E Tests

**Setup**:
- Start full Docker stack: `docker-compose up -d`
- Run migrations
- Execute tests

**Execution**:
```bash
docker-compose up -d
# Run migrations
cd backend/qdra
pytest tests/e2e/ -v
```

**What to test**:
- Complete user workflows
- API-to-database-to-API flows
- Error handling across system boundaries
- Performance characteristics

---

### Frontend

#### Unit Tests

**TODO**: Define frontend unit test strategy and tooling.

**Setup**: (To be defined)

**Execution**: (To be defined)

#### Integration Tests

**TODO**: Define frontend integration test strategy.

**Setup**: (To be defined)

**Execution**: (To be defined)

#### E2E Tests

**TODO**: Define frontend E2E test strategy (likely Playwright or Cypress).

**Setup**: (To be defined)

**Execution**: (To be defined)

---

### Other Components

#### Graph Worker

**TODO**: Define graph worker test strategy.

#### Infrastructure

**TODO**: Define infrastructure test strategy (Docker compose validation, etc.).

---

## Test Database Strategy

### Unit Tests
- Use in-memory databases or mocks
- No persistent storage required

### Integration Tests
- Use dedicated test database
- Clean database between test runs
- Can use Docker Postgres or local Postgres

### E2E Tests
- Use same database as development/staging
- Test data should be representative of production
- Clean up after test runs

---

## Running Tests

### Quick Development Loop (Unit Tests Only)
```bash
# Backend
cd backend/qdra
source venv/bin/activate
pytest tests/unit/ -v
```

### Full Test Suite (All Types)
```bash
# Start containers
docker-compose up -d

# Run all tests
pytest tests/ -v
```

### CI/CD Pipeline
1. Run unit tests (fast, no dependencies)
2. If passing, start containers and run integration tests
3. If passing, run E2E tests against deployed environment

---

## Naming Conventions

- Unit test files: `test_<module>_unit.py` or place in `tests/unit/`
- Integration test files: `test_<module>_integration.py` or place in `tests/integration/`
- E2E test files: `test_<workflow>_e2e.py` or place in `tests/e2e/`

---

## Current Status

### Backend
- [x] Unit test structure defined
- [x] Integration test structure defined
- [ ] E2E test structure defined
- [ ] Venv setup documented
- [ ] Test database automation

### Frontend
- [ ] Unit test strategy defined
- [ ] Integration test strategy defined
- [ ] E2E test strategy defined

### Other Components
- [ ] Graph worker test strategy
- [ ] Infrastructure test strategy
