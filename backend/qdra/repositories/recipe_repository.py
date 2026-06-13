import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.recipe import Recipe


class RecipeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project_id: uuid.UUID, name: str) -> Recipe:
        recipe = Recipe(project_id=project_id, name=name)
        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

    def get_by_id(self, recipe_id: uuid.UUID) -> Optional[Recipe]:
        return self.db.query(Recipe).filter(Recipe.id == recipe_id).first()

    def list_by_project(self, project_id: uuid.UUID) -> List[Recipe]:
        return self.db.query(Recipe).filter(Recipe.project_id == project_id).all()
