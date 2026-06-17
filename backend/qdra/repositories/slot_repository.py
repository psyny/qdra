import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.slot import Slot, SlotKind


class SlotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        recipe_entity_id: uuid.UUID,
        kind: str,
        sort_order: int = 0,
    ) -> Slot:
        slot = Slot(
            recipe_entity_id=recipe_entity_id,
            kind=kind,
            sort_order=sort_order,
        )
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def get_by_id(self, slot_id: uuid.UUID) -> Optional[Slot]:
        return self.db.query(Slot).filter(Slot.id == slot_id).first()

    def list_by_recipe_entity(self, recipe_entity_id: uuid.UUID) -> List[Slot]:
        return (
            self.db.query(Slot)
            .filter(Slot.recipe_entity_id == recipe_entity_id)
            .order_by(Slot.sort_order)
            .all()
        )

    def delete(self, slot_id: uuid.UUID) -> bool:
        slot = self.get_by_id(slot_id)
        if not slot:
            return False
        self.db.delete(slot)
        self.db.commit()
        return True
