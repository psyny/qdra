import uuid
from datetime import datetime
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


class ProjectTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectTemplateCloneRequest(BaseModel):
    name: Optional[str] = None


class ProjectTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: Optional[str]
    version: int
    is_builtin: bool
    created_at: datetime
    updated_at: datetime


class EntityTypeCreate(BaseModel):
    kind: str
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class EntityTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    # kind is immutable - not included in update


class ParameterDefinitionCreate(BaseModel):
    domain: str
    key: str
    value_type: str
    label: str = ""
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
    entity_type_id: uuid.UUID
    domain: str
    key: str
    value_type: str
    label: str
    description: Optional[str]
    required: bool
    sort_order: int
    is_label: bool
    is_unique: bool
    is_searchable: bool
    is_hidden: bool
    default_value: Optional[str]
    validation: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ParameterDefinitionUpdate(BaseModel):
    domain: Optional[str] = None
    key: Optional[str] = None
    value_type: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    sort_order: Optional[int] = None
    is_label: Optional[bool] = None
    is_unique: Optional[bool] = None
    is_searchable: Optional[bool] = None
    is_hidden: Optional[bool] = None
    default_value: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


class EntityTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    kind: str
    name: str
    description: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime
    parameter_definitions: List[ParameterDefinitionResponse] = []


class ParameterDefinitionUpdate(BaseModel):
    domain: Optional[str] = None
    key: Optional[str] = None
    value_type: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    sort_order: Optional[int] = None
    is_label: Optional[bool] = None
    is_unique: Optional[bool] = None
    is_searchable: Optional[bool] = None
    is_hidden: Optional[bool] = None
    default_value: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


class ViewCreate(BaseModel):
    view_name: str
    sort_order: int = 0


class ViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    view_name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ViewConfigCreate(BaseModel):
    entity_kind: Optional[str] = None
    entity_type_id: Optional[uuid.UUID] = None
    filter_params: Optional[List[Dict[str, Any]]] = None
    slots: Optional[List[Dict[str, Any]]] = None
    sort_order: int = 0


class ViewConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    view_id: uuid.UUID
    entity_kind: Optional[str]
    entity_type_id: Optional[uuid.UUID]
    filter_params: Optional[List[Dict[str, Any]]]
    slots: Optional[List[Dict[str, Any]]]
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ViewWithConfigsResponse(BaseModel):
    id: uuid.UUID
    project_template_id: uuid.UUID
    view_name: str
    sort_order: int
    configs: List[ViewConfigResponse]
    created_at: datetime
    updated_at: datetime


