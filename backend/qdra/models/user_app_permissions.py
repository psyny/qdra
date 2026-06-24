import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class UserAppPermissions(Base):
    __tablename__ = "user_app_permissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    can_manage_users: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_create_projects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_edit_projects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_delete_projects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_create_templates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_edit_templates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_delete_templates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
