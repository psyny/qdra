from dataclasses import dataclass
from typing import List
from models.entity import Entity


@dataclass
class State:
    """Represents the currently available entities (materials/recipes)."""
    entities: List[Entity]
