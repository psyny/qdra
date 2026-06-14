import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.recipe_parameter import RecipeParameter


class RecipeParameterRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        recipe_id: uuid.UUID,
        domain: str,
        key: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> RecipeParameter:
        parameter = RecipeParameter(
            recipe_id=recipe_id,
            domain=domain,
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
        )
        self.db.add(parameter)
        self.db.commit()
        self.db.refresh(parameter)
        return parameter

    def get_by_id(self, parameter_id: uuid.UUID) -> Optional[RecipeParameter]:
        return self.db.query(RecipeParameter).filter(RecipeParameter.id == parameter_id).first()

    def delete(self, parameter_id: uuid.UUID) -> bool:
        parameter = self.get_by_id(parameter_id)
        if parameter:
            self.db.delete(parameter)
            self.db.commit()
            return True
        return False

    def list_by_recipe(self, recipe_id: uuid.UUID) -> List[RecipeParameter]:
        return self.db.query(RecipeParameter).filter(RecipeParameter.recipe_id == recipe_id).all()
