import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.slot import Slot, SlotKind


class SlotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, recipe_id: uuid.UUID, kind: SlotKind) -> Slot:
        slot = Slot(recipe_id=recipe_id, kind=kind)
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def get_by_id(self, slot_id: uuid.UUID) -> Optional[Slot]:
        return self.db.query(Slot).filter(Slot.id == slot_id).first()

    def list_by_recipe(self, recipe_id: uuid.UUID) -> List[Slot]:
        return self.db.query(Slot).filter(Slot.recipe_id == recipe_id).all()
