import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str) -> Project:
        project = Project(name=name)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def list_all(self) -> List[Project]:
        return self.db.query(Project).all()
