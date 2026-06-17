import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.project_template import (
    ProjectTemplate,
    ProjectTemplateEntityType,
    ProjectTemplateParameterDefinition,
    ProjectTemplateView,
    ProjectTemplateViewConfig,
)


class ProjectTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    # ProjectTemplate CRUD

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        is_builtin: bool = False,
    ) -> ProjectTemplate:
        template = ProjectTemplate(
            name=name,
            description=description,
            is_builtin=is_builtin,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_id(self, template_id: uuid.UUID) -> Optional[ProjectTemplate]:
        return (
            self.db.query(ProjectTemplate)
            .filter(ProjectTemplate.id == template_id)
            .first()
        )

    def list_all(self) -> List[ProjectTemplate]:
        return self.db.query(ProjectTemplate).all()

    def update(
        self,
        template_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[ProjectTemplate]:
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
            from models.project import Project
            project_count = (
                self.db.query(Project)
                .filter(Project.project_template_id == template_id)
                .count()
            )
            if project_count > 0:
                return False
            self.db.delete(template)
            self.db.commit()
            return True
        return False

    def clone_template(
        self, template_id: uuid.UUID, name: Optional[str] = None
    ) -> Optional[ProjectTemplate]:
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

        # id mapping from old entity_type_id -> new entity_type_id
        entity_type_id_map: Dict[uuid.UUID, uuid.UUID] = {}

        for et in self.list_entity_types(template_id):
            new_et = self.create_entity_type(
                project_template_id=clone.id,
                kind=et.kind,
                name=et.name,
                description=et.description,
                sort_order=et.sort_order,
            )
            entity_type_id_map[et.id] = new_et.id

        for param_def in self.list_parameter_definitions(template_id):
            new_entity_type_id = entity_type_id_map.get(
                param_def.entity_type_id, param_def.entity_type_id
            )
            self.create_parameter_definition(
                project_template_id=clone.id,
                entity_type_id=new_entity_type_id,
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

        for view in self.list_views(template_id):
            new_view = self.create_view(
                project_template_id=clone.id,
                view_name=view.view_name,
                sort_order=view.sort_order,
            )
            for config in self.list_view_configs(view.id):
                new_et_id = (
                    entity_type_id_map.get(config.entity_type_id)
                    if config.entity_type_id
                    else None
                )
                self.create_view_config(
                    view_id=new_view.id,
                    entity_kind=config.entity_kind,
                    entity_type_id=new_et_id,
                    filter_params=config.filter_params,
                    slots=config.slots,
                    sort_order=config.sort_order,
                )

        return clone

    # ProjectTemplateEntityType CRUD

    def create_entity_type(
        self,
        project_template_id: uuid.UUID,
        kind: str,
        name: str,
        description: Optional[str] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateEntityType:
        entity_type = ProjectTemplateEntityType(
            project_template_id=project_template_id,
            kind=kind,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self.db.add(entity_type)
        self.db.commit()
        self.db.refresh(entity_type)
        return entity_type

    def get_entity_type_by_id(
        self, entity_type_id: uuid.UUID
    ) -> Optional[ProjectTemplateEntityType]:
        return (
            self.db.query(ProjectTemplateEntityType)
            .filter(ProjectTemplateEntityType.id == entity_type_id)
            .first()
        )

    def list_entity_types(
        self, project_template_id: uuid.UUID, kind: Optional[str] = None
    ) -> List[ProjectTemplateEntityType]:
        q = (
            self.db.query(ProjectTemplateEntityType)
            .filter(
                ProjectTemplateEntityType.project_template_id == project_template_id
            )
        )
        if kind is not None:
            q = q.filter(ProjectTemplateEntityType.kind == kind)
        return q.order_by(ProjectTemplateEntityType.sort_order).all()

    def update_entity_type(
        self,
        entity_type_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProjectTemplateEntityType]:
        entity_type = self.get_entity_type_by_id(entity_type_id)
        if entity_type:
            if name is not None:
                entity_type.name = name
            if description is not None:
                entity_type.description = description
            if sort_order is not None:
                entity_type.sort_order = sort_order
            self.db.commit()
            self.db.refresh(entity_type)
        return entity_type

    def delete_entity_type(self, entity_type_id: uuid.UUID) -> bool:
        entity_type = self.get_entity_type_by_id(entity_type_id)
        if entity_type:
            self.db.delete(entity_type)
            self.db.commit()
            return True
        return False

    # ProjectTemplateParameterDefinition CRUD

    def create_parameter_definition(
        self,
        project_template_id: uuid.UUID,
        entity_type_id: uuid.UUID,
        domain: str,
        key: str,
        value_type: str,
        label: str = "",
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
            entity_type_id=entity_type_id,
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

    def get_parameter_definition_by_id(
        self, param_def_id: uuid.UUID
    ) -> Optional[ProjectTemplateParameterDefinition]:
        return (
            self.db.query(ProjectTemplateParameterDefinition)
            .filter(ProjectTemplateParameterDefinition.id == param_def_id)
            .first()
        )

    def list_parameter_definitions(
        self, project_template_id: uuid.UUID
    ) -> List[ProjectTemplateParameterDefinition]:
        return (
            self.db.query(ProjectTemplateParameterDefinition)
            .filter(
                ProjectTemplateParameterDefinition.project_template_id
                == project_template_id
            )
            .order_by(ProjectTemplateParameterDefinition.sort_order)
            .all()
        )

    def list_parameter_definitions_by_entity_type(
        self, entity_type_id: uuid.UUID
    ) -> List[ProjectTemplateParameterDefinition]:
        return (
            self.db.query(ProjectTemplateParameterDefinition)
            .filter(
                ProjectTemplateParameterDefinition.entity_type_id == entity_type_id
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
        return (
            self.db.query(ProjectTemplateView)
            .filter(ProjectTemplateView.id == view_id)
            .first()
        )

    def list_views(
        self, project_template_id: uuid.UUID
    ) -> List[ProjectTemplateView]:
        return (
            self.db.query(ProjectTemplateView)
            .filter(
                ProjectTemplateView.project_template_id == project_template_id
            )
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
        entity_kind: Optional[str] = None,
        entity_type_id: Optional[uuid.UUID] = None,
        slots: Optional[List[Dict[str, Any]]] = None,
        filter_params: Optional[List[Dict[str, Any]]] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateViewConfig:
        config = ProjectTemplateViewConfig(
            view_id=view_id,
            entity_kind=entity_kind,
            entity_type_id=entity_type_id,
            filter_params=filter_params,
            slots=slots,
            sort_order=sort_order,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_view_config_by_id(
        self, config_id: uuid.UUID
    ) -> Optional[ProjectTemplateViewConfig]:
        return (
            self.db.query(ProjectTemplateViewConfig)
            .filter(ProjectTemplateViewConfig.id == config_id)
            .first()
        )

    def list_view_configs(
        self, view_id: uuid.UUID
    ) -> List[ProjectTemplateViewConfig]:
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
