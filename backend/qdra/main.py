from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.projects import router as projects_router
from api.materials import router as materials_router
from api.recipes import router as recipes_router
from api.output_solver import router as output_solver_router
from api.images import router as images_router
from api.project_templates import router as project_templates_router
from api.schema import router as schema_router
from api.entities import router as entities_router

app = FastAPI(title="Qdra")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(materials_router)
app.include_router(recipes_router)
app.include_router(output_solver_router)
app.include_router(images_router)
app.include_router(project_templates_router)
app.include_router(entities_router)
app.include_router(schema_router)
