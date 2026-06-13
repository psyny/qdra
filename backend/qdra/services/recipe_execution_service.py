import uuid
from typing import List, Set
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

from services.recipe_evaluation_service import RecipeEvaluationService

from domain.evaluation import RecipeExecutionResult, Allocation


class RecipeExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.material_repo = MaterialRepository(db)
        self.recipe_repo = RecipeRepository(db)
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.parameter_repo = ParameterRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)
        self.evaluation_service = RecipeEvaluationService(db)

    def execute_recipe(
        self, recipe_id: uuid.UUID, material_ids: List[uuid.UUID]
    ) -> RecipeExecutionResult:
        """
        Execute a recipe against a set of materials.
        
        Returns a RecipeExecutionResult with the new state.
        """
        # Capture state before execution
        state_before = set(material_ids)
        
        # Evaluate recipe first
        evaluation_result = self.evaluation_service.evaluate_recipe(recipe_id, material_ids)
        
        if not evaluation_result.success:
            # Evaluation failed - return failure without modifying state
            return RecipeExecutionResult(
                success=False,
                recipe_id=recipe_id,
                consumed_material_ids=[],
                required_material_ids=[],
                produced_material_ids=[],
                state_before=list(state_before),
                state_after=list(state_before)
            )
        
        # Load recipe structure
        recipe = self.recipe_repo.get_by_id(recipe_id)
        if not recipe:
            return RecipeExecutionResult(
                success=False,
                recipe_id=recipe_id,
                consumed_material_ids=[],
                required_material_ids=[],
                produced_material_ids=[],
                state_before=list(state_before),
                state_after=list(state_before)
            )
        
        slots = self.slot_repo.list_by_recipe(recipe_id)
        
        # Categorize allocations by slot kind
        consumed_materials: Set[uuid.UUID] = set()
        required_materials: Set[uuid.UUID] = set()
        produced_materials: List[uuid.UUID] = []
        
        for allocation in evaluation_result.allocations:
            slot = next((s for s in slots if s.id == allocation.slot_id), None)
            if slot:
                if slot.kind == SlotKind.CONSUMES:
                    consumed_materials.add(allocation.material_id)
                elif slot.kind == SlotKind.REQUIRES:
                    required_materials.add(allocation.material_id)
        
        # Create produced materials
        for slot in slots:
            if slot.kind == SlotKind.PRODUCES:
                produced = self._create_produced_materials(
                    slot=slot,
                    recipe_id=recipe_id,
                    project_id=recipe.project_id
                )
                produced_materials.extend(produced)
        
        # Calculate state after execution
        # Remove consumed, keep required, add produced
        state_after = state_before - consumed_materials
        state_after = state_after.union(set(produced_materials))
        
        return RecipeExecutionResult(
            success=True,
            recipe_id=recipe_id,
            consumed_material_ids=list(consumed_materials),
            required_material_ids=list(required_materials),
            produced_material_ids=produced_materials,
            state_before=list(state_before),
            state_after=list(state_after)
        )
    
    def _create_produced_materials(
        self, slot: Slot, recipe_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[uuid.UUID]:
        """
        Create materials from a PRODUCES slot.
        
        Uses the option constraints to define material parameters.
        """
        options = self.option_repo.list_by_slot(slot.id)
        produced_ids: List[uuid.UUID] = []
        
        for option in options:
            quantity = int(option.quantity)
            constraints = self.constraint_repo.list_by_option(option.id)
            
            # Create the specified quantity of materials
            for _ in range(quantity):
                material = self.material_repo.create(project_id)
                
                # Convert constraints to parameters
                for constraint in constraints:
                    if constraint.operator == "=" and not constraint.is_wildcard:
                        # Only equality constraints can be used for material creation
                        self._create_parameter_from_constraint(
                            material_id=material.id,
                            constraint=constraint
                        )
                
                produced_ids.append(material.id)
        
        return produced_ids
    
    def _create_parameter_from_constraint(
        self, material_id: uuid.UUID, constraint: ParameterConstraint
    ) -> Parameter:
        """
        Create a material parameter from a constraint.
        
        Only supports equality constraints for material creation.
        """
        return self.parameter_repo.create(
            material_id=material_id,
            domain=constraint.domain,
            key=constraint.key,
            value_string=constraint.value_string,
            value_number=constraint.value_number,
            value_boolean=constraint.value_boolean
        )
