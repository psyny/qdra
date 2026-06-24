import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class ProjectUserPermissions(Base):
    __tablename__ = "project_user_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    can_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_manage_project_users: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_create_material: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_edit_material: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_delete_material: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_create_recipe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_edit_recipe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_delete_recipe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_run_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        {"schema": None},  # Use default schema
    )
