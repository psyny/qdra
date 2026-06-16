import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.project_template import (
    ProjectTemplate,
    ProjectTemplateMaterialType,
    ProjectTemplateRecipeType,
    ProjectTemplateParameterDefinition,
    ProjectTemplateView,
    ProjectTemplateViewConfig,
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
            # Check if template is used by any projects
            from models.project import Project
            project_count = self.db.query(Project).filter(Project.project_template_id == template_id).count()
            if project_count > 0:
                return False  # Cannot delete, template is in use
            self.db.delete(template)
            self.db.commit()
            return True
        return False

    def clone_template(self, template_id: uuid.UUID, name: Optional[str] = None) -> Optional[ProjectTemplate]:
        source = self.get_by_id(template_id)
        if not source:
            return None

        clone_name = name or f"{source.name} Copy"
        clone = ProjectTemplate(
            name=clone_name,
            description=source.description,
            is_builtin=False,
        )
        self.db.add(clone)
        self.db.commit()
        self.db.refresh(clone)

        # Clone material types
        for material_type in self.list_material_types(template_id):
            self.create_material_type(
                project_template_id=clone.id,
                name=material_type.name,
                description=material_type.description,
                sort_order=material_type.sort_order,
            )

        # Clone recipe types
        for recipe_type in self.list_recipe_types(template_id):
            self.create_recipe_type(
                project_template_id=clone.id,
                name=recipe_type.name,
                description=recipe_type.description,
                sort_order=recipe_type.sort_order,
            )

        # Clone parameter definitions
        for param_def in self.list_parameter_definitions(template_id):
            self.create_parameter_definition(
                project_template_id=clone.id,
                owner_kind=param_def.owner_kind,
                owner_type_id=self._map_owner_id(param_def.owner_kind, param_def.owner_type_id, template_id, clone.id),
                domain=param_def.domain,
                key=param_def.key,
                value_type=param_def.value_type,
                label=param_def.label,
                description=param_def.description,
                required=param_def.required,
                sort_order=param_def.sort_order,
                is_label=param_def.is_label,
                is_unique=param_def.is_unique,
                is_searchable=param_def.is_searchable,
                is_hidden=param_def.is_hidden,
                default_value=param_def.default_value,
                validation=param_def.validation,
            )

        # Clone views
        for view in self.list_views(template_id):
            new_view = self.create_view(
                project_template_id=clone.id,
                view_name=view.view_name,
                sort_order=view.sort_order,
            )
            for config in self.list_view_configs(view.id):
                self.create_view_config(
                    view_id=new_view.id,
                    entity_type=config.entity_type,
                    filter_params=config.filter_params,
                    slots=config.slots,
                    sort_order=config.sort_order,
                )

        return clone

    def _map_owner_id(self, owner_kind: str, old_owner_id: uuid.UUID, old_template_id: uuid.UUID, new_template_id: uuid.UUID) -> uuid.UUID:
        """Map an owner_type_id from the source template to the cloned template."""
        if owner_kind == "material_type":
            old_type = self.get_material_type_by_id(old_owner_id)
            if old_type and old_type.project_template_id == old_template_id:
                # Find the corresponding new material type by name
                new_types = self.list_material_types(new_template_id)
                for new_type in new_types:
                    if new_type.name == old_type.name:
                        return new_type.id
        elif owner_kind == "recipe_type":
            old_type = self.get_recipe_type_by_id(old_owner_id)
            if old_type and old_type.project_template_id == old_template_id:
                # Find the corresponding new recipe type by name
                new_types = self.list_recipe_types(new_template_id)
                for new_type in new_types:
                    if new_type.name == old_type.name:
                        return new_type.id
        return old_owner_id  # Fallback, should not happen

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
        is_label: bool = False,
        is_unique: bool = False,
        is_searchable: bool = False,
        is_hidden: bool = False,
        default_value: Optional[str] = None,
        validation: Optional[Dict[str, Any]] = None,
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
            is_label=is_label,
            is_unique=is_unique,
            is_searchable=is_searchable,
            is_hidden=is_hidden,
            default_value=default_value,
            validation=validation,
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

    # ProjectTemplateView CRUD

    def create_view(
        self,
        project_template_id: uuid.UUID,
        view_name: str,
        sort_order: int = 0,
    ) -> ProjectTemplateView:
        view = ProjectTemplateView(
            project_template_id=project_template_id,
            view_name=view_name,
            sort_order=sort_order,
        )
        self.db.add(view)
        self.db.commit()
        self.db.refresh(view)
        return view

    def get_view_by_id(self, view_id: uuid.UUID) -> Optional[ProjectTemplateView]:
        return self.db.query(ProjectTemplateView).filter(ProjectTemplateView.id == view_id).first()

    def list_views(self, project_template_id: uuid.UUID) -> List[ProjectTemplateView]:
        return (
            self.db.query(ProjectTemplateView)
            .filter(ProjectTemplateView.project_template_id == project_template_id)
            .order_by(ProjectTemplateView.sort_order)
            .all()
        )

    def delete_view(self, view_id: uuid.UUID) -> bool:
        view = self.get_view_by_id(view_id)
        if view:
            self.db.delete(view)
            self.db.commit()
            return True
        return False

    # ProjectTemplateViewConfig CRUD

    def create_view_config(
        self,
        view_id: uuid.UUID,
        entity_type: str,
        slots: List[Dict[str, Any]],
        filter_params: Optional[List[Dict[str, Any]]] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateViewConfig:
        config = ProjectTemplateViewConfig(
            view_id=view_id,
            entity_type=entity_type,
            filter_params=filter_params,
            slots=slots,
            sort_order=sort_order,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_view_config_by_id(self, config_id: uuid.UUID) -> Optional[ProjectTemplateViewConfig]:
        return self.db.query(ProjectTemplateViewConfig).filter(ProjectTemplateViewConfig.id == config_id).first()

    def list_view_configs(self, view_id: uuid.UUID) -> List[ProjectTemplateViewConfig]:
        return (
            self.db.query(ProjectTemplateViewConfig)
            .filter(ProjectTemplateViewConfig.view_id == view_id)
            .order_by(ProjectTemplateViewConfig.sort_order)
            .all()
        )

    def delete_view_config(self, config_id: uuid.UUID) -> bool:
        config = self.get_view_config_by_id(config_id)
        if config:
            self.db.delete(config)
            self.db.commit()
            return True
        return False
