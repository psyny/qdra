import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Float, String, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class RecipeParameter(Base):
    __tablename__ = "recipe_parameters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value_string: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_number: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="parameters")

    __table_args__ = (
        CheckConstraint(
            "(value_string IS NOT NULL)::integer + (value_number IS NOT NULL)::integer + (value_boolean IS NOT NULL)::integer = 1",
            name="ck_recipe_exactly_one_value",
        ),
        {"extend_existing": True},
    )
