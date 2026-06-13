import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from repositories.project_repository import ProjectRepository
from services.material_service import MaterialService
from services.recipe_service import RecipeService

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    project = repo.create(project_data.name)
    return project


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    return repo.list_all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
