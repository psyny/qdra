import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from repositories.project_template_repository import ProjectTemplateRepository

router = APIRouter()


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class ProjectTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: Optional[str]
    version: int
    is_builtin: bool
    created_at: str
    updated_at: str


class MaterialTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class MaterialTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    name: str
    description: Optional[str]
    sort_order: int
    created_at: str
    updated_at: str


class RecipeTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class RecipeTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    name: str
    description: Optional[str]
    sort_order: int
    created_at: str
    updated_at: str


class ParameterDefinitionCreate(BaseModel):
    owner_kind: str  # "material_type" or "recipe_type"
    owner_type_id: uuid.UUID
    domain: str
    key: str
    value_type: str  # "string", "integer", "float", "boolean"
    label: Optional[str] = None
    description: Optional[str] = None
    required: bool = False
    sort_order: int = 0


class ParameterDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    owner_kind: str
    owner_type_id: uuid.UUID
    domain: str
    key: str
    value_type: str
    label: Optional[str]
    description: Optional[str]
    required: bool
    sort_order: int
    created_at: str
    updated_at: str


class ProjectTemplateDetailResponse(BaseModel):
    template: ProjectTemplateResponse
    material_types: List[MaterialTypeResponse]
    recipe_types: List[RecipeTypeResponse]
    parameter_definitions: List[ParameterDefinitionResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/project-templates", response_model=ProjectTemplateResponse)
def create_project_template(
    data: ProjectTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new project template."""
    repo = ProjectTemplateRepository(db)
    template = repo.create(name=data.name, description=data.description, is_builtin=False)
    return template


@router.get("/project-templates", response_model=List[ProjectTemplateResponse])
def list_project_templates(db: Session = Depends(get_db)):
    """List all available project templates."""
    repo = ProjectTemplateRepository(db)
    return repo.list_all()


@router.get("/project-templates/{project_template_id}", response_model=ProjectTemplateDetailResponse)
def get_project_template_detail(
    project_template_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get full details of a project template including types and parameter definitions."""
    repo = ProjectTemplateRepository(db)
    template = repo.get_by_id(project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")

    material_types = repo.list_material_types(project_template_id)
    recipe_types = repo.list_recipe_types(project_template_id)
    parameter_definitions = repo.list_parameter_definitions(project_template_id)

    return ProjectTemplateDetailResponse(
        template=template,
        material_types=material_types,
        recipe_types=recipe_types,
        parameter_definitions=parameter_definitions,
    )


@router.post("/project-templates/{project_template_id}/material-types", response_model=MaterialTypeResponse)
def create_material_type(
    project_template_id: uuid.UUID,
    data: MaterialTypeCreate,
    db: Session = Depends(get_db),
):
    """Create a material type within a project template."""
    repo = ProjectTemplateRepository(db)
    template = repo.get_by_id(project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")

    material_type = repo.create_material_type(
        project_template_id=project_template_id,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    return material_type


@router.post("/project-templates/{project_template_id}/recipe-types", response_model=RecipeTypeResponse)
def create_recipe_type(
    project_template_id: uuid.UUID,
    data: RecipeTypeCreate,
    db: Session = Depends(get_db),
):
    """Create a recipe type within a project template."""
    repo = ProjectTemplateRepository(db)
    template = repo.get_by_id(project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")

    recipe_type = repo.create_recipe_type(
        project_template_id=project_template_id,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    return recipe_type


@router.post("/project-templates/{project_template_id}/parameter-definitions", response_model=ParameterDefinitionResponse)
def create_parameter_definition(
    project_template_id: uuid.UUID,
    data: ParameterDefinitionCreate,
    db: Session = Depends(get_db),
):
    """Create a parameter definition for a material type or recipe type."""
    repo = ProjectTemplateRepository(db)
    template = repo.get_by_id(project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")

    if data.owner_kind not in ("material_type", "recipe_type"):
        raise HTTPException(status_code=400, detail="owner_kind must be 'material_type' or 'recipe_type'")

    if data.value_type not in ("string", "integer", "float", "boolean"):
        raise HTTPException(status_code=400, detail="value_type must be one of: string, integer, float, boolean")

    param_def = repo.create_parameter_definition(
        project_template_id=project_template_id,
        owner_kind=data.owner_kind,
        owner_type_id=data.owner_type_id,
        domain=data.domain,
        key=data.key,
        value_type=data.value_type,
        label=data.label,
        description=data.description,
        required=data.required,
        sort_order=data.sort_order,
    )
    return param_def
