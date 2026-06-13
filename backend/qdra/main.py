from fastapi import FastAPI

from api.health import router as health_router
from api.projects import router as projects_router
from api.materials import router as materials_router
from api.recipes import router as recipes_router

app = FastAPI(title="Qdra")

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(materials_router)
app.include_router(recipes_router)
