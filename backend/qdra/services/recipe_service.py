import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.recipe import Recipe
from models.slot import Slot, SlotKind
from models.option import Option
from models.parameter_constraint import ParameterConstraint, Operator
from models.recipe_parameter import RecipeParameter
from repositories.recipe_repository import RecipeRepository
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository
from repositories.project_repository import ProjectRepository
from repositories.recipe_parameter_repository import RecipeParameterRepository


class RecipeService:
    def __init__(self, db: Session):
        self.db = db
        self.recipe_repository = RecipeRepository(db)
        self.slot_repository = SlotRepository(db)
        self.option_repository = OptionRepository(db)
        self.constraint_repository = ParameterConstraintRepository(db)
        self.project_repository = ProjectRepository(db)
        self.recipe_parameter_repository = RecipeParameterRepository(db)

    def create_recipe(self, project_id: uuid.UUID) -> Recipe:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with id '{project_id}' not found")
        return self.recipe_repository.create(project_id)

    def get_recipe(self, recipe_id: uuid.UUID) -> Recipe:
        recipe = self.recipe_repository.get_by_id(recipe_id)
        if not recipe:
            raise ValueError(f"Recipe with id '{recipe_id}' not found")
        return recipe

    def list_recipes(self, project_id: uuid.UUID) -> List[Recipe]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with id '{project_id}' not found")
        return self.recipe_repository.list_by_project(project_id)

    def create_slot(self, recipe_id: uuid.UUID, kind: str) -> Slot:
        recipe = self.recipe_repository.get_by_id(recipe_id)
        if not recipe:
            raise ValueError(f"Recipe with id '{recipe_id}' not found")

        try:
            slot_kind = SlotKind(kind)
        except ValueError:
            raise ValueError(f"Invalid slot kind: {kind}. Must be CONSUMES, REQUIRES, or PRODUCES")

        return self.slot_repository.create(recipe_id, slot_kind)

    def create_option(self, slot_id: uuid.UUID, quantity: float) -> Option:
        slot = self.slot_repository.get_by_id(slot_id)
        if not slot:
            raise ValueError(f"Slot with id '{slot_id}' not found")
        return self.option_repository.create(slot_id, quantity)

    def create_constraint(
        self,
        option_id: uuid.UUID,
        domain: str,
        key: str,
        operator: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
        is_wildcard: bool = False,
    ) -> ParameterConstraint:
        option = self.option_repository.get_by_id(option_id)
        if not option:
            raise ValueError(f"Option with id '{option_id}' not found")

        try:
            op = Operator(operator)
        except ValueError:
            raise ValueError(f"Invalid operator: {operator}")

        return self.constraint_repository.create(
            option_id=option_id,
            domain=domain,
            key=key,
            operator=op,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
            is_wildcard=is_wildcard,
        )

    def add_parameter(
        self,
        recipe_id: uuid.UUID,
        domain: str,
        key: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> RecipeParameter:
        recipe = self.recipe_repository.get_by_id(recipe_id)
        if not recipe:
            raise ValueError(f"Recipe with id '{recipe_id}' not found")
        return self.recipe_parameter_repository.create(
            recipe_id=recipe_id,
            domain=domain,
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
        )

    def get_recipe_parameters(self, recipe_id: uuid.UUID) -> List[RecipeParameter]:
        recipe = self.recipe_repository.get_by_id(recipe_id)
        if not recipe:
            raise ValueError(f"Recipe with id '{recipe_id}' not found")
        return self.recipe_parameter_repository.list_by_recipe(recipe_id)

    def delete_parameter(self, parameter_id: uuid.UUID) -> bool:
        return self.recipe_parameter_repository.delete(parameter_id)
