import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.option import Option


class OptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, slot_id: uuid.UUID, quantity: float, sort_order: int = 0) -> Option:
        option = Option(slot_id=slot_id, quantity=quantity, sort_order=sort_order)
        self.db.add(option)
        self.db.commit()
        self.db.refresh(option)
        return option

    def get_by_id(self, option_id: uuid.UUID) -> Optional[Option]:
        return self.db.query(Option).filter(Option.id == option_id).first()

    def list_by_slot(self, slot_id: uuid.UUID) -> List[Option]:
        return self.db.query(Option).filter(Option.slot_id == slot_id).all()
