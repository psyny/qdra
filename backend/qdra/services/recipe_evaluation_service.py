import uuid
from typing import List, Set, Optional
from sqlalchemy.orm import Session

from models.material import Material
from models.recipe import Recipe
from models.slot import Slot, SlotKind
from models.option import Option
from models.parameter import Parameter
from models.parameter_constraint import ParameterConstraint

from repositories.material_repository import MaterialRepository
from repositories.recipe_repository import RecipeRepository
from repositories.slot_repository import SlotRepository
from repositories.option_repository import OptionRepository
from repositories.parameter_repository import ParameterRepository
from repositories.parameter_constraint_repository import ParameterConstraintRepository

from services.constraint_matcher import ConstraintMatcher

from domain.state import State
from domain.evaluation import RecipeMatchResult, SlotMatchResult, Allocation


class RecipeEvaluationService:
    def __init__(self, db: Session):
        self.db = db
        self.material_repo = MaterialRepository(db)
        self.recipe_repo = RecipeRepository(db)
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.parameter_repo = ParameterRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)

    def evaluate_recipe(
        self, recipe_id: uuid.UUID, material_ids: List[uuid.UUID]
    ) -> RecipeMatchResult:
        """
        Evaluate if a recipe can execute given a set of materials.
        
        Returns a RecipeMatchResult with success status and allocations.
        """
        # Load recipe
        recipe = self.recipe_repo.get_by_id(recipe_id)
        if not recipe:
            return RecipeMatchResult(
                success=False,
                recipe_id=recipe_id,
                slot_results=[],
                allocations=[]
            )

        # Load materials with their parameters
        materials = []
        material_params_map = {}
        for material_id in material_ids:
            material = self.material_repo.get_by_id(material_id)
            if material:
                materials.append(material)
                material_params_map[material_id] = self.parameter_repo.list_by_material(material_id)

        # Load recipe structure
        slots = self.slot_repo.list_by_recipe(recipe_id)
        
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
        materials: List[Material],
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
        materials: List[Material],
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
        material: Material,
        constraints: List[ParameterConstraint],
        material_params_map: dict
    ) -> bool:
        """
        Check if a material matches all constraints in an option.
        """
        for constraint in constraints:
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
