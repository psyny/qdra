import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.project_template import (
    ProjectTemplate,
    ProjectTemplateMaterialType,
    ProjectTemplateRecipeType,
    ProjectTemplateParameterDefinition,
)


class ProjectTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    # ProjectTemplate CRUD

    def create(self, name: str, description: Optional[str] = None, is_builtin: bool = False) -> ProjectTemplate:
        template = ProjectTemplate(name=name, description=description, is_builtin=is_builtin)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_id(self, template_id: uuid.UUID) -> Optional[ProjectTemplate]:
        return self.db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()

    def list_all(self) -> List[ProjectTemplate]:
        return self.db.query(ProjectTemplate).all()

    def update(self, template_id: uuid.UUID, name: Optional[str] = None, description: Optional[str] = None) -> Optional[ProjectTemplate]:
        template = self.get_by_id(template_id)
        if template:
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            self.db.commit()
            self.db.refresh(template)
        return template

    def delete(self, template_id: uuid.UUID) -> bool:
        template = self.get_by_id(template_id)
        if template:
            self.db.delete(template)
            self.db.commit()
            return True
        return False

    # ProjectTemplateMaterialType CRUD

    def create_material_type(
        self,
        project_template_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateMaterialType:
        material_type = ProjectTemplateMaterialType(
            project_template_id=project_template_id,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self.db.add(material_type)
        self.db.commit()
        self.db.refresh(material_type)
        return material_type

    def get_material_type_by_id(self, material_type_id: uuid.UUID) -> Optional[ProjectTemplateMaterialType]:
        return self.db.query(ProjectTemplateMaterialType).filter(ProjectTemplateMaterialType.id == material_type_id).first()

    def list_material_types(self, project_template_id: uuid.UUID) -> List[ProjectTemplateMaterialType]:
        return (
            self.db.query(ProjectTemplateMaterialType)
            .filter(ProjectTemplateMaterialType.project_template_id == project_template_id)
            .order_by(ProjectTemplateMaterialType.sort_order)
            .all()
        )

    def delete_material_type(self, material_type_id: uuid.UUID) -> bool:
        material_type = self.get_material_type_by_id(material_type_id)
        if material_type:
            self.db.delete(material_type)
            self.db.commit()
            return True
        return False

    # ProjectTemplateRecipeType CRUD

    def create_recipe_type(
        self,
        project_template_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateRecipeType:
        recipe_type = ProjectTemplateRecipeType(
            project_template_id=project_template_id,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self.db.add(recipe_type)
        self.db.commit()
        self.db.refresh(recipe_type)
        return recipe_type

    def get_recipe_type_by_id(self, recipe_type_id: uuid.UUID) -> Optional[ProjectTemplateRecipeType]:
        return self.db.query(ProjectTemplateRecipeType).filter(ProjectTemplateRecipeType.id == recipe_type_id).first()

    def list_recipe_types(self, project_template_id: uuid.UUID) -> List[ProjectTemplateRecipeType]:
        return (
            self.db.query(ProjectTemplateRecipeType)
            .filter(ProjectTemplateRecipeType.project_template_id == project_template_id)
            .order_by(ProjectTemplateRecipeType.sort_order)
            .all()
        )

    def delete_recipe_type(self, recipe_type_id: uuid.UUID) -> bool:
        recipe_type = self.get_recipe_type_by_id(recipe_type_id)
        if recipe_type:
            self.db.delete(recipe_type)
            self.db.commit()
            return True
        return False

    # ProjectTemplateParameterDefinition CRUD

    def create_parameter_definition(
        self,
        project_template_id: uuid.UUID,
        owner_kind: str,
        owner_type_id: uuid.UUID,
        domain: str,
        key: str,
        value_type: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        required: bool = False,
        sort_order: int = 0,
    ) -> ProjectTemplateParameterDefinition:
        param_def = ProjectTemplateParameterDefinition(
            project_template_id=project_template_id,
            owner_kind=owner_kind,
            owner_type_id=owner_type_id,
            domain=domain,
            key=key,
            value_type=value_type,
            label=label,
            description=description,
            required=required,
            sort_order=sort_order,
        )
        self.db.add(param_def)
        self.db.commit()
        self.db.refresh(param_def)
        return param_def

    def get_parameter_definition_by_id(self, param_def_id: uuid.UUID) -> Optional[ProjectTemplateParameterDefinition]:
        return self.db.query(ProjectTemplateParameterDefinition).filter(ProjectTemplateParameterDefinition.id == param_def_id).first()

    def list_parameter_definitions(self, project_template_id: uuid.UUID) -> List[ProjectTemplateParameterDefinition]:
        return (
            self.db.query(ProjectTemplateParameterDefinition)
            .filter(ProjectTemplateParameterDefinition.project_template_id == project_template_id)
            .order_by(ProjectTemplateParameterDefinition.sort_order)
            .all()
        )

    def list_parameter_definitions_by_owner(
        self, project_template_id: uuid.UUID, owner_kind: str, owner_type_id: uuid.UUID
    ) -> List[ProjectTemplateParameterDefinition]:
        return (
            self.db.query(ProjectTemplateParameterDefinition)
            .filter(
                ProjectTemplateParameterDefinition.project_template_id == project_template_id,
                ProjectTemplateParameterDefinition.owner_kind == owner_kind,
                ProjectTemplateParameterDefinition.owner_type_id == owner_type_id,
            )
            .order_by(ProjectTemplateParameterDefinition.sort_order)
            .all()
        )

    def delete_parameter_definition(self, param_def_id: uuid.UUID) -> bool:
        param_def = self.get_parameter_definition_by_id(param_def_id)
        if param_def:
            self.db.delete(param_def)
            self.db.commit()
            return True
        return False
