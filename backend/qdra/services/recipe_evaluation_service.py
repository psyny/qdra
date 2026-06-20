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

from services.constraint_matcher import ConstraintMatcher

from domain.evaluation import RecipeMatchResult, SlotMatchResult, Allocation


class RecipeEvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = EntityRepository(db)
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.entity_parameter_repo = EntityParameterRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)

    def evaluate_recipe(
        self, recipe_id: uuid.UUID, material_ids: List[uuid.UUID]
    ) -> RecipeMatchResult:
        """
        Evaluate if a recipe entity can execute given a set of material entity IDs.

        Returns a RecipeMatchResult with success status and allocations.
        """
        recipe = self.entity_repo.get_by_id(recipe_id)
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
            material = self.entity_repo.get_by_id(material_id)
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
        constraints = self.constraint_repo.list_by_option(option.id)
        matching_materials: List[uuid.UUID] = []

        for material in materials:
            # Skip if already allocated
            if material.id in allocated_materials:
                continue

            # Check if material matches all constraints
            if self._material_matches_constraints(
                material=material,
                constraints=constraints,
                material_params_map=material_params_map
            ):
                matching_materials.append(material.id)

        return matching_materials

    def _material_matches_constraints(
        self,
        material: Entity,
        constraints: List[ParameterConstraint],
        material_params_map: dict
    ) -> bool:
        """
        Check if a material matches all constraints in an option.
        """
        for constraint in constraints:
            # Special handling for material_id constraint
            if constraint.domain == "identity" and constraint.key == "material_id":
                if constraint.operator == "=" and constraint.value_string:
                    if str(material.id) != constraint.value_string:
                        return False
                else:
                    return False
                continue
            
            # Find matching parameter
            material_params = material_params_map.get(material.id, [])
            matched = False
            
            for param in material_params:
                if ConstraintMatcher.matches(param, constraint):
                    matched = True
                    break
            
            if not matched:
                return False
        
        return True

    def find_materials_for_recipe_slots(self, recipe_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """
        Find all materials in the project that match each slot's constraints.
        
        Returns a dict with slot types (consumes, produces, requires) as keys,
        each containing a list of slots with their matching material IDs.
        """
        recipe = self.entity_repo.get_by_id(recipe_id)
        if not recipe:
            return {"consumes": [], "produces": [], "requires": []}

        # Load all materials in the project
        materials = self.entity_repo.list_by_project(project_id, kind="material")
        material_params_map = {}
        for material in materials:
            material_params_map[material.id] = (
                self.entity_parameter_repo.list_by_entity(material.id)
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
                constraints = self.constraint_repo.list_by_option(option.id)
                matching_materials = []

                for material in materials:
                    if self._material_matches_constraints(
                        material=material,
                        constraints=constraints,
                        material_params_map=material_params_map
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

        return result
