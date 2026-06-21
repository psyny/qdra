import uuid
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, selectinload

from models.project_template import (
    ProjectTemplate,
    ProjectTemplateEntityType,
    ProjectTemplateParameterDefinition,
    ProjectTemplateView,
    ProjectTemplateViewConfig,
    ProjectTemplateSlotGroup,
    ProjectTemplateDefaultSlot,
    ProjectTemplateDefaultOption,
    ProjectTemplateDefaultParameterConstraint,
    ProjectTemplatePerSlot,
    ProjectTemplatePerOption,
    ProjectTemplatePerParameterConstraint,
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
            
            # Delete related records in order of dependencies
            # Delete view configs
            self.db.query(ProjectTemplateViewConfig).filter(
                ProjectTemplateViewConfig.view_id.in_(
                    self.db.query(ProjectTemplateView.id).filter(
                        ProjectTemplateView.project_template_id == template_id
                    )
                )
            ).delete(synchronize_session=False)
            
            # Delete views
            self.db.query(ProjectTemplateView).filter(
                ProjectTemplateView.project_template_id == template_id
            ).delete(synchronize_session=False)

            # Delete slot groups
            self.db.query(ProjectTemplateSlotGroup).filter(
                ProjectTemplateSlotGroup.entity_type_id.in_(
                    self.db.query(ProjectTemplateEntityType.id).filter(
                        ProjectTemplateEntityType.project_template_id == template_id
                    )
                )
            ).delete(synchronize_session=False)
            
            # Delete parameter definitions
            self.db.query(ProjectTemplateParameterDefinition).filter(
                ProjectTemplateParameterDefinition.entity_type_id.in_(
                    self.db.query(ProjectTemplateEntityType.id).filter(
                        ProjectTemplateEntityType.project_template_id == template_id
                    )
                )
            ).delete(synchronize_session=False)
            
            # Delete entity types
            self.db.query(ProjectTemplateEntityType).filter(
                ProjectTemplateEntityType.project_template_id == template_id
            ).delete(synchronize_session=False)
            
            # Delete the template
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
            .options(selectinload(ProjectTemplateEntityType.parameter_definitions))
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
            .options(selectinload(ProjectTemplateView.configs))
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
        """Create seeded system views for a project template if they don't already exist."""
        from sqlalchemy.exc import IntegrityError
        
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
                "view_key": "material_compact_catalog",
                "label": "Material Compact Catalog",
                "description": "Compact view of materials",
                "sort_order": 2,
            },
            {
                "view_key": "recipe_compact_catalog",
                "label": "Recipe Compact Catalog",
                "description": "Compact view of recipes",
                "sort_order": 3,
            },
            {
                "view_key": "planning_output_solver",
                "label": "Output Solver",
                "description": "Output solver planning configuration",
                "sort_order": 4,
            },
        ]
        
        # Get existing views to avoid duplicates
        existing_views = self.list_views(project_template_id)
        existing_view_keys = {view.view_key for view in existing_views}
        
        created_views = []
        for view_data in system_views_data:
            if view_data["view_key"] not in existing_view_keys:
                try:
                    view = self.create_view(
                        project_template_id=project_template_id,
                        view_key=view_data["view_key"],
                        label=view_data["label"],
                        description=view_data["description"],
                        is_system=True,
                        sort_order=view_data["sort_order"],
                    )
                    created_views.append(view)
                except IntegrityError:
                    # View already exists (race condition or pre-check missed it), skip it
                    self.db.rollback()
                    continue
        
        return created_views

    # ProjectTemplateSlotGroup CRUD

    def create_slot_group(
        self,
        entity_type_id: uuid.UUID,
        type: str,
        min_slots: int = 0,
        max_slots: Optional[int] = None,
        sort_order: int = 0,
    ) -> ProjectTemplateSlotGroup:
        slot_group = ProjectTemplateSlotGroup(
            entity_type_id=entity_type_id,
            type=type,
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
        type: Optional[str] = None,
        min_slots: Optional[int] = None,
        max_slots: Optional[int] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ProjectTemplateSlotGroup]:
        slot_group = self.get_slot_group_by_id(slot_group_id)
        if slot_group:
            if type is not None:
                slot_group.type = type
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

    # ProjectTemplateDefaultSlot CRUD

    def get_default_slot(self, slot_group_id: uuid.UUID) -> Optional[ProjectTemplateDefaultSlot]:
        return (
            self.db.query(ProjectTemplateDefaultSlot)
            .options(
                selectinload(ProjectTemplateDefaultSlot.options).selectinload(
                    ProjectTemplateDefaultOption.parameter_constraints
                )
            )
            .filter(ProjectTemplateDefaultSlot.slot_group_id == slot_group_id)
            .first()
        )

    def create_default_slot(
        self,
        slot_group_id: uuid.UUID,
        kind: str,
        sort_order: int = 0,
        options_data: Optional[List[Dict[str, Any]]] = None,
    ) -> ProjectTemplateDefaultSlot:
        default_slot = ProjectTemplateDefaultSlot(
            slot_group_id=slot_group_id,
            kind=kind,
            sort_order=sort_order,
        )
        self.db.add(default_slot)
        self.db.commit()
        self.db.refresh(default_slot)

        # Create options if provided
        if options_data:
            for option_data in options_data:
                option = ProjectTemplateDefaultOption(
                    default_slot_id=default_slot.id,
                    quantity=option_data.get("quantity"),
                    sort_order=option_data.get("sort_order", 0),
                )
                self.db.add(option)
                self.db.commit()
                self.db.refresh(option)

                # Create parameter constraints if provided
                constraints_data = option_data.get("parameter_constraints", [])
                for constraint_data in constraints_data:
                    constraint = ProjectTemplateDefaultParameterConstraint(
                        default_option_id=option.id,
                        domain=constraint_data["domain"],
                        key=constraint_data["key"],
                        operator=constraint_data["operator"],
                        value_string=constraint_data.get("value_string"),
                        value_number=constraint_data.get("value_number"),
                        value_boolean=constraint_data.get("value_boolean"),
                        is_wildcard=constraint_data.get("is_wildcard", False),
                    )
                    self.db.add(constraint)
                self.db.commit()
            self.db.refresh(default_slot)

        return default_slot

    def update_default_slot(
        self,
        slot_group_id: uuid.UUID,
        kind: Optional[str] = None,
        sort_order: Optional[int] = None,
        options_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[ProjectTemplateDefaultSlot]:
        default_slot = self.get_default_slot(slot_group_id)
        if not default_slot:
            return None

        if kind is not None:
            default_slot.kind = kind
        if sort_order is not None:
            default_slot.sort_order = sort_order

        # Update options if provided
        if options_data is not None:
            # Delete existing options and constraints
            self.db.query(ProjectTemplateDefaultParameterConstraint).filter(
                ProjectTemplateDefaultParameterConstraint.default_option_id.in_(
                    self.db.query(ProjectTemplateDefaultOption.id).filter(
                        ProjectTemplateDefaultOption.default_slot_id == default_slot.id
                    )
                )
            ).delete(synchronize_session=False)

            self.db.query(ProjectTemplateDefaultOption).filter(
                ProjectTemplateDefaultOption.default_slot_id == default_slot.id
            ).delete(synchronize_session=False)

            # Create new options
            for option_data in options_data:
                option = ProjectTemplateDefaultOption(
                    default_slot_id=default_slot.id,
                    quantity=option_data.get("quantity"),
                    sort_order=option_data.get("sort_order", 0),
                )
                self.db.add(option)
                self.db.commit()
                self.db.refresh(option)

                # Create parameter constraints
                constraints_data = option_data.get("parameter_constraints", [])
                for constraint_data in constraints_data:
                    constraint = ProjectTemplateDefaultParameterConstraint(
                        default_option_id=option.id,
                        domain=constraint_data["domain"],
                        key=constraint_data["key"],
                        operator=constraint_data["operator"],
                        value_string=constraint_data.get("value_string"),
                        value_number=constraint_data.get("value_number"),
                        value_boolean=constraint_data.get("value_boolean"),
                        is_wildcard=constraint_data.get("is_wildcard", False),
                    )
                    self.db.add(constraint)
                self.db.commit()

        self.db.commit()
        self.db.refresh(default_slot)
        return default_slot

    def delete_default_slot(self, slot_group_id: uuid.UUID) -> bool:
        default_slot = self.get_default_slot(slot_group_id)
        if default_slot:
            self.db.delete(default_slot)
            self.db.commit()
            return True
        return False

    # ProjectTemplatePerSlot CRUD

    def get_per_slot_by_id(self, per_slot_id: uuid.UUID) -> Optional[ProjectTemplatePerSlot]:
        return (
            self.db.query(ProjectTemplatePerSlot)
            .options(
                selectinload(ProjectTemplatePerSlot.options).selectinload(
                    ProjectTemplatePerOption.parameter_constraints
                )
            )
            .filter(ProjectTemplatePerSlot.id == per_slot_id)
            .first()
        )

    def list_per_slots(self, slot_group_id: uuid.UUID) -> List[ProjectTemplatePerSlot]:
        return (
            self.db.query(ProjectTemplatePerSlot)
            .options(
                selectinload(ProjectTemplatePerSlot.options).selectinload(
                    ProjectTemplatePerOption.parameter_constraints
                )
            )
            .filter(ProjectTemplatePerSlot.slot_group_id == slot_group_id)
            .order_by(ProjectTemplatePerSlot.sort_order)
            .all()
        )

    def create_per_slot(
        self,
        slot_group_id: uuid.UUID,
        kind: str,
        sort_order: int = 0,
        options_data: Optional[List[Dict[str, Any]]] = None,
    ) -> ProjectTemplatePerSlot:
        per_slot = ProjectTemplatePerSlot(
            slot_group_id=slot_group_id,
            kind=kind,
            sort_order=sort_order,
        )
        self.db.add(per_slot)
        self.db.commit()
        self.db.refresh(per_slot)

        # Create options if provided
        if options_data:
            for option_data in options_data:
                option = ProjectTemplatePerOption(
                    per_slot_id=per_slot.id,
                    quantity=option_data.get("quantity"),
                    sort_order=option_data.get("sort_order", 0),
                )
                self.db.add(option)
                self.db.commit()
                self.db.refresh(option)

                # Create parameter constraints if provided
                constraints_data = option_data.get("parameter_constraints", [])
                for constraint_data in constraints_data:
                    constraint = ProjectTemplatePerParameterConstraint(
                        per_option_id=option.id,
                        domain=constraint_data["domain"],
                        key=constraint_data["key"],
                        operator=constraint_data["operator"],
                        value_string=constraint_data.get("value_string"),
                        value_number=constraint_data.get("value_number"),
                        value_boolean=constraint_data.get("value_boolean"),
                        is_wildcard=constraint_data.get("is_wildcard", False),
                    )
                    self.db.add(constraint)
                self.db.commit()
            self.db.refresh(per_slot)

        return per_slot

    def update_per_slot(
        self,
        per_slot_id: uuid.UUID,
        kind: Optional[str] = None,
        sort_order: Optional[int] = None,
        options_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[ProjectTemplatePerSlot]:
        per_slot = self.get_per_slot_by_id(per_slot_id)
        if not per_slot:
            return None

        if kind is not None:
            per_slot.kind = kind
        if sort_order is not None:
            per_slot.sort_order = sort_order

        # Update options if provided
        if options_data is not None:
            # Delete existing options and constraints
            self.db.query(ProjectTemplatePerParameterConstraint).filter(
                ProjectTemplatePerParameterConstraint.per_option_id.in_(
                    self.db.query(ProjectTemplatePerOption.id).filter(
                        ProjectTemplatePerOption.per_slot_id == per_slot.id
                    )
                )
            ).delete(synchronize_session=False)

            self.db.query(ProjectTemplatePerOption).filter(
                ProjectTemplatePerOption.per_slot_id == per_slot.id
            ).delete(synchronize_session=False)

            # Create new options
            for option_data in options_data:
                option = ProjectTemplatePerOption(
                    per_slot_id=per_slot.id,
                    quantity=option_data.get("quantity"),
                    sort_order=option_data.get("sort_order", 0),
                )
                self.db.add(option)
                self.db.commit()
                self.db.refresh(option)

                # Create parameter constraints
                constraints_data = option_data.get("parameter_constraints", [])
                for constraint_data in constraints_data:
                    constraint = ProjectTemplatePerParameterConstraint(
                        per_option_id=option.id,
                        domain=constraint_data["domain"],
                        key=constraint_data["key"],
                        operator=constraint_data["operator"],
                        value_string=constraint_data.get("value_string"),
                        value_number=constraint_data.get("value_number"),
                        value_boolean=constraint_data.get("value_boolean"),
                        is_wildcard=constraint_data.get("is_wildcard", False),
                    )
                    self.db.add(constraint)
                self.db.commit()

        self.db.commit()
        self.db.refresh(per_slot)
        return per_slot

    def delete_per_slot(self, per_slot_id: uuid.UUID) -> bool:
        per_slot = self.get_per_slot_by_id(per_slot_id)
        if per_slot:
            self.db.delete(per_slot)
            self.db.commit()
            return True
        return False

    # Template Export/Import

    def export_template(self, project_template_id: uuid.UUID) -> Dict[str, Any]:
        """Export a project template and all its related data to a JSON-serializable dictionary."""
        template = self.get_by_id(project_template_id)
        if not template:
            raise ValueError(f"Template {project_template_id} not found")

        # Export entity types with their parameter definitions
        entity_types = []
        for et in self.list_entity_types(project_template_id):
            param_defs = self.list_parameter_definitions_by_entity_type(et.id)
            slot_groups = self.list_slot_groups(et.id)

            slot_groups_data = []
            for sg in slot_groups:
                slot_groups_data.append({
                    "type": sg.type,
                    "min_slots": sg.min_slots,
                    "max_slots": sg.max_slots,
                    "sort_order": sg.sort_order,
                })

            param_defs_data = [
                {
                    "domain": pd.domain,
                    "key": pd.key,
                    "value_type": pd.value_type,
                    "label": pd.label,
                    "description": pd.description,
                    "required": pd.required,
                    "sort_order": pd.sort_order,
                    "is_label": pd.is_label,
                    "is_unique": pd.is_unique,
                    "is_searchable": pd.is_searchable,
                    "is_hidden": pd.is_hidden,
                    "default_value": pd.default_value,
                    "validation_min": pd.validation_min,
                    "validation_max": pd.validation_max,
                    "validation_regex": pd.validation_regex,
                }
                for pd in param_defs
            ]

            entity_types.append({
                "kind": et.kind,
                "name": et.name,
                "description": et.description,
                "sort_order": et.sort_order,
                "parameter_definitions": param_defs_data,
                "slot_groups": slot_groups_data,
            })

        # Export views with their configs
        views = []
        for view in self.list_views(project_template_id):
            configs = self.list_view_configs(view.id)
            configs_data = [
                {
                    "entity_type_name": self._get_entity_type_name_by_id(config.entity_type_id) if config.entity_type_id else None,
                    "filter_params": config.filter_params,
                    "display_slots": config.display_slots,
                    "sort_order": config.sort_order,
                }
                for config in configs
            ]
            views.append({
                "view_key": view.view_key,
                "label": view.label,
                "description": view.description,
                "is_system": view.is_system,
                "sort_order": view.sort_order,
                "configs": configs_data,
            })

        return {
            "template": {
                "name": template.name,
                "description": template.description,
                "version": template.version,
            },
            "entity_types": entity_types,
            "views": views,
        }

    def _get_entity_type_name_by_id(self, entity_type_id: Optional[uuid.UUID]) -> Optional[str]:
        """Helper to get entity type name by ID for export."""
        if not entity_type_id:
            return None
        et = self.get_entity_type_by_id(entity_type_id)
        return et.name if et else None

    def import_template(self, data: Dict[str, Any], name: Optional[str] = None) -> ProjectTemplate:
        """Import a project template from a JSON-serializable dictionary."""
        template_data = data["template"]
        entity_types_data = data["entity_types"]
        views_data = data["views"]

        # Use provided name or fall back to the name in the JSON
        template_name = name if name and name.strip() else template_data["name"]

        # Create the template
        template = self.create(
            name=template_name,
            description=template_data.get("description"),
            is_builtin=False,
        )

        # Track entity type name -> ID mapping for references
        entity_type_id_map: Dict[str, uuid.UUID] = {}

        # Import entity types with their parameter definitions and slot groups
        for et_data in entity_types_data:
            et = self.create_entity_type(
                project_template_id=template.id,
                kind=et_data["kind"],
                name=et_data["name"],
                description=et_data.get("description"),
                sort_order=et_data["sort_order"],
            )
            entity_type_id_map[et_data["name"]] = et.id

            # Import parameter definitions
            for pd_data in et_data["parameter_definitions"]:
                self.create_parameter_definition(
                    project_template_id=template.id,
                    entity_type_id=et.id,
                    domain=pd_data["domain"],
                    key=pd_data["key"],
                    value_type=pd_data["value_type"],
                    label=pd_data["label"],
                    description=pd_data.get("description"),
                    required=pd_data["required"],
                    sort_order=pd_data["sort_order"],
                    is_label=pd_data["is_label"],
                    is_unique=pd_data["is_unique"],
                    is_searchable=pd_data["is_searchable"],
                    is_hidden=pd_data["is_hidden"],
                    default_value=pd_data.get("default_value"),
                    validation_min=pd_data.get("validation_min"),
                    validation_max=pd_data.get("validation_max"),
                    validation_regex=pd_data.get("validation_regex"),
                )

            # Import slot groups
            for sg_data in et_data.get("slot_groups", []):
                sg = self.create_slot_group(
                    entity_type_id=et.id,
                    type=sg_data["type"],
                    min_slots=sg_data["min_slots"],
                    max_slots=sg_data.get("max_slots"),
                    sort_order=sg_data["sort_order"],
                )

        # Import views with their configs
        for view_data in views_data:
            view = self.create_view(
                project_template_id=template.id,
                view_key=view_data["view_key"],
                label=view_data["label"],
                description=view_data.get("description"),
                is_system=view_data["is_system"],
                sort_order=view_data["sort_order"],
            )

            for config_data in view_data.get("configs", []):
                entity_type_id = None
                if config_data.get("entity_type_name"):
                    entity_type_id = entity_type_id_map.get(config_data["entity_type_name"])

                self.create_view_config(
                    view_id=view.id,
                    entity_type_id=entity_type_id,
                    filter_params=config_data.get("filter_params"),
                    display_slots=config_data.get("display_slots"),
                    sort_order=config_data["sort_order"],
                )

        return template
