"""Compatibility wrapper: recipes are entities with kind='recipe'."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.entity_service import EntityService
from services.recipe_evaluation_service import RecipeEvaluationService
from services.recipe_execution_service import RecipeExecutionService
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository
from repositories.project_template_repository import ProjectTemplateRepository
from repositories.project_repository import ProjectRepository
from infrastructure.security.permission_checker import (
    require_can_create_recipe,
    require_can_edit_recipe,
    require_can_delete_recipe,
)

router = APIRouter(prefix="/api")


def _resolve_entity_type_id(
    project_id: uuid.UUID,
    entity_type_id: Optional[uuid.UUID],
    db: Session,
) -> uuid.UUID:
    if entity_type_id:
        return entity_type_id
    project = ProjectRepository(db).get_by_id(project_id)
    if not project:
        raise ValueError(f"Project '{project_id}' not found")
    types = ProjectTemplateRepository(db).list_entity_types(
        project.project_template_id, kind="recipe"
    )
    if not types:
        raise ValueError("No recipe entity types defined in the project template")
    return types[0].id


class RecipeCreate(BaseModel):
    entity_type_id: Optional[uuid.UUID] = None


class RecipeParameterCreate(BaseModel):
    domain: str
    key: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None


class ConstraintCreate(BaseModel):
    domain: str
    key: str
    operator: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False


class OptionBulkCreate(BaseModel):
    quantity: float
    constraints: List[ConstraintCreate] = []


class SlotBulkCreate(BaseModel):
    kind: str
    options: List[OptionBulkCreate] = []


class RecipeBulkCreate(BaseModel):
    entity_type_id: Optional[uuid.UUID] = None
    parameters: List[RecipeParameterCreate] = []
    slots: List[SlotBulkCreate] = []


class RecipeParameterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entity_id: uuid.UUID
    domain: str
    key: str
    value_string: Optional[str]
    value_number: Optional[float]
    value_boolean: Optional[bool]
    created_at: datetime
    updated_at: datetime


class RecipeResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    entity_type_id: uuid.UUID
    group: str = ""
    kind: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    image: Optional[Dict[str, Any]] = None


class OptionMaterialsResponse(BaseModel):
    option_id: str
    quantity: float
    matching_material_ids: List[str]


class SlotMaterialsResponse(BaseModel):
    slot_id: str
    kind: str
    options: List[OptionMaterialsResponse]


class RecipeSlotMaterialsResponse(BaseModel):
    consumes: List[SlotMaterialsResponse]
    produces: List[SlotMaterialsResponse]
    requires: List[SlotMaterialsResponse]


class SlotCreate(BaseModel):
    kind: str
    sort_order: int = 0


class SlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    recipe_entity_id: uuid.UUID
    kind: str
    sort_order: int


class OptionCreate(BaseModel):
    quantity: float
    sort_order: int = 0


class OptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slot_id: uuid.UUID
    quantity: Optional[float]
    sort_order: int


class ConstraintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    option_id: uuid.UUID
    domain: str
    key: str
    operator: str
    value_string: Optional[str]
    value_number: Optional[float]
    value_boolean: Optional[bool]
    is_wildcard: bool


class RecipeEvaluationRequest(BaseModel):
    materials: List[uuid.UUID]


class AllocationResponse(BaseModel):
    material_id: uuid.UUID
    slot_id: uuid.UUID
    option_id: uuid.UUID


class SlotMatchResultResponse(BaseModel):
    slot_id: uuid.UUID
    success: bool
    matched_option_id: Optional[uuid.UUID] = None
    allocated_materials: List[uuid.UUID] = []


class RecipeEvaluationResponse(BaseModel):
    success: bool
    recipe_id: uuid.UUID
    slot_results: List[SlotMatchResultResponse]
    allocations: List[AllocationResponse]


class RecipeExecutionRequest(BaseModel):
    materials: List[uuid.UUID]


class RecipeExecutionResponse(BaseModel):
    success: bool
    recipe_id: uuid.UUID
    consumed_material_ids: List[uuid.UUID]
    required_material_ids: List[uuid.UUID]
    produced_material_ids: List[uuid.UUID]
    state_before: List[uuid.UUID]
    state_after: List[uuid.UUID]


@router.post("/projects/{project_id}/recipes", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    project_id: uuid.UUID,
    data: RecipeCreate,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_create_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipes_added

    service = EntityService(db)
    try:
        et_id = _resolve_entity_type_id(project_id, data.entity_type_id, db)
        entity = service.create_entity(project_id=project_id, entity_type_id=et_id)
        # Invalidate all relationship caches so the solver sees the new recipe
        recipes_added([entity.id], project_id)
        return await service.get_entity(entity.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/recipes/bulk", response_model=RecipeResponse, status_code=201)
async def create_recipe_bulk(
    project_id: uuid.UUID,
    recipe_data: RecipeBulkCreate,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_create_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipes_added

    service = EntityService(db)
    slot_repo = SlotRepository(db)
    option_repo = OptionRepository(db)
    constraint_repo = ParameterConstraintRepository(db)
    try:
        et_id = _resolve_entity_type_id(project_id, recipe_data.entity_type_id, db)
        entity = service.create_entity(project_id=project_id, entity_type_id=et_id)

        for p in recipe_data.parameters:
            service.add_parameter(
                entity_id=entity.id, domain=p.domain, key=p.key,
                value_string=p.value_string, value_number=p.value_number,
                value_boolean=p.value_boolean,
            )

        for slot_data in recipe_data.slots:
            slot = slot_repo.create(
                recipe_entity_id=entity.id,
                kind=slot_data.kind.lower(),
            )
            for opt in slot_data.options:
                option = option_repo.create(slot_id=slot.id, quantity=opt.quantity)
                for c in opt.constraints:
                    constraint_repo.create(
                        option_id=option.id,
                        domain=c.domain, key=c.key, operator=c.operator,
                        value_string=c.value_string, value_number=c.value_number,
                        value_boolean=c.value_boolean, is_wildcard=c.is_wildcard,
                    )

        # Invalidate all relationship caches so the solver sees the new recipe
        recipes_added([entity.id], project_id)
        return await service.get_entity(entity.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/recipes", response_model=List[RecipeResponse])
async def list_recipes(project_id: uuid.UUID, db: Session = Depends(get_db)):
    service = EntityService(db)
    try:
        return await service.list_entities(project_id=project_id, kind="recipe")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/recipes/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    project_id: uuid.UUID, recipe_id: uuid.UUID, db: Session = Depends(get_db)
):
    service = EntityService(db)
    try:
        return await service.get_entity(recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/projects/{project_id}/recipes/{recipe_id}", status_code=204)
def delete_recipe(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_delete_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipes_edited

    service = EntityService(db)
    try:
        service.delete_entity(recipe_id)
        # Invalidate all relationship caches for this project
        recipes_edited([recipe_id], project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/recipes/{recipe_id}/slots", response_model=SlotResponse, status_code=201)
def create_slot(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    slot_data: SlotCreate,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_slots_changed

    slot_repo = SlotRepository(db)
    slot = slot_repo.create(
        recipe_entity_id=recipe_id,
        kind=slot_data.kind.lower(),
        sort_order=slot_data.sort_order,
    )
    # Invalidate all relationship caches for this project
    recipe_slots_changed(recipe_id, project_id)
    return slot


@router.post("/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options", response_model=OptionResponse, status_code=201)
def create_option(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    slot_id: uuid.UUID,
    option_data: OptionCreate,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_slots_changed

    option_repo = OptionRepository(db)
    option = option_repo.create(
        slot_id=slot_id,
        quantity=option_data.quantity,
        sort_order=option_data.sort_order,
    )
    # Invalidate all relationship caches for this project
    recipe_slots_changed(recipe_id, project_id)
    return option


@router.post(
    "/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options/{option_id}/constraints",
    response_model=ConstraintResponse,
    status_code=201,
)
def create_constraint(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    slot_id: uuid.UUID,
    option_id: uuid.UUID,
    constraint_data: ConstraintCreate,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_slots_changed

    constraint_repo = ParameterConstraintRepository(db)
    constraint = constraint_repo.create(
        option_id=option_id,
        domain=constraint_data.domain, key=constraint_data.key,
        operator=constraint_data.operator,
        value_string=constraint_data.value_string,
        value_number=constraint_data.value_number,
        value_boolean=constraint_data.value_boolean,
        is_wildcard=constraint_data.is_wildcard,
    )
    # Invalidate all relationship caches for this project
    recipe_slots_changed(recipe_id, project_id)
    return constraint


@router.post("/projects/{project_id}/recipes/{recipe_id}/evaluate", response_model=RecipeEvaluationResponse)
def evaluate_recipe(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    evaluation_data: RecipeEvaluationRequest,
    db: Session = Depends(get_db),
):
    service = RecipeEvaluationService(db)
    result = service.evaluate_recipe(recipe_id, evaluation_data.materials)
    return RecipeEvaluationResponse(
        success=result.success,
        recipe_id=result.recipe_id,
        slot_results=[
            SlotMatchResultResponse(
                slot_id=s.slot_id, success=s.success,
                matched_option_id=s.matched_option_id,
                allocated_materials=s.allocated_materials,
            )
            for s in result.slot_results
        ],
        allocations=[
            AllocationResponse(
                material_id=a.material_id, slot_id=a.slot_id, option_id=a.option_id
            )
            for a in result.allocations
        ],
    )


@router.get("/projects/{project_id}/recipes/{recipe_id}/materials", response_model=RecipeSlotMaterialsResponse)
def get_recipe_materials(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = RecipeEvaluationService(db)
    result = service.find_materials_for_recipe_slots(recipe_id, project_id)
    return RecipeSlotMaterialsResponse(
        consumes=[SlotMaterialsResponse(**slot) for slot in result["consumes"]],
        produces=[SlotMaterialsResponse(**slot) for slot in result["produces"]],
        requires=[SlotMaterialsResponse(**slot) for slot in result["requires"]],
    )


@router.post("/projects/{project_id}/recipes/{recipe_id}/execute", response_model=RecipeExecutionResponse)
def execute_recipe(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    execution_data: RecipeExecutionRequest,
    db: Session = Depends(get_db),
):
    service = RecipeExecutionService(db)
    result = service.execute_recipe(recipe_id, execution_data.materials)
    return RecipeExecutionResponse(
        success=result.success, recipe_id=result.recipe_id,
        consumed_material_ids=result.consumed_material_ids,
        required_material_ids=result.required_material_ids,
        produced_material_ids=result.produced_material_ids,
        state_before=result.state_before, state_after=result.state_after,
    )


@router.get("/projects/{project_id}/recipes/{recipe_id}/slots", response_model=List[SlotResponse])
def list_recipe_slots(
    project_id: uuid.UUID, recipe_id: uuid.UUID, db: Session = Depends(get_db)
):
    slot_repo = SlotRepository(db)
    return slot_repo.list_by_recipe_entity(recipe_id)


@router.get("/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options", response_model=List[OptionResponse])
def list_recipe_options(
    project_id: uuid.UUID, recipe_id: uuid.UUID, slot_id: uuid.UUID, db: Session = Depends(get_db)
):
    option_repo = OptionRepository(db)
    return option_repo.list_by_slot(slot_id)


@router.get(
    "/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options/{option_id}/constraints",
    response_model=List[ConstraintResponse],
)
def list_recipe_constraints(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    slot_id: uuid.UUID,
    option_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    constraint_repo = ParameterConstraintRepository(db)
    return constraint_repo.list_by_option(option_id)


@router.delete("/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}", status_code=204)
def delete_recipe_slot(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_slots_changed

    slot_repo = SlotRepository(db)
    if not slot_repo.delete(slot_id):
        raise HTTPException(status_code=404, detail="Slot not found")
    # Invalidate all relationship caches for this project
    recipe_slots_changed(recipe_id, project_id)


@router.delete("/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options/{option_id}", status_code=204)
def delete_recipe_option(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    slot_id: uuid.UUID,
    option_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_slots_changed

    option_repo = OptionRepository(db)
    option = option_repo.get_by_id(option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")
    db.delete(option)
    db.commit()
    # Invalidate all relationship caches for this project
    recipe_slots_changed(recipe_id, project_id)


@router.delete("/projects/{project_id}/recipes/{recipe_id}/slots/{slot_id}/options/{option_id}/constraints/{constraint_id}", status_code=204)
def delete_recipe_constraint(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    slot_id: uuid.UUID,
    option_id: uuid.UUID,
    constraint_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_slots_changed

    constraint_repo = ParameterConstraintRepository(db)
    constraint = constraint_repo.get_by_id(constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    db.delete(constraint)
    db.commit()
    # Invalidate all relationship caches for this project
    recipe_slots_changed(recipe_id, project_id)


@router.post("/projects/{project_id}/recipes/{recipe_id}/parameters", response_model=RecipeParameterResponse, status_code=201)
def add_recipe_parameter(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    param_data: RecipeParameterCreate,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_parameters_changed

    service = EntityService(db)
    try:
        result = service.add_parameter(
            entity_id=recipe_id, domain=param_data.domain, key=param_data.key,
            value_string=param_data.value_string, value_number=param_data.value_number,
            value_boolean=param_data.value_boolean,
        )
        # Invalidate all relationship caches for this project
        recipe_parameters_changed(recipe_id, project_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/recipes/{recipe_id}/parameters", response_model=List[RecipeParameterResponse])
def list_recipe_parameters(
    project_id: uuid.UUID, recipe_id: uuid.UUID, db: Session = Depends(get_db)
):
    service = EntityService(db)
    try:
        return service.get_entity_parameters(recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/projects/{project_id}/recipes/{recipe_id}/parameters/{parameter_id}", status_code=204)
def delete_recipe_parameter(
    project_id: uuid.UUID,
    recipe_id: uuid.UUID,
    parameter_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(require_can_edit_recipe),
):
    from qdra.infrastructure.cache.invalidation_controller import recipe_parameters_changed

    service = EntityService(db)
    if not service.delete_parameter(parameter_id):
        raise HTTPException(status_code=404, detail="Parameter not found")
    # Invalidate all relationship caches for this project
    recipe_parameters_changed(recipe_id, project_id)
