import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from repositories.project_repository import ProjectRepository
from repositories.project_template_repository import ProjectTemplateRepository
from repositories.image_asset_repository import ImageAssetRepository
from repositories.entity_repository import EntityRepository
from api.project_templates import ProjectTemplateDetailResponse
from infrastructure.storage.image_storage_provider import ImageStorageProvider
from infrastructure.storage.local_image_storage_provider import LocalImageStorageProvider
from infrastructure.storage.s3_image_storage_provider import S3ImageStorageProvider
from infrastructure.config.settings import settings

router = APIRouter()


def _get_storage_provider() -> ImageStorageProvider:
    """Get the configured storage provider."""
    if settings.image_storage_backend == "local":
        return LocalImageStorageProvider(settings.local_storage_root)
    elif settings.image_storage_backend == "s3":
        return S3ImageStorageProvider(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url or None,
            access_key_id=settings.s3_access_key_id or None,
            secret_access_key=settings.s3_secret_access_key or None,
            public_base_url=settings.s3_public_base_url or None,
            force_path_style=getattr(settings, 's3_force_path_style', False),
        )
    else:
        raise ValueError(f"Unknown storage backend: {settings.image_storage_backend}")


class ProjectCreate(BaseModel):
    name: str
    project_template_id: uuid.UUID  # Required as of template hub milestone
    image_size_px: int = 256  # Default 256, range 32-1024


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    project_template_id: uuid.UUID
    image_size_px: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    # Validate that the template exists
    template_repo = ProjectTemplateRepository(db)
    template = template_repo.get_by_id(project_data.project_template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Project template not found")

    # Validate image_size_px range
    if not (32 <= project_data.image_size_px <= 1024):
        raise HTTPException(status_code=400, detail="image_size_px must be between 32 and 1024")

    repo = ProjectRepository(db)
    project = repo.create(
        project_data.name, 
        project_data.project_template_id,
        image_size_px=project_data.image_size_px
    )
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


@router.get("/projects/{project_id}/template", response_model=ProjectTemplateDetailResponse)
def get_project_template(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get the project template for a project."""
    project_repo = ProjectRepository(db)
    project = project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    template_repo = ProjectTemplateRepository(db)
    template = template_repo.get_by_id(project.project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")
    
    # Build the detailed response
    entity_types = template_repo.list_entity_types(template.id)
    parameter_definitions = []
    for et in entity_types:
        param_defs = template_repo.list_parameter_definitions_by_entity_type(et.id)
        parameter_definitions.extend(param_defs)
    
    views = template_repo.list_views(template.id)
    
    return ProjectTemplateDetailResponse(
        template=template,
        entity_types=entity_types,
        parameter_definitions=parameter_definitions,
        views=views,
    )


class ProjectUpdateTemplate(BaseModel):
    project_template_id: uuid.UUID


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    image_size_px: Optional[int] = None


@router.patch("/projects/{project_id}/template", response_model=ProjectResponse)
def update_project_template(
    project_id: uuid.UUID,
    data: ProjectUpdateTemplate,
    db: Session = Depends(get_db),
):
    """Update a project's template."""
    template_repo = ProjectTemplateRepository(db)
    template = template_repo.get_by_id(data.project_template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Project template not found")

    repo = ProjectRepository(db)
    project = repo.update_template(project_id, data.project_template_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """Update a project's name or image_size_px."""
    # Validate image_size_px range if provided
    if data.image_size_px is not None and not (32 <= data.image_size_px <= 1024):
        raise HTTPException(status_code=400, detail="image_size_px must be between 32 and 1024")

    repo = ProjectRepository(db)
    project = repo.update(project_id, name=data.name, image_size_px=data.image_size_px)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a project and all its entities and images."""
    from qdra.infrastructure.cache.cache_service import CacheService
    entity_repo = EntityRepository(db, CacheService())
    image_repo = ImageAssetRepository(db)
    storage_provider = _get_storage_provider()
    
    # Get all entities in the project
    entities = entity_repo.list_by_project(project_id)
    
    # Delete images from storage for all entities
    for entity in entities:
        images = image_repo.get_by_entity_id(entity.id)
        for image in images:
            try:
                storage_provider.delete(image.storage_key)
            except Exception:
                pass  # Ignore storage deletion errors
    
    # Delete the project (repository handles entity cascade)
    repo = ProjectRepository(db)
    if not repo.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
