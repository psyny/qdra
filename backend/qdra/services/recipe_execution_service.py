import uuid
from typing import List, Optional, Set
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
from repositories.project_repository import ProjectRepository
from repositories.project_template_repository import ProjectTemplateRepository
from qdra.infrastructure.cache.cache_service import CacheService

from services.recipe_evaluation_service import RecipeEvaluationService

from domain.evaluation import RecipeExecutionResult, Allocation


class RecipeExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = EntityRepository(db, CacheService())
        self.slot_repo = SlotRepository(db)
        self.option_repo = OptionRepository(db)
        self.entity_parameter_repo = EntityParameterRepository(db)
        self.constraint_repo = ParameterConstraintRepository(db)
        self.project_repo = ProjectRepository(db)
        self.template_repo = ProjectTemplateRepository(db)
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
        recipe = self.entity_repo.get_by_id(recipe_id)
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

        slots = self.slot_repo.list_by_recipe_entity(recipe_id)
        
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
        
        # Create produced entities
        for slot in slots:
            if slot.kind == SlotKind.PRODUCES:
                produced = self._create_produced_entities(
                    slot=slot,
                    recipe=recipe,
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
    
    def _get_default_material_entity_type_id(
        self, recipe: Entity
    ) -> Optional[uuid.UUID]:
        """Get the first material-kind entity type from the recipe's project template."""
        project = self.project_repo.get_by_id(recipe.project_id)
        if not project or not project.project_template_id:
            return None
        types = self.template_repo.list_entity_types(
            project.project_template_id, kind="material"
        )
        return types[0].id if types else None

    def _create_produced_entities(
        self, slot: Slot, recipe: Entity
    ) -> List[uuid.UUID]:
        """
        Create material entities from a PRODUCES slot.

        Uses the option constraints to define entity parameters.
        """
        options = self.option_repo.list_by_slot(slot.id)
        produced_ids: List[uuid.UUID] = []

        entity_type_id = self._get_default_material_entity_type_id(recipe)
        if not entity_type_id:
            return produced_ids

        for option in options:
            quantity = int(option.quantity or 1)
            constraints = self.constraint_repo.list_by_option(option.id)

            for _ in range(quantity):
                entity = self.entity_repo.create(
                    project_id=recipe.project_id,
                    entity_type_id=entity_type_id,
                )

                for constraint in constraints:
                    if constraint.operator == "=" and not constraint.is_wildcard:
                        self.entity_parameter_repo.create(
                            entity_id=entity.id,
                            domain=constraint.domain,
                            key=constraint.key,
                            value_string=constraint.value_string,
                            value_number=constraint.value_number,
                            value_boolean=constraint.value_boolean,
                        )

                produced_ids.append(entity.id)

        return produced_ids
