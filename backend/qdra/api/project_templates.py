import uuid
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from repositories.project_template_repository import ProjectTemplateRepository

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Validation Functions
# ---------------------------------------------------------------------------

def validate_domain_name(domain: str) -> None:
    """
    Validate that domain name does not start with underscore.
    Domain names starting with '_' are reserved for system use.
    Raises HTTPException if validation fails.
    """
    if domain.startswith("_"):
        raise HTTPException(
            status_code=400,
            detail="Domain names starting with '_' are reserved for system use"
        )


def validate_parameter_definition(
    value_type: str,
    validation_min: Optional[float] = None,
    validation_max: Optional[float] = None,
    validation_regex: Optional[str] = None,
) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Validate and normalize parameter definition validation fields.
    
    Returns normalized (validation_min, validation_max, validation_regex).
    Raises HTTPException if validation fails.
    """
    # Normalize empty regex to None
    if validation_regex is not None and validation_regex.strip() == "":
        validation_regex = None
    
    # For boolean parameters, ignore all validation fields
    if value_type == "boolean":
        return None, None, None
    
    # For number parameters, ignore regex
    if value_type == "number":
        validation_regex = None
    
    # Validate min/max relationship
    if validation_min is not None and validation_max is not None:
        if validation_min > validation_max:
            raise HTTPException(
                status_code=400,
                detail="validation_min cannot be greater than validation_max"
            )
    
    # For string parameters, validate that min/max are non-negative
    if value_type == "string":
        if validation_min is not None and validation_min < 0:
            raise HTTPException(
                status_code=400,
                detail="validation_min for string parameters must be >= 0"
            )
        if validation_max is not None and validation_max < 0:
            raise HTTPException(
                status_code=400,
                detail="validation_max for string parameters must be >= 0"
            )
        # Validate regex compiles
        if validation_regex is not None:
            try:
                re.compile(validation_regex)
            except re.error as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid regex: {str(e)}"
                )
    
    return validation_min, validation_max, validation_regex


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
    validation_min: Optional[float] = None
    validation_max: Optional[float] = None
    validation_regex: Optional[str] = None


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
    validation_min: Optional[float]
    validation_max: Optional[float]
    validation_regex: Optional[str]
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
    validation_min: Optional[float] = None
    validation_max: Optional[float] = None
    validation_regex: Optional[str] = None


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


class ViewCreate(BaseModel):
    view_key: str
    label: str
    description: Optional[str] = None
    sort_order: int = 0


class ViewUpdate(BaseModel):
    view_key: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class ViewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    view_key: str
    label: str
    description: Optional[str]
    is_system: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ViewConfigCreate(BaseModel):
    entity_type_id: Optional[uuid.UUID] = None
    filter_params: Optional[List[Dict[str, Any]]] = None
    display_slots: Optional[List[Dict[str, Any]]] = None
    sort_order: int = 0


class ViewConfigUpdate(BaseModel):
    entity_type_id: Optional[uuid.UUID] = None
    filter_params: Optional[List[Dict[str, Any]]] = None
    display_slots: Optional[List[Dict[str, Any]]] = None
    sort_order: Optional[int] = None


class ViewConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    view_id: uuid.UUID
    entity_type_id: Optional[uuid.UUID]
    filter_params: Optional[List[Dict[str, Any]]]
    display_slots: Optional[List[Dict[str, Any]]]
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ViewWithConfigsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_template_id: uuid.UUID
    view_key: str
    label: str
    description: Optional[str]
    is_system: bool
    sort_order: int
    configs: List[ViewConfigResponse]
    created_at: datetime
    updated_at: datetime


class ProjectTemplateDetailResponse(BaseModel):
    template: ProjectTemplateResponse
    entity_types: List[EntityTypeResponse]
    parameter_definitions: List[ParameterDefinitionResponse]
    views: List[ViewWithConfigsResponse]


class TemplateImportRequest(BaseModel):
    data: Dict[str, Any]
    name: Optional[str] = None


class TemplateExportResponse(BaseModel):
    data: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/project-templates", response_model=ProjectTemplateResponse, status_code=201)
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
            view_key=v.view_key,
            label=v.label,
            description=v.description,
            is_system=v.is_system,
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


@router.post("/project-templates/{project_template_id}/clone", response_model=ProjectTemplateResponse, status_code=201)
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


@router.get(
    "/project-templates/{project_template_id}/export",
    response_model=TemplateExportResponse,
)
def export_template(
    project_template_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    data = repo.export_template(project_template_id)
    return TemplateExportResponse(data=data)


@router.post(
    "/project-templates/import",
    response_model=ProjectTemplateResponse,
    status_code=201,
)
def import_template(
    request: TemplateImportRequest,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    try:
        template = repo.import_template(request.data, request.name)
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import template: {str(e)}")


# Entity types

@router.post("/project-templates/{project_template_id}/entity-types", response_model=EntityTypeResponse, status_code=201)
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
    status_code=201,
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
    status_code=201,
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
    
    # Validate domain name
    validate_domain_name(data.domain)
    
    # Validate and normalize validation fields
    validation_min, validation_max, validation_regex = validate_parameter_definition(
        data.value_type,
        data.validation_min,
        data.validation_max,
        data.validation_regex,
    )
    
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
        validation_min=validation_min,
        validation_max=validation_max,
        validation_regex=validation_regex,
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
    
    # Get existing param_def to check value_type if not being updated
    existing_param_def = repo.get_parameter_definition_by_id(definition_id)
    if not existing_param_def:
        raise HTTPException(status_code=404, detail="Parameter definition not found")
    
    # Use the value_type from the update if provided, otherwise use existing
    value_type = data.value_type if data.value_type is not None else existing_param_def.value_type
    
    # Validate domain name if being updated
    if data.domain is not None:
        validate_domain_name(data.domain)
    
    # Validate and normalize validation fields
    validation_min, validation_max, validation_regex = validate_parameter_definition(
        value_type,
        data.validation_min,
        data.validation_max,
        data.validation_regex,
    )
    
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
        validation_min=validation_min,
        validation_max=validation_max,
        validation_regex=validation_regex,
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

@router.post("/project-templates/{project_template_id}/views", response_model=ViewResponse, status_code=201)
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
        view_key=data.view_key,
        label=data.label,
        description=data.description,
        is_system=False,
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
            view_key=v.view_key,
            label=v.label,
            description=v.description,
            is_system=v.is_system,
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
    view = repo.get_view_by_id(view_id)
    if not view or view.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="View not found")
    if view.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system views")
    if not repo.delete_view(view_id):
        raise HTTPException(status_code=404, detail="View not found")


@router.put(
    "/project-templates/{project_template_id}/views/{view_id}",
    response_model=ViewResponse,
)
def update_view(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    data: ViewUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    view = repo.get_view_by_id(view_id)
    if not view or view.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="View not found")
    if view.is_system and data.view_key is not None:
        raise HTTPException(status_code=403, detail="Cannot modify system view key")
    updated = repo.update_view(
        view_id=view_id,
        view_key=data.view_key,
        label=data.label,
        description=data.description,
        sort_order=data.sort_order,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="View not found")
    return updated


@router.post(
    "/project-templates/{project_template_id}/views/seed-system",
    response_model=List[ViewResponse],
)
def seed_system_views(
    project_template_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.get_by_id(project_template_id):
        raise HTTPException(status_code=404, detail="Project template not found")
    views = repo.seed_system_views(project_template_id)
    return [ViewResponse.model_validate(v) for v in views]


@router.post(
    "/project-templates/{project_template_id}/views/{view_id}/configs",
    response_model=ViewConfigResponse,
    status_code=201,
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
        entity_type_id=data.entity_type_id,
        filter_params=data.filter_params,
        display_slots=data.display_slots,
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
    view = repo.get_view_by_id(view_id)
    if not view or view.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="View not found")
    if not repo.delete_view_config(config_id):
        raise HTTPException(status_code=404, detail="View config not found")


@router.put(
    "/project-templates/{project_template_id}/views/{view_id}/configs/{config_id}",
    response_model=ViewConfigResponse,
)
def update_view_config(
    project_template_id: uuid.UUID,
    view_id: uuid.UUID,
    config_id: uuid.UUID,
    data: ViewConfigUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    view = repo.get_view_by_id(view_id)
    if not view or view.project_template_id != project_template_id:
        raise HTTPException(status_code=404, detail="View not found")
    updated = repo.update_view_config(
        config_id=config_id,
        entity_type_id=data.entity_type_id,
        filter_params=data.filter_params,
        display_slots=data.display_slots,
        sort_order=data.sort_order,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="View config not found")
    return updated


# ---------------------------------------------------------------------------
# Slot Group Models
# ---------------------------------------------------------------------------

class SlotGroupCreate(BaseModel):
    type: str
    min_slots: int = 0
    max_slots: Optional[int] = None
    default_slots_qty: int = 0
    sort_order: int = 0


class SlotGroupUpdate(BaseModel):
    type: Optional[str] = None
    min_slots: Optional[int] = None
    max_slots: Optional[int] = None
    default_slots_qty: Optional[int] = None
    sort_order: Optional[int] = None


class SlotConstraintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slot_group_id: Optional[uuid.UUID]
    slot_definition_id: Optional[uuid.UUID]
    domain: Optional[str]
    key: Optional[str]
    operator: Optional[str]
    value_string: Optional[str]
    value_number: Optional[float]
    value_boolean: Optional[bool]
    is_wildcard: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class SlotDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slot_group_id: uuid.UUID
    slot_key: str
    slot_idx: Optional[int]
    min_occurrences: int
    max_occurrences: Optional[int]
    sort_order: int
    created_at: datetime
    updated_at: datetime
    constraints: List[SlotConstraintResponse] = []


class SlotGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entity_type_id: uuid.UUID
    type: str
    min_slots: int
    max_slots: Optional[int]
    default_slots_qty: int
    sort_order: int
    created_at: datetime
    updated_at: datetime
    constraints: List[SlotConstraintResponse] = []
    slot_definitions: List[SlotDefinitionResponse] = []


# ---------------------------------------------------------------------------
# Slot Definition Models
# ---------------------------------------------------------------------------

class SlotDefinitionCreate(BaseModel):
    slot_key: str
    slot_idx: Optional[int] = None
    min_occurrences: int = 0
    max_occurrences: Optional[int] = None
    sort_order: int = 0


class SlotDefinitionUpdate(BaseModel):
    slot_key: Optional[str] = None
    slot_idx: Optional[int] = None
    min_occurrences: Optional[int] = None
    max_occurrences: Optional[int] = None
    sort_order: Optional[int] = None


# ---------------------------------------------------------------------------
# Slot Constraint Models
# ---------------------------------------------------------------------------

class SlotConstraintCreate(BaseModel):
    domain: Optional[str] = None
    key: Optional[str] = None
    operator: Optional[str] = None
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False
    sort_order: int = 0


class SlotConstraintUpdate(BaseModel):
    domain: Optional[str] = None
    key: Optional[str] = None
    operator: Optional[str] = None
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: Optional[bool] = None
    sort_order: Optional[int] = None


# ---------------------------------------------------------------------------
# Slot Group Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/project-template-entity-types/{entity_type_id}/slot-groups",
    response_model=List[SlotGroupResponse],
)
def list_slot_groups(
    entity_type_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    entity_type = repo.get_entity_type_by_id(entity_type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    
    slot_groups = repo.list_slot_groups(entity_type_id)
    
    # Build nested response with constraints and definitions
    result = []
    for sg in slot_groups:
        sg_response = SlotGroupResponse.model_validate(sg)
        sg_response.constraints = [
            SlotConstraintResponse.model_validate(c)
            for c in repo.list_slot_constraints_for_group(sg.id)
        ]
        
        slot_defs = repo.list_slot_definitions(sg.id)
        sg_response.slot_definitions = []
        for sd in slot_defs:
            sd_response = SlotDefinitionResponse.model_validate(sd)
            sd_response.constraints = [
                SlotConstraintResponse.model_validate(c)
                for c in repo.list_slot_constraints_for_definition(sd.id)
            ]
            sg_response.slot_definitions.append(sd_response)
        
        result.append(sg_response)
    
    return result


@router.post(
    "/project-template-entity-types/{entity_type_id}/slot-groups",
    response_model=SlotGroupResponse,
    status_code=201,
)
def create_slot_group(
    entity_type_id: uuid.UUID,
    data: SlotGroupCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    entity_type = repo.get_entity_type_by_id(entity_type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    
    # Validate entity type is recipe
    if entity_type.kind != "recipe":
        raise HTTPException(
            status_code=400,
            detail="Slot groups can only be created for recipe entity types"
        )
    
    # Validate type
    if data.type not in ("consumes", "requires", "produces"):
        raise HTTPException(
            status_code=400,
            detail="type must be one of: consumes, requires, produces"
        )
    
    # Validate min/max slots
    if data.min_slots < 0:
        raise HTTPException(status_code=400, detail="min_slots must be >= 0")
    if data.max_slots is not None and data.max_slots < data.min_slots:
        raise HTTPException(status_code=400, detail="max_slots must be >= min_slots")
    
    # Check for duplicate type
    existing_groups = repo.list_slot_groups(entity_type_id)
    for eg in existing_groups:
        if eg.type == data.type:
            raise HTTPException(
                status_code=409,
                detail=f"A {data.type} slot group already exists for this entity type"
            )
    
    slot_group = repo.create_slot_group(
        entity_type_id=entity_type_id,
        type=data.type,
        min_slots=data.min_slots,
        max_slots=data.max_slots,
        default_slots_qty=data.default_slots_qty,
        sort_order=data.sort_order,
    )
    
    response = SlotGroupResponse.model_validate(slot_group)
    response.constraints = []
    response.slot_definitions = []
    return response


@router.patch(
    "/project-template-slot-groups/{slot_group_id}",
    response_model=SlotGroupResponse,
)
def update_slot_group(
    slot_group_id: uuid.UUID,
    data: SlotGroupUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    slot_group = repo.get_slot_group_by_id(slot_group_id)
    if not slot_group:
        raise HTTPException(status_code=404, detail="Slot group not found")
    
    # Validate type if provided
    if data.type is not None and data.type not in ("consumes", "requires", "produces"):
        raise HTTPException(
            status_code=400,
            detail="type must be one of: consumes, requires, produces"
        )
    
    # Validate min/max slots if provided
    if data.min_slots is not None and data.min_slots < 0:
        raise HTTPException(status_code=400, detail="min_slots must be >= 0")
    
    if data.min_slots is not None and data.max_slots is not None:
        if data.max_slots < data.min_slots:
            raise HTTPException(status_code=400, detail="max_slots must be >= min_slots")
    
    # Check for duplicate type if changing
    if data.type is not None and data.type != slot_group.type:
        existing_groups = repo.list_slot_groups(slot_group.entity_type_id)
        for eg in existing_groups:
            if eg.id != slot_group_id and eg.type == data.type:
                raise HTTPException(
                    status_code=409,
                    detail=f"A {data.type} slot group already exists for this entity type"
                )
    
    updated = repo.update_slot_group(
        slot_group_id=slot_group_id,
        type=data.type,
        min_slots=data.min_slots,
        max_slots=data.max_slots,
        default_slots_qty=data.default_slots_qty,
        sort_order=data.sort_order,
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Slot group not found")
    
    response = SlotGroupResponse.model_validate(updated)
    response.constraints = [
        SlotConstraintResponse.model_validate(c)
        for c in repo.list_slot_constraints_for_group(slot_group_id)
    ]
    response.slot_definitions = []
    for sd in repo.list_slot_definitions(slot_group_id):
        sd_response = SlotDefinitionResponse.model_validate(sd)
        sd_response.constraints = [
            SlotConstraintResponse.model_validate(c)
            for c in repo.list_slot_constraints_for_definition(sd.id)
        ]
        response.slot_definitions.append(sd_response)
    
    return response


@router.delete("/project-template-slot-groups/{slot_group_id}", status_code=204)
def delete_slot_group(
    slot_group_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.delete_slot_group(slot_group_id):
        raise HTTPException(status_code=404, detail="Slot group not found")


# ---------------------------------------------------------------------------
# Slot Definition Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/project-template-slot-groups/{slot_group_id}/slot-definitions",
    response_model=SlotDefinitionResponse,
    status_code=201,
)
def create_slot_definition(
    slot_group_id: uuid.UUID,
    data: SlotDefinitionCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    slot_group = repo.get_slot_group_by_id(slot_group_id)
    if not slot_group:
        raise HTTPException(status_code=404, detail="Slot group not found")
    
    # Validate min/max occurrences
    if data.min_occurrences < 0:
        raise HTTPException(status_code=400, detail="min_occurrences must be >= 0")
    if data.max_occurrences is not None and data.max_occurrences < data.min_occurrences:
        raise HTTPException(status_code=400, detail="max_occurrences must be >= min_occurrences")
    
    # Check for duplicate slot_key
    existing_defs = repo.list_slot_definitions(slot_group_id)
    for ed in existing_defs:
        if ed.slot_key == data.slot_key:
            raise HTTPException(
                status_code=409,
                detail=f"A slot definition with key '{data.slot_key}' already exists in this group"
            )
    
    slot_def = repo.create_slot_definition(
        slot_group_id=slot_group_id,
        slot_key=data.slot_key,
        slot_idx=data.slot_idx,
        min_occurrences=data.min_occurrences,
        max_occurrences=data.max_occurrences,
        sort_order=data.sort_order,
    )
    
    response = SlotDefinitionResponse.model_validate(slot_def)
    response.constraints = []
    return response


@router.patch(
    "/project-template-slot-definitions/{slot_definition_id}",
    response_model=SlotDefinitionResponse,
)
def update_slot_definition(
    slot_definition_id: uuid.UUID,
    data: SlotDefinitionUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    slot_def = repo.get_slot_definition_by_id(slot_definition_id)
    if not slot_def:
        raise HTTPException(status_code=404, detail="Slot definition not found")
    
    # Validate min/max occurrences if provided
    if data.min_occurrences is not None and data.min_occurrences < 0:
        raise HTTPException(status_code=400, detail="min_occurrences must be >= 0")
    
    if data.min_occurrences is not None and data.max_occurrences is not None:
        if data.max_occurrences < data.min_occurrences:
            raise HTTPException(status_code=400, detail="max_occurrences must be >= min_occurrences")
    
    # Check for duplicate slot_key if changing
    if data.slot_key is not None and data.slot_key != slot_def.slot_key:
        existing_defs = repo.list_slot_definitions(slot_def.slot_group_id)
        for ed in existing_defs:
            if ed.id != slot_definition_id and ed.slot_key == data.slot_key:
                raise HTTPException(
                    status_code=409,
                    detail=f"A slot definition with key '{data.slot_key}' already exists in this group"
                )
    
    updated = repo.update_slot_definition(
        slot_def_id=slot_definition_id,
        slot_key=data.slot_key,
        slot_idx=data.slot_idx,
        min_occurrences=data.min_occurrences,
        max_occurrences=data.max_occurrences,
        sort_order=data.sort_order,
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Slot definition not found")
    
    response = SlotDefinitionResponse.model_validate(updated)
    response.constraints = [
        SlotConstraintResponse.model_validate(c)
        for c in repo.list_slot_constraints_for_definition(slot_definition_id)
    ]
    return response


@router.delete("/project-template-slot-definitions/{slot_definition_id}", status_code=204)
def delete_slot_definition(
    slot_definition_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.delete_slot_definition(slot_definition_id):
        raise HTTPException(status_code=404, detail="Slot definition not found")


# ---------------------------------------------------------------------------
# Slot Constraint Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/project-template-slot-groups/{slot_group_id}/constraints",
    response_model=SlotConstraintResponse,
    status_code=201,
)
def create_group_constraint(
    slot_group_id: uuid.UUID,
    data: SlotConstraintCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    slot_group = repo.get_slot_group_by_id(slot_group_id)
    if not slot_group:
        raise HTTPException(status_code=404, detail="Slot group not found")
    
    # Validate constraint
    if not data.is_wildcard:
        if not data.domain or not data.key or not data.operator:
            raise HTTPException(
                status_code=400,
                detail="Non-wildcard constraints require domain, key, and operator"
            )
        if not any([data.value_string is not None, data.value_number is not None, data.value_boolean is not None]):
            raise HTTPException(
                status_code=400,
                detail="Non-wildcard constraints require at least one value field"
            )
    
    constraint = repo.create_slot_constraint(
        slot_group_id=slot_group_id,
        domain=data.domain,
        key=data.key,
        operator=data.operator,
        value_string=data.value_string,
        value_number=data.value_number,
        value_boolean=data.value_boolean,
        is_wildcard=data.is_wildcard,
        sort_order=data.sort_order,
    )
    
    return SlotConstraintResponse.model_validate(constraint)


@router.post(
    "/project-template-slot-definitions/{slot_definition_id}/constraints",
    response_model=SlotConstraintResponse,
    status_code=201,
)
def create_definition_constraint(
    slot_definition_id: uuid.UUID,
    data: SlotConstraintCreate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    slot_def = repo.get_slot_definition_by_id(slot_definition_id)
    if not slot_def:
        raise HTTPException(status_code=404, detail="Slot definition not found")
    
    # Validate constraint
    if not data.is_wildcard:
        if not data.domain or not data.key or not data.operator:
            raise HTTPException(
                status_code=400,
                detail="Non-wildcard constraints require domain, key, and operator"
            )
        if not any([data.value_string is not None, data.value_number is not None, data.value_boolean is not None]):
            raise HTTPException(
                status_code=400,
                detail="Non-wildcard constraints require at least one value field"
            )
    
    constraint = repo.create_slot_constraint(
        slot_definition_id=slot_definition_id,
        domain=data.domain,
        key=data.key,
        operator=data.operator,
        value_string=data.value_string,
        value_number=data.value_number,
        value_boolean=data.value_boolean,
        is_wildcard=data.is_wildcard,
        sort_order=data.sort_order,
    )
    
    return SlotConstraintResponse.model_validate(constraint)


@router.patch(
    "/project-template-slot-constraints/{constraint_id}",
    response_model=SlotConstraintResponse,
)
def update_slot_constraint(
    constraint_id: uuid.UUID,
    data: SlotConstraintUpdate,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    constraint = repo.get_slot_constraint_by_id(constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Slot constraint not found")
    
    # Validate constraint if changing wildcard status
    if data.is_wildcard is not None:
        if not data.is_wildcard:
            # Becoming non-wildcard - need domain, key, operator, and value
            if not data.domain and not constraint.domain:
                raise HTTPException(
                    status_code=400,
                    detail="Non-wildcard constraints require domain"
                )
            if not data.key and not constraint.key:
                raise HTTPException(
                    status_code=400,
                    detail="Non-wildcard constraints require key"
                )
            if not data.operator and not constraint.operator:
                raise HTTPException(
                    status_code=400,
                    detail="Non-wildcard constraints require operator"
                )
            has_value = (
                (data.value_string is not None) or
                (data.value_number is not None) or
                (data.value_boolean is not None) or
                (constraint.value_string is not None) or
                (constraint.value_number is not None) or
                (constraint.value_boolean is not None)
            )
            if not has_value:
                raise HTTPException(
                    status_code=400,
                    detail="Non-wildcard constraints require at least one value field"
                )
    
    updated = repo.update_slot_constraint(
        constraint_id=constraint_id,
        domain=data.domain,
        key=data.key,
        operator=data.operator,
        value_string=data.value_string,
        value_number=data.value_number,
        value_boolean=data.value_boolean,
        is_wildcard=data.is_wildcard,
        sort_order=data.sort_order,
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Slot constraint not found")
    
    return SlotConstraintResponse.model_validate(updated)


@router.delete("/project-template-slot-constraints/{constraint_id}", status_code=204)
def delete_slot_constraint(
    constraint_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = ProjectTemplateRepository(db)
    if not repo.delete_slot_constraint(constraint_id):
        raise HTTPException(status_code=404, detail="Slot constraint not found")
