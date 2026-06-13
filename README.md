# Qdra

Generic Graph Based Requirement System

## Architecture

This project implements a Docker-based microservices architecture for graph reasoning:

- **frontend**: React/Vite web UI served via Nginx
- **backend-api**: FastAPI application handling CRUD and job creation
- **graph-worker**: Async worker processing graph reasoning jobs
- **postgres**: PostgreSQL database with project-level isolation
- **redis**: Redis queue for job distribution

## Project Structure

```
qdra/
├── docker-compose.yml          # Orchestrate all services
├── frontend/                   # React/Vite web UI
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
├── backend/                    # Python backend
│   ├── Dockerfile.api          # API server image
│   ├── Dockerfile.worker       # Worker image
│   ├── pyproject.toml
│   └── qdra/
│       ├── main.py             # API entry point
│       ├── worker.py           # Worker entry point
│       ├── api/                # API routes
│       ├── domain/             # Business logic
│       └── infrastructure/     # DB, queue, config
└── notversioned/               # Local-only docs (gitignored)
```

## Quick Start

```bash
# Start all services
docker-compose up --build

# API will be available at http://localhost:8000
# Frontend at http://localhost:3000
```

## API Endpoints

- `POST /projects` - Create project
- `GET /projects` - List projects
- `POST /projects/{id}/types` - Create custom type
- `POST /projects/{id}/objects` - Create object
- `POST /projects/{id}/relationships` - Create relationship
- `POST /projects/{id}/reasoning-jobs` - Create reasoning job
- `GET /projects/{id}/reasoning-jobs/{job_id}` - Get job status
- `GET /projects/{id}/reasoning-jobs/{job_id}/result` - Get job result

## Development

Frontend TypeScript errors are expected until `npm install` is run in the frontend directory.
