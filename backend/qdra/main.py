from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdra.infrastructure.db.session import engine
from qdra.infrastructure.db.init_db import init_db
from qdra.api.routes import projects, schemas, objects, relationships, reasoning_jobs
import asyncio

app = FastAPI(title="Qdra API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(schemas.router, prefix="/projects/{project_id}/types", tags=["schemas"])
app.include_router(objects.router, prefix="/projects/{project_id}/objects", tags=["objects"])
app.include_router(relationships.router, prefix="/projects/{project_id}/relationships", tags=["relationships"])
app.include_router(reasoning_jobs.router, prefix="/projects/{project_id}/reasoning-jobs", tags=["reasoning-jobs"])


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: init_db(conn))


@app.get("/")
async def root():
    return {"message": "Qdra API"}
