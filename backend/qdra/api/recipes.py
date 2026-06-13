import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.recipe_service import RecipeService
from services.recipe_evaluation_service import RecipeEvaluationService
from services.recipe_execution_service import RecipeExecutionService

router = APIRouter()


class RecipeCreate(BaseModel):
    name: str


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
    name: str
    slots: List[SlotBulkCreate] = []


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    name: str


class SlotCreate(BaseModel):
    kind: str


class SlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    recipe_id: uuid.UUID
    kind: str


class OptionCreate(BaseModel):
    quantity: float


class OptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slot_id: uuid.UUID
    quantity: float


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
def create_recipe(project_id: uuid.UUID, recipe_data: RecipeCreate, db: Session = Depends(get_db)):
    service = RecipeService(db)
    try:
        recipe = service.create_recipe(project_id, recipe_data.name)
        return recipe
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/recipes/bulk", response_model=RecipeResponse, status_code=201)
def create_recipe_bulk(project_id: uuid.UUID, recipe_data: RecipeBulkCreate, db: Session = Depends(get_db)):
    service = RecipeService(db)
    try:
        recipe = service.create_recipe(project_id, recipe_data.name)
        
        for slot_data in recipe_data.slots:
            slot = service.create_slot(recipe.id, slot_data.kind)
            
            for option_data in slot_data.options:
                option = service.create_option(slot.id, option_data.quantity)
                
                for constraint_data in option_data.constraints:
                    service.create_constraint(
                        option_id=option.id,
                        domain=constraint_data.domain,
                        key=constraint_data.key,
                        operator=constraint_data.operator,
                        value_string=constraint_data.value_string,
                        value_number=constraint_data.value_number,
                        value_boolean=constraint_data.value_boolean,
                        is_wildcard=constraint_data.is_wildcard,
                    )
        
        return recipe
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/recipes", response_model=list[RecipeResponse])
def list_recipes(project_id: uuid.UUID, db: Session = Depends(get_db)):
    service = RecipeService(db)
    try:
        return service.list_recipes(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: uuid.UUID, db: Session = Depends(get_db)):
    service = RecipeService(db)
    try:
        return service.get_recipe(recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/recipes/{recipe_id}/slots", response_model=SlotResponse, status_code=201)
def create_slot(recipe_id: uuid.UUID, slot_data: SlotCreate, db: Session = Depends(get_db)):
    service = RecipeService(db)
    try:
        slot = service.create_slot(recipe_id, slot_data.kind)
        return slot
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/slots/{slot_id}/options", response_model=OptionResponse, status_code=201)
def create_option(slot_id: uuid.UUID, option_data: OptionCreate, db: Session = Depends(get_db)):
    service = RecipeService(db)
    try:
        option = service.create_option(slot_id, option_data.quantity)
        return option
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/options/{option_id}/constraints", response_model=ConstraintResponse, status_code=201)
def create_constraint(
    option_id: uuid.UUID, constraint_data: ConstraintCreate, db: Session = Depends(get_db)
):
    service = RecipeService(db)
    try:
        constraint = service.create_constraint(
            option_id=option_id,
            domain=constraint_data.domain,
            key=constraint_data.key,
            operator=constraint_data.operator,
            value_string=constraint_data.value_string,
            value_number=constraint_data.value_number,
            value_boolean=constraint_data.value_boolean,
            is_wildcard=constraint_data.is_wildcard,
        )
        return constraint
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recipes/{recipe_id}/evaluate", response_model=RecipeEvaluationResponse)
def evaluate_recipe(
    recipe_id: uuid.UUID, evaluation_data: RecipeEvaluationRequest, db: Session = Depends(get_db)
):
    service = RecipeEvaluationService(db)
    result = service.evaluate_recipe(recipe_id, evaluation_data.materials)
    
    return RecipeEvaluationResponse(
        success=result.success,
        recipe_id=result.recipe_id,
        slot_results=[
            SlotMatchResultResponse(
                slot_id=slot.slot_id,
                success=slot.success,
                matched_option_id=slot.matched_option_id,
                allocated_materials=slot.allocated_materials
            )
            for slot in result.slot_results
        ],
        allocations=[
            AllocationResponse(
                material_id=alloc.material_id,
                slot_id=alloc.slot_id,
                option_id=alloc.option_id
            )
            for alloc in result.allocations
        ]
    )


@router.post("/recipes/{recipe_id}/execute", response_model=RecipeExecutionResponse)
def execute_recipe(
    recipe_id: uuid.UUID, execution_data: RecipeExecutionRequest, db: Session = Depends(get_db)
):
    service = RecipeExecutionService(db)
    result = service.execute_recipe(recipe_id, execution_data.materials)
    
    return RecipeExecutionResponse(
        success=result.success,
        recipe_id=result.recipe_id,
        consumed_material_ids=result.consumed_material_ids,
        required_material_ids=result.required_material_ids,
        produced_material_ids=result.produced_material_ids,
        state_before=result.state_before,
        state_after=result.state_after
    )
