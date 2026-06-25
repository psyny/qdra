import uuid
from typing import List, Set, Optional
from sqlalchemy.orm import Session

from models.entity import Entity
from models.slot import Slot, SlotKind
from models.option import Option
from models.entity_parameter import EntityParameter
from models.parameter_constraint import ParameterConstraint

from repositories.entity_repository import EntityRepository
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.entity_parameter_repository import EntityParameterRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository
from infrastructure.cache.cache_service import CacheService
from infrastructure.cache.relationship_cache import (
    get_material_recipes_cache,
    get_recipe_materials_cache,
    get_cache_service,
)

from services.entity_service import EntityService
from services.constraint_resolution_service import ConstraintResolutionService

from domain.evaluation import RecipeMatchResult, SlotMatchResult, Allocation
from domain.constraints import ConstraintSpec


class RecipeEvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = EntityRepository(db)
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.entity_parameter_repo = EntityParameterRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)
        self.entity_service = EntityService(db)
        self.constraint_resolution_service = ConstraintResolutionService(db)
        from qdra.infrastructure.config.settings import settings
        self.settings = settings

    def evaluate_recipe(
        self, recipe_id: uuid.UUID, material_ids: List[uuid.UUID]
    ) -> RecipeMatchResult:
        """
        Evaluate if a recipe entity can execute given a set of material entity IDs.

        Returns a RecipeMatchResult with success status and allocations.
        """
        recipe = self.entity_service.get_basic_entity(recipe_id)
        if not recipe:
            return RecipeMatchResult(
                success=False,
                recipe_id=recipe_id,
                slot_results=[],
                allocations=[]
            )

        # Load material entities with their parameters
        materials = []
        material_params_map = {}
        for material_id in material_ids:
            material = self.entity_service.get_basic_entity(material_id)
            if material:
                materials.append(material)
                material_params_map[material_id] = (
                    self.entity_parameter_repo.list_by_entity(material_id)
                )

        # Load recipe structure
        slots = self.slot_repo.list_by_recipe_entity(recipe_id)
        
        # Track allocated materials
        allocated_materials: Set[uuid.UUID] = set()
        all_allocations: List[Allocation] = []
        slot_results: List[SlotMatchResult] = []

        # Evaluate each slot
        for slot in slots:
            # PRODUCES slots don't require material matching - they create materials
            if slot.kind == SlotKind.PRODUCES:
                slot_results.append(SlotMatchResult(
                    success=True,
                    slot_id=slot.id,
                    matched_option_id=None,
                    allocated_materials=[]
                ))
                continue
            
            slot_result = self._evaluate_slot(
                slot=slot,
                materials=materials,
                material_params_map=material_params_map,
                allocated_materials=allocated_materials
            )
            slot_results.append(slot_result)

            if slot_result.success:
                # Record allocations
                for material_id in slot_result.allocated_materials:
                    allocated_materials.add(material_id)
                    all_allocations.append(
                        Allocation(
                            material_id=material_id,
                            slot_id=slot.id,
                            option_id=slot_result.matched_option_id
                        )
                    )
            else:
                # Slot failed - recipe fails
                return RecipeMatchResult(
                    success=False,
                    recipe_id=recipe_id,
                    slot_results=slot_results,
                    allocations=all_allocations
                )

        # All slots succeeded
        return RecipeMatchResult(
            success=True,
            recipe_id=recipe_id,
            slot_results=slot_results,
            allocations=all_allocations
        )

    def _evaluate_slot(
        self,
        slot: Slot,
        materials: List[Entity],
        material_params_map: dict,
        allocated_materials: Set[uuid.UUID]
    ) -> SlotMatchResult:
        """
        Evaluate a slot by trying options in order.
        Returns the first option that succeeds.
        """
        options = self.option_repo.list_by_slot(slot.id)
        
        for option in options:
            # Try to satisfy this option
            matching_materials = self._find_matching_materials(
                option=option,
                materials=materials,
                material_params_map=material_params_map,
                allocated_materials=allocated_materials
            )

            # Check if we have enough materials
            required_quantity = int(option.quantity)
            if len(matching_materials) >= required_quantity:
                # Allocate materials
                allocated = matching_materials[:required_quantity]
                return SlotMatchResult(
                    success=True,
                    slot_id=slot.id,
                    matched_option_id=option.id,
                    allocated_materials=allocated
                )

        # No option succeeded
        return SlotMatchResult(
            success=False,
            slot_id=slot.id,
            matched_option_id=None,
            allocated_materials=[]
        )

    def _find_matching_materials(
        self,
        option: Option,
        materials: List[Entity],
        material_params_map: dict,
        allocated_materials: Set[uuid.UUID]
    ) -> List[uuid.UUID]:
        """
        Find all materials that match the option's constraints
        and are not already allocated.
        """
        constraints = self.constraint_repo.list_by_option_as_specs(option.id)
        matching_materials: List[uuid.UUID] = []

        for material in materials:
            # Skip if already allocated
            if material.id in allocated_materials:
                continue

            # Check if material matches all constraints
            material_params = material_params_map.get(material.id, [])
            if self.constraint_resolution_service._material_matches_constraints(
                material=material,
                material_params=material_params,
                constraints=constraints
            ):
                matching_materials.append(material.id)

        return matching_materials

    def find_materials_for_recipe_slots(self, recipe_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """
        Find all materials in the project that match each slot's constraints.
        
        Returns a dict with slot types (consumes, produces, requires) as keys,
        each containing a list of slots with their matching material IDs.
        """
        cache_key = f"recipe_materials:{project_id}:{recipe_id}"
        l1_cache = get_recipe_materials_cache()
        cache_service = get_cache_service()
        
        # L1: Check local cache if enabled
        if self.settings.l1_caching and cache_key in l1_cache:
            return l1_cache[cache_key]
        
        # L2: Check Redis cache if enabled
        if self.settings.l2_caching:
            cached = cache_service.get(cache_key)
            if cached:
                if self.settings.l1_caching:
                    l1_cache[cache_key] = cached
                return cached
        
        # Compute result
        recipe = self.entity_service.get_basic_entity(recipe_id)
        if not recipe:
            return {"consumes": [], "produces": [], "requires": []}

        # Load all materials in the project
        materials = self.entity_repo.list_by_project(project_id, kind="material")
        material_params_map = {}
        for material in materials:
            # Use cached parameters if available via entity_service
            material_params_map[material.id] = (
                self.entity_service.get_entity_parameters(material.id)
            )

        # Load recipe structure
        slots = self.slot_repo.list_by_recipe_entity(recipe_id)
        
        result = {
            "consumes": [],
            "produces": [],
            "requires": []
        }

        # Group slots by kind and find matching materials
        for slot in slots:
            options = self.option_repo.list_by_slot(slot.id)
            slot_data = {
                "slot_id": str(slot.id),
                "kind": slot.kind if isinstance(slot.kind, str) else slot.kind.value,
                "options": []
            }

            for option in options:
                constraints = self.constraint_repo.list_by_option_as_specs(option.id)
                matching_materials = []

                for material in materials:
                    material_params = material_params_map.get(material.id, [])
                    if self.constraint_resolution_service._material_matches_constraints(
                        material=material,
                        material_params=material_params,
                        constraints=constraints
                    ):
                        matching_materials.append(str(material.id))

                slot_data["options"].append({
                    "option_id": str(option.id),
                    "quantity": option.quantity,
                    "matching_material_ids": matching_materials
                })

            # Add to appropriate slot type list
            if slot.kind == SlotKind.CONSUMES:
                result["consumes"].append(slot_data)
            elif slot.kind == SlotKind.PRODUCES:
                result["produces"].append(slot_data)
            elif slot.kind == SlotKind.REQUIRES:
                result["requires"].append(slot_data)

        # Cache result if enabled
        if self.settings.l1_caching:
            l1_cache[cache_key] = result
        if self.settings.l2_caching:
            cache_service.set(cache_key, result, self.settings.cache_relationship_ttl)
        
        return result

    def find_recipes_for_material(self, material_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """
        Find all recipes in the project where this material can be used (consumed, produced, or required).
        
        Returns a dict with slot types (consumes, produces, requires) as keys,
        each containing a list of recipes with their matching slots.
        """
        cache_key = f"material_recipes:{project_id}:{material_id}"
        l1_cache = get_material_recipes_cache()
        cache_service = get_cache_service()
        
        # L1: Check local cache if enabled
        if self.settings.l1_caching and cache_key in l1_cache:
            return l1_cache[cache_key]
        
        # L2: Check Redis cache if enabled
        if self.settings.l2_caching:
            cached = cache_service.get(cache_key)
            if cached:
                if self.settings.l1_caching:
                    l1_cache[cache_key] = cached
                return cached
        
        # Compute result
        # Load material and its parameters once
        material = self.entity_service.get_basic_entity(material_id)
        if not material:
            return {"consumes": [], "produces": [], "requires": []}
        
        # Use cached parameters if available via entity_service
        material_params = self.entity_service.get_entity_parameters(material_id)
        
        # Load all recipes in the project
        recipes = self.entity_repo.list_by_project(project_id, kind="recipe")
        
        result = {
            "consumes": [],
            "produces": [],
            "requires": []
        }
        
        for recipe in recipes:
            # Load recipe structure
            slots = self.slot_repo.list_by_recipe_entity(recipe.id)
            
            recipe_matches = {
                "recipe_id": str(recipe.id),
                "slots": []
            }
            
            for slot in slots:
                options = self.option_repo.list_by_slot(slot.id)
                
                for option in options:
                    constraints = self.constraint_repo.list_by_option_as_specs(option.id)
                    
                    if self.constraint_resolution_service._material_matches_constraints(
                        material=material,
                        material_params=material_params,
                        constraints=constraints
                    ):
                        # Material matches this slot
                        recipe_matches["slots"].append({
                            "slot_id": str(slot.id),
                            "kind": slot.kind if isinstance(slot.kind, str) else slot.kind.value,
                            "quantity": option.quantity
                        })
                        break  # Only add slot once per recipe
            
            # Add recipe to appropriate slot type list if it has matching slots
            if recipe_matches["slots"]:
                # Determine which slot type(s) this recipe belongs to
                slot_kinds = {slot["kind"] for slot in recipe_matches["slots"]}
                
                if "consumes" in slot_kinds:
                    result["consumes"].append(recipe_matches.copy())
                if "produces" in slot_kinds:
                    result["produces"].append(recipe_matches.copy())
                if "requires" in slot_kinds:
                    result["requires"].append(recipe_matches.copy())
        
        # Cache result if enabled
        if self.settings.l1_caching:
            l1_cache[cache_key] = result
        if self.settings.l2_caching:
            cache_service.set(cache_key, result, self.settings.cache_relationship_ttl)
        
        return result
