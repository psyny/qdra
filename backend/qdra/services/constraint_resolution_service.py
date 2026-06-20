"""Service for resolving constraints to entity IDs with two-layer caching."""
import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from cachetools import TTLCache

from models.entity import Entity
from models.entity_parameter import EntityParameter
from repositories.entity_repository import EntityRepository
from repositories.entity_parameter_repository import EntityParameterRepository
from qdra.infrastructure.cache.cache_service import CacheService
from qdra.infrastructure.config.settings import settings
from qdra.infrastructure.cache.relationship_cache import get_cache_service
from domain.planning.output_solver_domain import ConstraintSpec

from services.constraint_matcher import ConstraintMatcher


class ConstraintResolutionService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = EntityRepository(db, CacheService())
        self.entity_param_repo = EntityParameterRepository(db)
        from qdra.infrastructure.config.settings import settings
        self.settings = settings
        self.cache_service = get_cache_service()
        self.l1_cache = TTLCache(maxsize=1000, ttl=settings.cache_relationship_ttl)

    def find_materials_by_constraints(
        self, 
        constraints: List[ConstraintSpec], 
        project_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """Find materials in the project that match the given constraints."""
        # Create cache key from constraints
        cache_key = self._make_cache_key("materials", project_id, constraints)
        
        # L1: Check local cache if enabled
        if self.settings.l1_caching and cache_key in self.l1_cache:
            return self.l1_cache[cache_key]
        
        # L2: Check Redis cache if enabled
        if self.settings.l2_caching:
            cached = self.cache_service.get(cache_key)
            if cached:
                result = [uuid.UUID(id_str) for id_str in cached]
                if self.settings.l1_caching:
                    self.l1_cache[cache_key] = result
                return result
        
        # Compute result
        materials = self.entity_repo.list_by_project(project_id, kind="material")
        matching_materials = []
        
        for material in materials:
            material_params = self.entity_param_repo.list_by_entity(material.id)
            if self._material_matches_constraints(material, material_params, constraints):
                matching_materials.append(material.id)
        
        # Cache result if enabled
        if self.settings.l1_caching:
            self.l1_cache[cache_key] = matching_materials
        if self.settings.l2_caching:
            serialized = [str(id) for id in matching_materials]
            self.cache_service.set(cache_key, serialized, self.settings.cache_relationship_ttl)
        
        return matching_materials

    def find_recipes_by_constraints(
        self, 
        constraints: List[ConstraintSpec], 
        project_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """Find recipes in the project that match the given constraints."""
        # Create cache key from constraints
        cache_key = self._make_cache_key("recipes", project_id, constraints)
        
        # L1: Check local cache if enabled
        if self.settings.l1_caching and cache_key in self.l1_cache:
            return self.l1_cache[cache_key]
        
        # L2: Check Redis cache if enabled
        if self.settings.l2_caching:
            cached = self.cache_service.get(cache_key)
            if cached:
                result = [uuid.UUID(id_str) for id_str in cached]
                if self.settings.l1_caching:
                    self.l1_cache[cache_key] = result
                return result
        
        # Compute result
        recipes = self.entity_repo.list_by_project(project_id, kind="recipe")
        matching_recipes = []
        
        for recipe in recipes:
            recipe_params = self.entity_param_repo.list_by_entity(recipe.id)
            if self._entity_matches_constraints(recipe, recipe_params, constraints):
                matching_recipes.append(recipe.id)
        
        # Cache result if enabled
        if self.settings.l1_caching:
            self.l1_cache[cache_key] = matching_recipes
        if self.settings.l2_caching:
            serialized = [str(id) for id in matching_recipes]
            self.cache_service.set(cache_key, serialized, self.settings.cache_relationship_ttl)
        
        return matching_recipes

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
        """Clear the L1 cache."""
        self.l1_cache.clear()

    def clear_pattern(self, project_id: str):
        """Clear all L2 caches matching the project pattern."""
        if self.settings.l2_caching:
            self.cache_service.delete_pattern(f"constraint_resolution:*:{project_id}:*")
