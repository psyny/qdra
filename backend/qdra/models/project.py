import uuid
from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, String, func, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_templates.id"), nullable=False
    )
    image_size_px: Mapped[int] = mapped_column(
        Integer, nullable=False, default=256
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    entities: Mapped[List["Entity"]] = relationship(
        "Entity", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("image_size_px >= 32", name="check_image_size_min"),
        CheckConstraint("image_size_px <= 1024", name="check_image_size_max"),
    )
