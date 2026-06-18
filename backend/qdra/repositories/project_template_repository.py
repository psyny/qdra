import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.project_template import (
    ProjectTemplate,
    ProjectTemplateEntityType,
    ProjectTemplateParameterDefinition,
    ProjectTemplateView,
    ProjectTemplateViewConfig,
    ProjectTemplateSlotGroup,
    ProjectTemplateSlotDefinition,
    ProjectTemplateSlotConstraint,
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

    def is_entity_type_used_by_entities(self, entity_type_id: uuid.UUID) -> bool:
        """Check if an entity type is used by any runtime entities."""
        from models.entity import Entity
        count = (
            self.db.query(Entity)
            .filter(Entity.entity_type_id == entity_type_id)
            .count()
        )
        return count > 0

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
        validation_min: Optional[float] = None,
        validation_max: Optional[float] = None,
        validation_regex: Optional[str] = None,
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
            validation_min=validation_min,
            validation_max=validation_max,
            validation_regex=validation_regex,
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

    def update_parameter_definition(
        self,
        definition_id: uuid.UUID,
        domain: Optional[str] = None,
        key: Optional[str] = None,
        value_type: Optional[str] = None,
        label: Optional[str] = None,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        sort_order: Optional[int] = None,
        is_label: Optional[bool] = None,
        is_unique: Optional[bool] = None,
        is_searchable: Optional[bool] = None,
        is_hidden: Optional[bool] = None,
        default_value: Optional[str] = None,
        validation_min: Optional[float] = None,
        validation_max: Optional[float] = None,
        validation_regex: Optional[str] = None,
    ) -> Optional[ProjectTemplateParameterDefinition]:
        param_def = self.get_parameter_definition_by_id(definition_id)
        if param_def:
            if domain is not None:
                param_def.domain = domain
            if key is not None:
                param_def.key = key
            if value_type is not None:
                param_def.value_type = value_type
            if label is not None:
                param_def.label = label
            if description is not None:
                param_def.description = description
            if required is not None:
                param_def.required = required
            if sort_order is not None:
                param_def.sort_order = sort_order
            if is_label is not None:
                param_def.is_label = is_label
            if is_unique is not None:
                param_def.is_unique = is_unique
            if is_searchable is not None:
                param_def.is_searchable = is_searchable
            if is_hidden is not None:
                param_def.is_hidden = is_hidden
            if default_value is not None:
                param_def.default_value = default_value
            if validation_min is not None:
                param_def.validation_min = validation_min
            if validation_max is not None:
                param_def.validation_max = validation_max
            if validation_regex is not None:
                param_def.validation_regex = validation_regex
            self.db.commit()
            self.db.refresh(param_def)
        return param_def

    # ProjectTemplateView CRUD

    def create_view(
        self,
        project_template_id: uuid.UUID,
        view_key: str,
        label: str,
        description: Optional[str] = None,
        is_system: bool = False,
        sort_order: int = 0,
    ) -> ProjectTemplateView:
        view = ProjectTemplateView(
            project_template_id=project_template_id,
            view_key=view_key,
            label=label,
            description=description,
            is_system=is_system,
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

    def update_view(
        self,
        view_id: uuid.UUID,
        view_key: Optional[str] = None,
        label: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProjectTemplateView]:
        view = self.get_view_by_id(view_id)
        if view:
            if view_key is not None:
                view.view_key = view_key
            if label is not None:
                view.label = label
            if description is not None:
                view.description = description
            if sort_order is not None:
                view.sort_order = sort_order
            self.db.commit()
            self.db.refresh(view)
        return view

    # ProjectTemplateViewConfig CRUD

    def create_view_config(
        self,
        view_id: uuid.UUID,
        entity_type_id: Optional[uuid.UUID] = None,
        display_slots: Optional[List[Dict[str, Any]]] = None,
        filter_params: Optional[List[Dict[str, Any]]] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateViewConfig:
        config = ProjectTemplateViewConfig(
            view_id=view_id,
            entity_type_id=entity_type_id,
            filter_params=filter_params,
            display_slots=display_slots,
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

    def update_view_config(
        self,
        config_id: uuid.UUID,
        entity_type_id: Optional[uuid.UUID] = None,
        filter_params: Optional[List[Dict[str, Any]]] = None,
        display_slots: Optional[List[Dict[str, Any]]] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProjectTemplateViewConfig]:
        config = self.get_view_config_by_id(config_id)
        if config:
            if entity_type_id is not None:
                config.entity_type_id = entity_type_id
            if filter_params is not None:
                config.filter_params = filter_params
            if display_slots is not None:
                config.display_slots = display_slots
            if sort_order is not None:
                config.sort_order = sort_order
            self.db.commit()
            self.db.refresh(config)
        return config

    def seed_system_views(self, project_template_id: uuid.UUID) -> List[ProjectTemplateView]:
        """Create seeded system views for a project template."""
        system_views_data = [
            {
                "view_key": "material_catalog",
                "label": "Material Catalog",
                "description": "Full catalog of all materials",
                "sort_order": 0,
            },
            {
                "view_key": "recipe_catalog",
                "label": "Recipe Catalog",
                "description": "Full catalog of all recipes",
                "sort_order": 1,
            },
            {
                "view_key": "plan_catalog",
                "label": "Plan Catalog",
                "description": "Full catalog of all plans",
                "sort_order": 2,
            },
            {
                "view_key": "plan_results",
                "label": "Plan Results",
                "description": "Results from plan execution",
                "sort_order": 3,
            },
            {
                "view_key": "material_compact_catalog",
                "label": "Material Compact Catalog",
                "description": "Compact view of materials",
                "sort_order": 4,
            },
            {
                "view_key": "recipe_compact_catalog",
                "label": "Recipe Compact Catalog",
                "description": "Compact view of recipes",
                "sort_order": 5,
            },
        ]
        
        created_views = []
        for view_data in system_views_data:
            view = self.create_view(
                project_template_id=project_template_id,
                view_key=view_data["view_key"],
                label=view_data["label"],
                description=view_data["description"],
                is_system=True,
                sort_order=view_data["sort_order"],
            )
            created_views.append(view)
        
        return created_views

    # ProjectTemplateSlotGroup CRUD

    def create_slot_group(
        self,
        entity_type_id: uuid.UUID,
        kind: str,
        min_slots: int = 0,
        max_slots: Optional[int] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateSlotGroup:
        slot_group = ProjectTemplateSlotGroup(
            entity_type_id=entity_type_id,
            kind=kind,
            min_slots=min_slots,
            max_slots=max_slots,
            sort_order=sort_order,
        )
        self.db.add(slot_group)
        self.db.commit()
        self.db.refresh(slot_group)
        return slot_group

    def get_slot_group_by_id(self, slot_group_id: uuid.UUID) -> Optional[ProjectTemplateSlotGroup]:
        return (
            self.db.query(ProjectTemplateSlotGroup)
            .filter(ProjectTemplateSlotGroup.id == slot_group_id)
            .first()
        )

    def list_slot_groups(self, entity_type_id: uuid.UUID) -> List[ProjectTemplateSlotGroup]:
        return (
            self.db.query(ProjectTemplateSlotGroup)
            .filter(ProjectTemplateSlotGroup.entity_type_id == entity_type_id)
            .order_by(ProjectTemplateSlotGroup.sort_order)
            .all()
        )

    def update_slot_group(
        self,
        slot_group_id: uuid.UUID,
        kind: Optional[str] = None,
        min_slots: Optional[int] = None,
        max_slots: Optional[int] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProjectTemplateSlotGroup]:
        slot_group = self.get_slot_group_by_id(slot_group_id)
        if slot_group:
            if kind is not None:
                slot_group.kind = kind
            if min_slots is not None:
                slot_group.min_slots = min_slots
            if max_slots is not None:
                slot_group.max_slots = max_slots
            if sort_order is not None:
                slot_group.sort_order = sort_order
            self.db.commit()
            self.db.refresh(slot_group)
        return slot_group

    def delete_slot_group(self, slot_group_id: uuid.UUID) -> bool:
        slot_group = self.get_slot_group_by_id(slot_group_id)
        if slot_group:
            self.db.delete(slot_group)
            self.db.commit()
            return True
        return False

    # ProjectTemplateSlotDefinition CRUD

    def create_slot_definition(
        self,
        slot_group_id: uuid.UUID,
        slot_key: str,
        min_occurrences: int = 0,
        max_occurrences: Optional[int] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateSlotDefinition:
        slot_def = ProjectTemplateSlotDefinition(
            slot_group_id=slot_group_id,
            slot_key=slot_key,
            min_occurrences=min_occurrences,
            max_occurrences=max_occurrences,
            sort_order=sort_order,
        )
        self.db.add(slot_def)
        self.db.commit()
        self.db.refresh(slot_def)
        return slot_def

    def get_slot_definition_by_id(self, slot_def_id: uuid.UUID) -> Optional[ProjectTemplateSlotDefinition]:
        return (
            self.db.query(ProjectTemplateSlotDefinition)
            .filter(ProjectTemplateSlotDefinition.id == slot_def_id)
            .first()
        )

    def list_slot_definitions(self, slot_group_id: uuid.UUID) -> List[ProjectTemplateSlotDefinition]:
        return (
            self.db.query(ProjectTemplateSlotDefinition)
            .filter(ProjectTemplateSlotDefinition.slot_group_id == slot_group_id)
            .order_by(ProjectTemplateSlotDefinition.sort_order)
            .all()
        )

    def update_slot_definition(
        self,
        slot_def_id: uuid.UUID,
        slot_key: Optional[str] = None,
        min_occurrences: Optional[int] = None,
        max_occurrences: Optional[int] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProjectTemplateSlotDefinition]:
        slot_def = self.get_slot_definition_by_id(slot_def_id)
        if slot_def:
            if slot_key is not None:
                slot_def.slot_key = slot_key
            if min_occurrences is not None:
                slot_def.min_occurrences = min_occurrences
            if max_occurrences is not None:
                slot_def.max_occurrences = max_occurrences
            if sort_order is not None:
                slot_def.sort_order = sort_order
            self.db.commit()
            self.db.refresh(slot_def)
        return slot_def

    def delete_slot_definition(self, slot_def_id: uuid.UUID) -> bool:
        slot_def = self.get_slot_definition_by_id(slot_def_id)
        if slot_def:
            self.db.delete(slot_def)
            self.db.commit()
            return True
        return False

    # ProjectTemplateSlotConstraint CRUD

    def create_slot_constraint(
        self,
        slot_group_id: Optional[uuid.UUID] = None,
        slot_definition_id: Optional[uuid.UUID] = None,
        domain: Optional[str] = None,
        key: Optional[str] = None,
        operator: Optional[str] = None,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
        is_wildcard: bool = False,
        sort_order: int = 0,
    ) -> ProjectTemplateSlotConstraint:
        constraint = ProjectTemplateSlotConstraint(
            slot_group_id=slot_group_id,
            slot_definition_id=slot_definition_id,
            domain=domain,
            key=key,
            operator=operator,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
            is_wildcard=is_wildcard,
            sort_order=sort_order,
        )
        self.db.add(constraint)
        self.db.commit()
        self.db.refresh(constraint)
        return constraint

    def get_slot_constraint_by_id(self, constraint_id: uuid.UUID) -> Optional[ProjectTemplateSlotConstraint]:
        return (
            self.db.query(ProjectTemplateSlotConstraint)
            .filter(ProjectTemplateSlotConstraint.id == constraint_id)
            .first()
        )

    def list_slot_constraints_for_group(self, slot_group_id: uuid.UUID) -> List[ProjectTemplateSlotConstraint]:
        return (
            self.db.query(ProjectTemplateSlotConstraint)
            .filter(ProjectTemplateSlotConstraint.slot_group_id == slot_group_id)
            .order_by(ProjectTemplateSlotConstraint.sort_order)
            .all()
        )

    def list_slot_constraints_for_definition(self, slot_def_id: uuid.UUID) -> List[ProjectTemplateSlotConstraint]:
        return (
            self.db.query(ProjectTemplateSlotConstraint)
            .filter(ProjectTemplateSlotConstraint.slot_definition_id == slot_def_id)
            .order_by(ProjectTemplateSlotConstraint.sort_order)
            .all()
        )

    def update_slot_constraint(
        self,
        constraint_id: uuid.UUID,
        domain: Optional[str] = None,
        key: Optional[str] = None,
        operator: Optional[str] = None,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
        is_wildcard: Optional[bool] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProjectTemplateSlotConstraint]:
        constraint = self.get_slot_constraint_by_id(constraint_id)
        if constraint:
            if domain is not None:
                constraint.domain = domain
            if key is not None:
                constraint.key = key
            if operator is not None:
                constraint.operator = operator
            if value_string is not None:
                constraint.value_string = value_string
            if value_number is not None:
                constraint.value_number = value_number
            if value_boolean is not None:
                constraint.value_boolean = value_boolean
            if is_wildcard is not None:
                constraint.is_wildcard = is_wildcard
            if sort_order is not None:
                constraint.sort_order = sort_order
            self.db.commit()
            self.db.refresh(constraint)
        return constraint

    def delete_slot_constraint(self, constraint_id: uuid.UUID) -> bool:
        constraint = self.get_slot_constraint_by_id(constraint_id)
        if constraint:
            self.db.delete(constraint)
            self.db.commit()
            return True
        return False
