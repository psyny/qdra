import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db.session import get_db
from services.recipe_service import RecipeService

router = APIRouter()


class RecipeCreate(BaseModel):
    name: str


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


class ConstraintCreate(BaseModel):
    domain: str
    key: str
    operator: str
    value_string: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    is_wildcard: bool = False


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


@router.post("/projects/{project_id}/recipes", response_model=RecipeResponse, status_code=201)
def create_recipe(project_id: uuid.UUID, recipe_data: RecipeCreate, db: Session = Depends(get_db)):
    service = RecipeService(db)
    try:
        recipe = service.create_recipe(project_id, recipe_data.name)
        return recipe
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
