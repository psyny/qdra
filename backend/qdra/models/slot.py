import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class SlotKind(str, Enum):
    CONSUMES = "CONSUMES"
    REQUIRES = "REQUIRES"
    PRODUCES = "PRODUCES"


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False
    )
    kind: Mapped[SlotKind] = mapped_column(String(50), nullable=False)
