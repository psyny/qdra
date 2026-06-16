import uuid
from typing import Any, Dict, List, Optional

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
    is_label: bool = False
    is_unique: bool = False
    is_searchable: bool = False
    is_hidden: bool = False
    default_value: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


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
    is_label: bool
    is_unique: bool
    is_searchable: bool
    is_hidden: bool
    default_value: Optional[str]
    validation: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str


class ViewCreate(BaseModel):
    view_name: str
    sort_order: int = 0


class ViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    view_name: str
    sort_order: int
    created_at: str
    updated_at: str


class ViewConfigCreate(BaseModel):
    entity_type: str  # "material" | "recipe"
    filter_params: Optional[List[Dict[str, Any]]] = None  # [{domain, key, value}, ...] AND logic; null = fallback
    slots: List[Dict[str, Any]]  # [{domain, key}, ...]
    sort_order: int = 0


class ViewConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    view_id: uuid.UUID
    entity_type: str
    filter_params: Optional[List[Dict[str, Any]]]
    slots: List[Dict[str, Any]]
    sort_order: int
    created_at: str
    updated_at: str


class ViewWithConfigsResponse(BaseModel):
    id: uuid.UUID
    project_template_id: uuid.UUID
    view_name: str
    sort_order: int
    configs: List[ViewConfigResponse]
    created_at: str
    updated_at: str


class ProjectTemplateDetailResponse(BaseModel):
    template: ProjectTemplateResponse
    material_types: List[MaterialTypeResponse]
    recipe_types: List[RecipeTypeResponse]
    parameter_definitions: List[ParameterDefinitionResponse]
    views: List[ViewWithConfigsResponse]


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
    raw_views = repo.list_views(project_template_id)
    views = [
        ViewWithConfigsResponse(
            id=v.id,
            project_template_id=v.project_template_id,
            view_name=v.view_name,
            sort_order=v.sort_order,
            configs=[ViewConfigResponse.model_validate(c) for c in repo.list_view_configs(v.id)],
            created_at=str(v.created_at),
            updated_at=str(v.updated_at),
        )
        for v in raw_views
    ]

    return ProjectTemplateDetailResponse(
        template=template,
        material_types=material_types,
        recipe_types=recipe_types,
        parameter_definitions=parameter_definitions,
        views=views,
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


@router.post("/project-templates/{project_template_id}/views", response_model=ViewResponse)
def create_view(
    project_template_id: uuid.UUID,
    data: ViewCreate,
    db: Session = Depends(get_db),
):
    """Create a named view context within a project template."""
    repo = ProjectTemplateRepository(db)
    template = repo.get_by_id(project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")

    view = repo.create_view(
        project_template_id=project_template_id,
        view_name=data.view_name,
        sort_order=data.sort_order,
    )
    return view


@router.get("/project-templates/{project_template_id}/views", response_model=List[ViewWithConfigsResponse])
def list_views(
    project_template_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """List all views for a project template, each with their configs."""
    repo = ProjectTemplateRepository(db)
    template = repo.get_by_id(project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")

    raw_views = repo.list_views(project_template_id)
    return [
        ViewWithConfigsResponse(
            id=v.id,
            project_template_id=v.project_template_id,
            view_name=v.view_name,
            sort_order=v.sort_order,
            configs=[ViewConfigResponse.model_validate(c) for c in repo.list_view_configs(v.id)],
            created_at=str(v.created_at),
            updated_at=str(v.updated_at),
        )
        for v in raw_views
    ]


@router.delete("/project-templates/{project_template_id}/views/{view_id}", status_code=204)
def delete_view(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Delete a view and all its configs (cascades)."""
    repo = ProjectTemplateRepository(db)
    if not repo.delete_view(view_id):
        raise HTTPException(status_code=404, detail="View not found")


@router.post("/project-templates/{project_template_id}/views/{view_id}/configs", response_model=ViewConfigResponse)
def create_view_config(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    data: ViewConfigCreate,
    db: Session = Depends(get_db),
):
    """Add an entity display config to a view."""
    repo = ProjectTemplateRepository(db)
    view = repo.get_view_by_id(view_id)
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    if view.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="View not found")

    if data.entity_type not in ("material", "recipe"):
        raise HTTPException(status_code=400, detail="entity_type must be 'material' or 'recipe'")

    config = repo.create_view_config(
        view_id=view_id,
        entity_type=data.entity_type,
        filter_params=data.filter_params,
        slots=data.slots,
        sort_order=data.sort_order,
    )
    return config


@router.delete("/project-templates/{project_template_id}/views/{view_id}/configs/{config_id}", status_code=204)
def delete_view_config(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Delete a single view config."""
    repo = ProjectTemplateRepository(db)
    if not repo.delete_view_config(config_id):
        raise HTTPException(status_code=404, detail="View config not found")


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
        is_label=data.is_label,
        is_unique=data.is_unique,
        is_searchable=data.is_searchable,
        is_hidden=data.is_hidden,
        default_value=data.default_value,
        validation=data.validation,
    )
    return param_def
