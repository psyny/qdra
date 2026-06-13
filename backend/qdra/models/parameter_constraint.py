import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Operator(str, Enum):
    EQ = "="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    IN = "in"
    EXISTS = "exists"


class ParameterConstraint(Base):
    __tablename__ = "parameter_constraints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("options.id"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    operator: Mapped[Operator] = mapped_column(String(50), nullable=False)
    value_string: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_number: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_wildcard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
