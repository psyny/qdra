import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.project import Project
from models.entity import Entity
from models.image_asset import ImageAsset


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, project_template_id: uuid.UUID, image_size_px: int = 256) -> Project:
        project = Project(
            name=name, 
            project_template_id=project_template_id,
            image_size_px=image_size_px
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def list_all(self) -> List[Project]:
        return self.db.query(Project).all()

    def update_template(self, project_id: uuid.UUID, project_template_id: uuid.UUID) -> Optional[Project]:
        project = self.get_by_id(project_id)
        if project:
            project.project_template_id = project_template_id
            self.db.commit()
            self.db.refresh(project)
        return project

    def update(self, project_id: uuid.UUID, name: Optional[str] = None, image_size_px: Optional[int] = None) -> Optional[Project]:
        project = self.get_by_id(project_id)
        if project:
            if name is not None:
                project.name = name
            if image_size_px is not None:
                project.image_size_px = image_size_px
            self.db.commit()
            self.db.refresh(project)
        return project

    def delete(self, project_id: uuid.UUID) -> bool:
        project = self.get_by_id(project_id)
        if not project:
            return False
        
        # Get all images for all entities in the project for storage cleanup
        entities = self.db.query(Entity).filter(Entity.project_id == project_id).all()
        for entity in entities:
            images = self.db.query(ImageAsset).filter(ImageAsset.entity_id == entity.id).all()
            for image in images:
                # Return images for caller to delete from storage
                # We'll handle this in the service layer
                pass
        
        # Delete all entities (cascade will handle image records)
        for entity in entities:
            self.db.delete(entity)
        
        self.db.delete(project)
        self.db.commit()
        return True
