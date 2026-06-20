.PHONY: up down build logs restart clean help
.PHONY: be-venv be-install be-qdra-tests-unit be-qdra-tests-integration be-qdra-tests-all

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Docker / Infrastructure Commands
# ============================================================================

up: ## Start all services
	docker-compose up -d
	@echo ""
	@echo "Services started. Click here to access the frontend: http://localhost:3000"
	@echo ""

prepare: ## Prepare the application (run migrations after up)
	@echo "Running database migrations..."
	docker exec qdra-backend-api-1 sh -c "cd qdra && alembic upgrade head"

down: ## Stop all services
	docker-compose down

build: ## Build all services
	docker-compose build

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show logs from backend-api
	docker-compose logs -f backend-api

logs-worker: ## Show logs from graph-worker
	docker-compose logs -f graph-worker

restart-soft: ## Soft restart (down, up, prepare)
	$(MAKE) down
	$(MAKE) up
	$(MAKE) prepare

restart-hard: ## Hard restart (down, rebuild, up, prepare)
	$(MAKE) down
	$(MAKE) rebuild
	$(MAKE) up
	$(MAKE) prepare

clean: ## Stop and remove all containers, volumes, and networks
	docker-compose down -v

rebuild: ## Rebuild all services
	docker-compose build

ps: ## Show running containers
	docker-compose ps

db-reset: ## Drop and recreate main database
	docker-compose up -d postgres
	@echo "Waiting for Postgres to be ready..."
	@sleep 3
	docker exec qdra-postgres-1 psql -U qdra -d postgres -c "DROP DATABASE IF EXISTS qdra;"
	docker exec qdra-postgres-1 psql -U qdra -d postgres -c "CREATE DATABASE qdra;"
	@echo "Main database reset"

db-reset-test: ## Drop and recreate test database
	docker-compose up -d postgres
	@echo "Waiting for Postgres to be ready..."
	@sleep 3
	docker exec qdra-postgres-1 psql -U qdra -d postgres -c "DROP DATABASE IF EXISTS qdra_test;"
	docker exec qdra-postgres-1 psql -U qdra -d postgres -c "CREATE DATABASE qdra_test;"
	@echo "Test database reset"

db-reset-all: ## Drop and recreate both main and test databases
	$(MAKE) db-reset
	$(MAKE) db-reset-test

db-check-structure: ## Check current database structure via API
	@echo "Fetching database structure..."
	@curl -s http://localhost:8000/api/schema | $(BE_PYTHON) -m json.tool

# ============================================================================
# Backend (Qdra) Commands
# ============================================================================

BE_DIR := backend
BE_SRC_DIR := $(BE_DIR)/qdra
BE_VENV := $(BE_DIR)/venv
BE_PYTHON := $(BE_VENV)/bin/python
BE_PIP := $(BE_VENV)/bin/pip
BE_PYTEST := $(BE_VENV)/bin/pytest

be-venv: ## Create Python virtual environment for backend
	python3 -m venv $(BE_VENV)
	@echo "Virtual environment created at $(BE_VENV)"

be-install: ## Install backend dependencies into venv (creates venv if needed)
	@if [ ! -d "$(BE_VENV)" ]; then \
		echo "Virtual environment not found, creating..."; \
		python3 -m venv $(BE_VENV); \
	fi
	$(BE_PIP) install --upgrade pip
	$(BE_PIP) install -e "$(BE_DIR)[dev]"
	@echo "Backend dependencies installed"

# Unit tests require venv with dependencies installed
# Usage: make be-qdra-tests-unit TARGET=tests/unit/test_materials.py
be-qdra-tests-unit: ## Run backend unit tests (no external dependencies). Optional: TARGET=path/to/test
	@echo "Running unit tests..."
	@echo "Note: Requires venv with dependencies installed"
	@echo "Run 'make be-install' first if needed"
	@if [ -z "$(TARGET)" ]; then \
		$(BE_PYTEST) $(BE_SRC_DIR)/tests/unit/ -v; \
	else \
		$(BE_PYTEST) $(BE_SRC_DIR)/tests/$(TARGET) -v -s; \
	fi

# Integration tests require Docker Postgres running
# Usage: make be-qdra-tests-integration TARGET=integration/test_output_solver.py
be-qdra-tests-integration: be-install ## Run backend integration tests (requires Docker). Optional: TARGET=path/to/test
	@echo "Running integration tests..."
	@echo "Loading environment variables from $(BE_DIR)/.env..."
	@if [ -f $(BE_DIR)/.env ]; then \
		set -a && . $(BE_DIR)/.env && set +a; \
	fi
	@echo "Checking if Postgres is accessible..."
	@docker exec qdra-postgres-1 psql -U qdra -c "SELECT 1;" > /dev/null 2>&1 || (echo "ERROR: Postgres is not accessible. Run 'make up' to start Docker services." && exit 1)
	@echo "Creating test database..."
	docker exec qdra-postgres-1 psql -U qdra -c "CREATE DATABASE qdra_test;" || echo "Database may already exist"
	@echo "Running migrations on test database..."
	cd $(BE_DIR)/qdra && DATABASE_URL="postgresql+psycopg2://qdra:qdra@localhost:5432/qdra_test" ../venv/bin/python -m alembic upgrade head
	@echo "Running integration tests..."
	@if [ -z "$(TARGET)" ]; then \
		DATABASE_URL="postgresql+psycopg2://qdra:qdra@localhost:5432/qdra_test" $(BE_PYTEST) $(BE_SRC_DIR)/tests/integration/ -v; \
	else \
		DATABASE_URL="postgresql+psycopg2://qdra:qdra@localhost:5432/qdra_test" $(BE_PYTEST) $(BE_SRC_DIR)/tests/$(TARGET) -v -s; \
	fi



# ============================================================================
# Frontend Commands (TODO)
# ============================================================================

# fe-venv: ## Create Node environment for frontend
# fe-install: ## Install frontend dependencies
# fe-tests-unit: ## Run frontend unit tests
# fe-tests-integration: ## Run frontend integration tests
# fe-tests-all: ## Run all frontend tests