class ProjectTemplateDetailResponse(BaseModel):
    template: ProjectTemplateResponse
    entity_types: List[EntityTypeResponse]
    parameter_definitions: List[ParameterDefinitionResponse]
    views: List[ViewWithConfigsResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/project-templates", response_model=ProjectTemplateResponse)
def create_project_template(data: ProjectTemplateCreate, db: Session = Depends(get_db)):
    repo = ProjectTemplateRepository(db)
    return repo.create(name=data.name, description=data.description, is_builtin=False)


@router.get("/project-templates", response_model=List[ProjectTemplateResponse])
def list_project_templates(db: Session = Depends(get_db)):
    return ProjectTemplateRepository(db).list_all()


@router.get("/project-templates/{project_template_id}", response_model=ProjectTemplateDetailResponse)
def get_project_template_detail(
    project_template_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    template = repo.get_by_id(project_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")

    entity_types = repo.list_entity_types(project_template_id)
    param_defs = repo.list_parameter_definitions(project_template_id)
    raw_views = repo.list_views(project_template_id)
    views = [
        ViewWithConfigsResponse(
            id=v.id,
            project_template_id=v.project_template_id,
            view_name=v.view_name,
            sort_order=v.sort_order,
            configs=[ViewConfigResponse.model_validate(c) for c in repo.list_view_configs(v.id)],
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in raw_views
    ]
    return ProjectTemplateDetailResponse(
        template=ProjectTemplateResponse.model_validate(template),
        entity_types=[EntityTypeResponse.model_validate(et) for et in entity_types],
        parameter_definitions=[ParameterDefinitionResponse.model_validate(pd) for pd in param_defs],
        views=views,
    )


@router.put("/project-templates/{project_template_id}", response_model=ProjectTemplateResponse)
def update_project_template(
    project_template_id: uuid.UUID,
    data: ProjectTemplateUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    template = repo.update(template_id=project_template_id, name=data.name, description=data.description)
    if not template:
        raise HTTPException(status_code=404, detail="Project template not found")
    return template


@router.delete("/project-templates/{project_template_id}", status_code=204)
def delete_project_template(
    project_template_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    success = repo.delete(project_template_id)
    if not success:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete template: it is used by one or more projects.",
        )


@router.post("/project-templates/{project_template_id}/clone", response_model=ProjectTemplateResponse)
def clone_project_template(
    project_template_id: uuid.UUID,
    data: ProjectTemplateCloneRequest,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    cloned = repo.clone_template(project_template_id, data.name)
    if not cloned:
        raise HTTPException(status_code=404, detail="Project template not found")
    return cloned


# Entity types

@router.post("/project-templates/{project_template_id}/entity-types", response_model=EntityTypeResponse)
def create_entity_type(
    project_template_id: uuid.UUID,
    data: EntityTypeCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    if data.kind not in ("material", "recipe"):
        raise HTTPException(status_code=400, detail="kind must be one of: material, recipe")
    entity_type = repo.create_entity_type(
        project_template_id=project_template_id,
        kind=data.kind,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    # Return with empty parameter definitions
    et_response = EntityTypeResponse.model_validate(entity_type)
    et_response.parameter_definitions = []
    return et_response


@router.get("/project-templates/{project_template_id}/entity-types", response_model=List[EntityTypeResponse])
def list_entity_types(
    project_template_id: uuid.UUID,
    kind: Optional[str] = None,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    entity_types = repo.list_entity_types(project_template_id, kind=kind)
    # Attach parameter definitions to each entity type
    result = []
    for et in entity_types:
        param_defs = repo.list_parameter_definitions_by_entity_type(et.id)
        et_response = EntityTypeResponse.model_validate(et)
        et_response.parameter_definitions = [ParameterDefinitionResponse.model_validate(pd) for pd in param_defs]
        result.append(et_response)
    return result


@router.get(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}",
    response_model=EntityTypeResponse,
)
def get_entity_type(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    et = repo.get_entity_type_by_id(entity_type_id)
    if not et or et.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="Entity type not found")
    param_defs = repo.list_parameter_definitions_by_entity_type(entity_type_id)
    et_response = EntityTypeResponse.model_validate(et)
    et_response.parameter_definitions = [ParameterDefinitionResponse.model_validate(pd) for pd in param_defs]
    return et_response


@router.post(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}/clone",
    response_model=EntityTypeResponse,
)
def clone_entity_type(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    source = repo.get_entity_type_by_id(entity_type_id)
    if not source or source.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="Entity type not found")
    
    # Clone with "Copy" suffix
    clone_name = f"{source.name} Copy"
    cloned = repo.create_entity_type(
        project_template_id=project_template_id,
        kind=source.kind,
        name=clone_name,
        description=source.description,
        sort_order=source.sort_order,
    )
    
    # Clone parameter definitions
    for param_def in repo.list_parameter_definitions_by_entity_type(entity_type_id):
        repo.create_parameter_definition(
            project_template_id=project_template_id,
            entity_type_id=cloned.id,
            domain=param_def.domain,
            key=param_def.key,
            value_type=param_def.value_type,
            label=param_def.label,
            description=param_def.description,
            required=param_def.required,
            sort_order=param_def.sort_order,
            is_label=param_def.is_label,
            is_unique=param_def.is_unique,
            is_searchable=param_def.is_searchable,
            is_hidden=param_def.is_hidden,
            default_value=param_def.default_value,
            validation=param_def.validation,
        )
    
    # Return with parameter definitions
    param_defs = repo.list_parameter_definitions_by_entity_type(cloned.id)
    cloned_response = EntityTypeResponse.model_validate(cloned)
    cloned_response.parameter_definitions = [ParameterDefinitionResponse.model_validate(pd) for pd in param_defs]
    return cloned_response


@router.put(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}",
    response_model=EntityTypeResponse,
)
def update_entity_type(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    data: EntityTypeUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    et = repo.update_entity_type(
        entity_type_id=entity_type_id,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    if not et:
        raise HTTPException(status_code=404, detail="Entity type not found")
    # Return with parameter definitions
    param_defs = repo.list_parameter_definitions_by_entity_type(entity_type_id)
    et_response = EntityTypeResponse.model_validate(et)
    et_response.parameter_definitions = [ParameterDefinitionResponse.model_validate(pd) for pd in param_defs]
    return et_response


@router.delete(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}",
    status_code=204,
)
def delete_entity_type(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    # Check if entity type is used by runtime entities
    if repo.is_entity_type_used_by_entities(entity_type_id):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete entity type: it is used by existing entities."
        )
    if not repo.delete_entity_type(entity_type_id):
        raise HTTPException(status_code=404, detail="Entity type not found")


# Parameter definitions

@router.post(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}/parameter-definitions",
    response_model=ParameterDefinitionResponse,
)
def create_parameter_definition(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    data: ParameterDefinitionCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    if not repo.get_entity_type_by_id(entity_type_id):
        raise HTTPException(status_code=404, detail="Entity type not found")
    if data.value_type not in ("string", "number", "boolean"):
        raise HTTPException(status_code=400, detail="value_type must be one of: string, number, boolean")
    return repo.create_parameter_definition(
        project_template_id=project_template_id,
        entity_type_id=entity_type_id,
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


@router.get(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}/parameter-definitions",
    response_model=List[ParameterDefinitionResponse],
)
def list_parameter_definitions_by_entity_type(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    if not repo.get_entity_type_by_id(entity_type_id):
        raise HTTPException(status_code=404, detail="Entity type not found")
    return repo.list_parameter_definitions_by_entity_type(entity_type_id)


@router.patch(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}/parameter-definitions/{definition_id}",
    response_model=ParameterDefinitionResponse,
)
def update_parameter_definition(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    definition_id: uuid.UUID,
    data: ParameterDefinitionUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    param_def = repo.update_parameter_definition(
        definition_id=definition_id,
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
    if not param_def:
        raise HTTPException(status_code=404, detail="Parameter definition not found")
    return param_def


@router.delete(
    "/project-templates/{project_template_id}/entity-types/{entity_type_id}/parameter-definitions/{definition_id}",
    status_code=204,
)
def delete_parameter_definition(
    project_template_id: uuid.UUID,
    entity_type_id: uuid.UUID,
    definition_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    if not repo.delete_parameter_definition(definition_id):
        raise HTTPException(status_code=404, detail="Parameter definition not found")


# Views

@router.post("/project-templates/{project_template_id}/views", response_model=ViewResponse)
def create_view(
    project_template_id: uuid.UUID,
    data: ViewCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    return repo.create_view(
        project_template_id=project_template_id,
        view_name=data.view_name,
        sort_order=data.sort_order,
    )


@router.get(
    "/project-templates/{project_template_id}/views",
    response_model=List[ViewWithConfigsResponse],
)
def list_views(
    project_template_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    raw_views = repo.list_views(project_template_id)
    return [
        ViewWithConfigsResponse(
            id=v.id,
            project_template_id=v.project_template_id,
            view_name=v.view_name,
            sort_order=v.sort_order,
            configs=[ViewConfigResponse.model_validate(c) for c in repo.list_view_configs(v.id)],
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in raw_views
    ]


@router.delete("/project-templates/{project_template_id}/views/{view_id}", status_code=204)
def delete_view(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.delete_view(view_id):
        raise HTTPException(status_code=404, detail="View not found")


@router.post(
    "/project-templates/{project_template_id}/views/{view_id}/configs",
    response_model=ViewConfigResponse,
)
def create_view_config(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    data: ViewConfigCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    view = repo.get_view_by_id(view_id)
    if not view or view.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="View not found")
    return repo.create_view_config(
        view_id=view_id,
        entity_kind=data.entity_kind,
        entity_type_id=data.entity_type_id,
        filter_params=data.filter_params,
        slots=data.slots,
        sort_order=data.sort_order,
    )


@router.delete(
    "/project-templates/{project_template_id}/views/{view_id}/configs/{config_id}",
    status_code=204,
)
def delete_view_config(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.delete_view_config(config_id):
        raise HTTPException(status_code=404, detail="View config not found")
