from dataclasses import dataclass
from typing import List
from models.material import Material


@dataclass
class State:
    """Represents the currently available materials."""
    materials: List[Material]
