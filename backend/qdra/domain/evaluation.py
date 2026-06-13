import uuid
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Allocation:
    """Represents a material allocated to a slot."""
    material_id: uuid.UUID
    slot_id: uuid.UUID
    option_id: uuid.UUID


@dataclass
class SlotMatchResult:
    """Result of matching a single slot."""
    slot_id: uuid.UUID
    success: bool
    matched_option_id: Optional[uuid.UUID] = None
    allocated_materials: List[uuid.UUID] = None
    
    def __post_init__(self):
        if self.allocated_materials is None:
            self.allocated_materials = []


@dataclass
class RecipeMatchResult:
    """Result of evaluating a recipe against a state."""
    success: bool
    recipe_id: uuid.UUID
    slot_results: List[SlotMatchResult]
    allocations: List[Allocation]
