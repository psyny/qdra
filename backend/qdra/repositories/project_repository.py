import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, project_template_id: uuid.UUID) -> Project:
        project = Project(name=name, project_template_id=project_template_id)
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
