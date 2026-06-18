import uuid
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from models.entity_parameter import EntityParameter
from models.entity import Entity
from models.project_template import ProjectTemplateParameterDefinition


class EntityParameterRepository:
    def __init__(self, db: Session):
        self.db = db

    def _validate_parameter_value(
        self,
        param_def: ProjectTemplateParameterDefinition,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> None:
        """
        Validate a parameter value against its parameter definition.
        Raises ValueError if validation fails.
        """
        # Check required constraint
        if param_def.required:
            has_value = (
                (param_def.value_type == "string" and value_string is not None and value_string != "")
                or (param_def.value_type == "number" and value_number is not None)
                or (param_def.value_type == "boolean" and value_boolean is not None)
            )
            if not has_value:
                raise ValueError(f"Parameter '{param_def.key}' is required but no value was provided")

        # Validate based on value_type
        if param_def.value_type == "string":
            if value_string is not None:
                # Validate min length
                if param_def.validation_min is not None and len(value_string) < param_def.validation_min:
                    raise ValueError(
                        f"Parameter '{param_def.key}' must be at least {param_def.validation_min} characters long"
                    )
                # Validate max length
                if param_def.validation_max is not None and len(value_string) > param_def.validation_max:
                    raise ValueError(
                        f"Parameter '{param_def.key}' must be at most {param_def.validation_max} characters long"
                    )
                # Validate regex
                if param_def.validation_regex is not None:
                    try:
                        if not re.match(param_def.validation_regex, value_string):
                            raise ValueError(
                                f"Parameter '{param_def.key}' does not match the required pattern"
                            )
                    except re.error:
                        pass  # Regex validation should have been caught at definition time

        elif param_def.value_type == "number":
            if value_number is not None:
                # Validate min value
                if param_def.validation_min is not None and value_number < param_def.validation_min:
                    raise ValueError(
                        f"Parameter '{param_def.key}' must be at least {param_def.validation_min}"
                    )
                # Validate max value
                if param_def.validation_max is not None and value_number > param_def.validation_max:
                    raise ValueError(
                        f"Parameter '{param_def.key}' must be at most {param_def.validation_max}"
                    )

        # Boolean parameters have no min/max/regex validation

    def create(
        self,
        entity_id: uuid.UUID,
        domain: str,
        key: str,
        value_string: Optional[str] = None,
        value_number: Optional[float] = None,
        value_boolean: Optional[bool] = None,
    ) -> EntityParameter:
        # Get the entity to find its entity_type_id
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        # Get the parameter definition
        param_def = (
            self.db.query(ProjectTemplateParameterDefinition)
            .filter(
                ProjectTemplateParameterDefinition.entity_type_id == entity.entity_type_id,
                ProjectTemplateParameterDefinition.domain == domain,
                ProjectTemplateParameterDefinition.key == key,
            )
            .first()
        )

        if param_def:
            # Validate the value against the parameter definition
            self._validate_parameter_value(
                param_def, value_string, value_number, value_boolean
            )

        parameter = EntityParameter(
            entity_id=entity_id,
            domain=domain,
            key=key,
            value_string=value_string,
            value_number=value_number,
            value_boolean=value_boolean,
        )
        self.db.add(parameter)
        self.db.commit()
        self.db.refresh(parameter)
        return parameter

    def get_by_id(self, parameter_id: uuid.UUID) -> Optional[EntityParameter]:
        return (
            self.db.query(EntityParameter)
            .filter(EntityParameter.id == parameter_id)
            .first()
        )

    def list_by_entity(self, entity_id: uuid.UUID) -> List[EntityParameter]:
        return (
            self.db.query(EntityParameter)
            .filter(EntityParameter.entity_id == entity_id)
            .all()
        )

    def delete(self, parameter_id: uuid.UUID) -> bool:
        parameter = self.get_by_id(parameter_id)
        if not parameter:
            return False
        self.db.delete(parameter)
        self.db.commit()
        return True
