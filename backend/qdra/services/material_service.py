import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.material import Material
from models.parameter import Parameter
from repositories.material_repository import MaterialRepository
from repositories.parameter_repository import ParameterRepository
from repositories.project_repository import ProjectRepository


class MaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.material_repository = MaterialRepository(db)
        self.parameter_repository = ParameterRepository(db)
        self.project_repository = ProjectRepository(db)

    def create_material(self, project_id: uuid.UUID) -> Material:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with id '{project_id}' not found")
        return self.material_repository.create(project_id)

    def get_material(self, material_id: uuid.UUID) -> Material:
        material = self.material_repository.get_by_id(material_id)
        if not material:
            raise ValueError(f"Material with id '{material_id}' not found")
        return material

    def list_materials(self, project_id: uuid.UUID) -> List[Material]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with id '{project_id}' not found")
        return self.material_repository.list_by_project(project_id)

    def add_parameter(
        self,
        material_id: uuid.UUID,
        domain: str,
        key: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> Parameter:
        material = self.material_repository.get_by_id(material_id)
        if not material:
            raise ValueError(f"Material with id '{material_id}' not found")

        # Validate exactly one value is provided
        values_provided = sum(
            [
                value_string is not None,
                value_number is not None,
                value_boolean is not None,
            ]
        )
        if values_provided != 1:
            raise ValueError("Exactly one value must be provided")

        return self.parameter_repository.create(
            material_id=material_id,
            domain=domain,
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
        )

    def delete_parameter(self, parameter_id: uuid.UUID) -> bool:
        return self.parameter_repository.delete(parameter_id)

    def get_material_parameters(self, material_id: uuid.UUID) -> List[Parameter]:
        material = self.material_repository.get_by_id(material_id)
        if not material:
            raise ValueError(f"Material with id '{material_id}' not found")
        return self.parameter_repository.list_by_material(material_id)
