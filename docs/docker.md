# Docker Services

## frontend
- **Responsibility**: Serves the React/Vite web UI
- **Tech**: Nginx static file server
- **Port**: 3000
- **Depends on**: backend-api

## backend-api
- **Responsibility**: Main application API handling CRUD and job creation
- **Tech**: FastAPI
- **Port**: 8000
- **Depends on**: postgres, redis
- **Key rule**: Never executes graph reasoning directly; delegates to worker via queue

## graph-worker
- **Responsibility**: Executes slow graph reasoning asynchronously
- **Tech**: Python async worker
- **Depends on**: postgres, redis
- **Consumes**: Redis queue `graph_reasoning_jobs`

## postgres
- **Responsibility**: Primary persistent storage
- **Tech**: PostgreSQL 16
- **Port**: 5432
- **Isolation**: All project-scoped tables include `project_id` foreign key

## redis
- **Responsibility**: Queue and lightweight cache
- **Tech**: Redis 7
- **Port**: 6379
- **Usage**: Graph reasoning job queue, temporary state

## Database Migrations

### Manual Migration Commands

Run migrations manually in local Docker:

```bash
docker compose exec backend-api sh -c "cd /app/qdra && alembic upgrade head"
```

Or using the migration script:

```bash
docker compose exec backend-api python scripts/run_migrations.py
```

### Automatic Migrations on Startup

The API service can run migrations automatically on startup by setting:

```bash
RUN_MIGRATIONS_ON_STARTUP=true
```

This is controlled by the entrypoint script at `backend/docker/api-entrypoint.sh`. Default behavior is `false` for safety.

### Railway Deployment Options

**Option A — API runs migrations on startup:**
Set in Railway API service environment:
```bash
RUN_MIGRATIONS_ON_STARTUP=true
```

**Option B — Dedicated migration service:**
Create a separate Railway service that runs:
```bash
python scripts/run_migrations.py
```
