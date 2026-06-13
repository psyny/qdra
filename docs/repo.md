# Repository Structure

This document describes the main folders in the Qdra repository and their purpose.

## Main Folders

### `backend/`
- **Goal**: Python-based backend services
  - `qdra/` - Main Qdra service (FastAPI server and graph reasoning worker)
  - (future be microservices will be added here)

### `frontend/`
- **Goal**: React/Vite web UI for interacting with the Qdra API

### `docs/`
- **Goal**: Project documentation for developers and users

### `notversioned/`
- **Goal**: Local-only documentation (gitignored) for development notes and internal planning

## Service Locations

| Service | Location | Entry Point |
|---------|----------|-------------|
| Frontend Web UI | `frontend/` | `src/main.tsx` |
| Backend API | `backend/qdra/` | `main.py` |
| Graph Worker | `backend/qdra/` | `worker.py` |
