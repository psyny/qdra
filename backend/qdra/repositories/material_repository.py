import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.material import Material


class MaterialRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project_id: uuid.UUID) -> Material:
        material = Material(project_id=project_id)
        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)
        return material

    def get_by_id(self, material_id: uuid.UUID) -> Optional[Material]:
        return self.db.query(Material).filter(Material.id == material_id).first()

    def list_by_project(self, project_id: uuid.UUID) -> List[Material]:
        return self.db.query(Material).filter(Material.project_id == project_id).all()
