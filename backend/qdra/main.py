from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.session import get_db
from models.user import User
from qdra.api.health import router as health_router
from qdra.api.projects import router as projects_router
from qdra.api.materials import router as materials_router
from qdra.api.recipes import router as recipes_router
from qdra.api.output_solver import router as output_solver_router
from qdra.api.images import router as images_router
from qdra.api.project_templates import router as project_templates_router
from qdra.api.schema import router as schema_router
from qdra.api.entities import router as entities_router
from qdra.api.planning_runs import router as planning_runs_router
from qdra.api.auth import router as auth_router
from qdra.api.users import router as users_router

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
app.include_router(planning_runs_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    try:
        user_count = db.query(User).count()
        users = db.query(User.login_name).limit(10).all()
        login_names = [u[0] for u in users]
        
        print(f"UsersRegistered: {user_count}")
        print(login_names)
    finally:
        db.close()
