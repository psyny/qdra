"""Service for resolving constraints to entity IDs with two-layer caching."""
import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, exists
from infrastructure.cache.constraint_cache import (
    get_constraint_resolution,
    set_constraint_resolution,
)

from models.entity import Entity
from models.entity_parameter import EntityParameter
from models.project_template import ProjectTemplateEntityType
from repositories.entity_repository import EntityRepository
from repositories.entity_parameter_repository import EntityParameterRepository
from infrastructure.config.settings import settings
from domain.constraints import ConstraintSpec

from services.constraint_matcher import ConstraintMatcher


class ConstraintResolutionService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = EntityRepository(db)
        self.entity_param_repo = EntityParameterRepository(db)
        from qdra.infrastructure.config.settings import settings
        self.settings = settings

    def find_materials_by_constraints(
        self,
        constraints: List[ConstraintSpec],
        project_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """Find materials in the project that match the given constraints using SQL filtering."""
        # Create cache key from constraints
        cache_key = self._make_cache_key("materials", project_id, constraints)

        # Check cache (L2 only)
        cached = get_constraint_resolution(cache_key)
        if cached is not None:
            return cached

        # Build SQL query with constraint filtering
        query = (
            self.db.query(Entity.id)
            .join(ProjectTemplateEntityType)
            .filter(Entity.project_id == project_id)
            .filter(ProjectTemplateEntityType.kind == "material")
        )

        # Add EXISTS clauses for each constraint
        for constraint in constraints:
            query = query.filter(self._build_constraint_exists_clause(constraint))

        # Execute query
        matching_materials = [row[0] for row in query.all()]

        # Cache result
        set_constraint_resolution(cache_key, matching_materials)

        return matching_materials

    def find_recipes_by_constraints(
        self,
        constraints: List[ConstraintSpec],
        project_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """Find recipes in the project that match the given constraints using SQL filtering."""
        # Create cache key from constraints
        cache_key = self._make_cache_key("recipes", project_id, constraints)

        # Check cache (L2 only)
        cached = get_constraint_resolution(cache_key)
        if cached is not None:
            return cached

        # Build SQL query with constraint filtering
        query = (
            self.db.query(Entity.id)
            .join(ProjectTemplateEntityType)
            .filter(Entity.project_id == project_id)
            .filter(ProjectTemplateEntityType.kind == "recipe")
        )

        # Add EXISTS clauses for each constraint
        for constraint in constraints:
            query = query.filter(self._build_constraint_exists_clause(constraint))

        # Execute query
        matching_recipes = [row[0] for row in query.all()]

        # Cache result
        set_constraint_resolution(cache_key, matching_recipes)

        return matching_recipes

    def _build_constraint_exists_clause(self, constraint: ConstraintSpec):
        """Build an EXISTS clause for a single constraint."""
        # Special handling for __system__ domain
        if constraint.domain == "__system__":
            if constraint.key == "id":
                if constraint.operator == "=" and constraint.value_string:
                    return Entity.id == uuid.UUID(constraint.value_string)
                else:
                    return False  # Invalid __system__ constraint
            elif constraint.key == "group":
                if constraint.operator == "=" and constraint.value_string is not None:
                    return Entity.group == constraint.value_string
                else:
                    return False  # Invalid __system__ constraint
            return False  # Unsupported __system__ key

        # Build EXISTS subquery for entity_parameters using select()
        from sqlalchemy import select

        subquery = select(EntityParameter.id).where(EntityParameter.entity_id == Entity.id)

        # Handle wildcard domain
        if constraint.domain != "*":
            subquery = subquery.where(EntityParameter.domain == constraint.domain)

        # Handle wildcard key
        if constraint.key != "*":
            subquery = subquery.where(EntityParameter.key == constraint.key)

        # Handle exists operator
        if constraint.operator == "exists":
            return exists(subquery)

        # Get constraint value
        constraint_value = self._get_constraint_value(constraint)
        if constraint_value is None:
            return False  # Invalid constraint

        # Add value comparison based on type
        if constraint.value_string is not None:
            subquery = self._add_value_comparison(
                subquery, EntityParameter.value_string, constraint.operator, constraint_value
            )
        elif constraint.value_number is not None:
            subquery = self._add_value_comparison(
                subquery, EntityParameter.value_number, constraint.operator, constraint_value
            )
        elif constraint.value_boolean is not None:
            subquery = self._add_value_comparison(
                subquery, EntityParameter.value_boolean, constraint.operator, constraint_value
            )

        return exists(subquery)

    def _add_value_comparison(self, query, column, operator: str, value):
        """Add value comparison to query based on operator."""
        if operator == "=":
            return query.where(column == value)
        elif operator == "<":
            return query.where(column < value)
        elif operator == "<=":
            return query.where(column <= value)
        elif operator == ">":
            return query.where(column > value)
        elif operator == ">=":
            return query.where(column >= value)
        elif operator == "in":
            if isinstance(value, list):
                return query.where(column.in_(value))
            else:
                return query.where(False)  # Invalid IN constraint
        return query.where(False)  # Unsupported operator

    def _material_matches_constraints(
        self, 
        material: Entity, 
        material_params: List[EntityParameter], 
        constraints: List[ConstraintSpec]
    ) -> bool:
        """Check if a material matches all constraints."""
        for constraint in constraints:
            # Special handling for __system__ domain
            if constraint.domain == "__system__":
                if constraint.key == "id":
                    if constraint.operator == "=" and constraint.value_string:
                        if str(material.id) != constraint.value_string:
                            return False
                    else:
                        return False
                    continue
                elif constraint.key == "group":
                    if constraint.operator == "=" and constraint.value_string is not None:
                        if material.group != constraint.value_string:
                            return False
                    else:
                        return False
                    continue
            
            # Find matching parameter
            matched = False
            for param in material_params:
                if self._param_matches_constraint(param, constraint):
                    matched = True
                    break
            
            if not matched:
                return False
        
        return True

    def _entity_matches_constraints(
        self, 
        entity: Entity, 
        entity_params: List[EntityParameter], 
        constraints: List[ConstraintSpec]
    ) -> bool:
        """Check if an entity (material or recipe) matches all constraints."""
        for constraint in constraints:
            # Special handling for __system__ domain
            if constraint.domain == "__system__":
                if constraint.key == "id":
                    if constraint.operator == "=" and constraint.value_string:
                        if str(entity.id) != constraint.value_string:
                            return False
                    else:
                        return False
                    continue
                elif constraint.key == "group":
                    if constraint.operator == "=" and constraint.value_string is not None:
                        if entity.group != constraint.value_string:
                            return False
                    else:
                        return False
                    continue
            
            # Find matching parameter
            matched = False
            for param in entity_params:
                if self._param_matches_constraint(param, constraint):
                    matched = True
                    break
            
            if not matched:
                return False
        
        return True

    def _param_matches_constraint(
        self, 
        param: EntityParameter, 
        constraint: ConstraintSpec
    ) -> bool:
        """Check if a parameter matches a constraint spec."""
        # Get parameter value
        param_value = self._get_parameter_value(param)
        if param_value is None:
            return False

        # Get constraint value
        constraint_value = self._get_constraint_value(constraint)

        # Handle wildcard domain/key
        if constraint.is_wildcard:
            if constraint.domain == "*" and constraint.key == "*":
                return param_value is not None
            elif constraint.domain == "*":
                if param.key != constraint.key:
                    return False
                return param_value is not None
            elif constraint.key == "*":
                if param.domain != constraint.domain:
                    return False
                return param_value is not None

        # Check domain and key match
        if not constraint.is_wildcard:
            if constraint.domain != "*" and param.domain != constraint.domain:
                return False
            if constraint.key != "*" and param.key != constraint.key:
                return False

        # Handle exists operator
        if constraint.operator == "exists":
            return param_value is not None

        # Handle comparison operators
        if constraint_value is None:
            return False

        # Type checking for comparisons
        if type(param_value) != type(constraint_value):
            return False

        # Apply operator
        if constraint.operator == "=":
            return param_value == constraint_value
        elif constraint.operator == "<":
            return param_value < constraint_value
        elif constraint.operator == "<=":
            return param_value <= constraint_value
        elif constraint.operator == ">":
            return param_value > constraint_value
        elif constraint.operator == ">=":
            return param_value >= constraint_value
        elif constraint.operator == "in":
            if not isinstance(constraint_value, list):
                return False
            return param_value in constraint_value

        return False

    def _get_parameter_value(self, param: EntityParameter) -> Any:
        """Extract the value from a parameter."""
        if param.value_string is not None:
            return param.value_string
        elif param.value_number is not None:
            return param.value_number
        elif param.value_boolean is not None:
            return param.value_boolean
        return None

    def _get_constraint_value(self, constraint: ConstraintSpec) -> Any:
        """Extract the value from a constraint spec."""
        if constraint.value_string is not None:
            return constraint.value_string
        elif constraint.value_number is not None:
            return constraint.value_number
        elif constraint.value_boolean is not None:
            return constraint.value_boolean
        return None

    def _make_cache_key(self, entity_type: str, project_id: uuid.UUID, constraints: List[ConstraintSpec]) -> str:
        """Create a deterministic cache key from constraints."""
        import hashlib
        import json
        
        # Sort constraints for deterministic key
        sorted_constraints = sorted(
            [
                {
                    "domain": c.domain,
                    "key": c.key,
                    "operator": c.operator,
                    "value_string": c.value_string,
                    "value_number": c.value_number,
                    "value_boolean": c.value_boolean,
                    "is_wildcard": c.is_wildcard,
                }
                for c in constraints
            ],
            key=lambda x: (x["domain"], x["key"], x["operator"])
        )
        
        constraint_str = json.dumps(sorted_constraints, sort_keys=True)
        hash_str = hashlib.md5(constraint_str.encode()).hexdigest()
        return f"constraint_resolution:{entity_type}:{project_id}:{hash_str}"

    def clear_cache(self):
        """Clear the cache (now L2 only)."""
        # This is now handled by the constraint_cache module
        pass

    def clear_pattern(self, project_id: uuid.UUID):
        """Clear all caches matching the project pattern."""
        from qdra.infrastructure.cache.invalidation_controller import constraint_resolution_changed
        constraint_resolution_changed(project_id)
