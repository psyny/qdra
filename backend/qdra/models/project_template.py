import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID, DOUBLE_PRECISION
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class ProjectTemplate(Base):
    __tablename__ = "project_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_builtin: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectTemplateEntityType(Base):
    __tablename__ = "project_template_entity_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "project_template_id", "kind", "name", name="uq_entity_type_kind_name"
        ),
    )


class ProjectTemplateParameterDefinition(Base):
    __tablename__ = "project_template_parameter_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_templates.id"), nullable=False
    )
    entity_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_entity_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_label: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_unique: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_searchable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_value: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    validation_min: Mapped[Optional[float]] = mapped_column(DOUBLE_PRECISION, nullable=True)
    validation_max: Mapped[Optional[float]] = mapped_column(DOUBLE_PRECISION, nullable=True)
    validation_regex: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "entity_type_id", "domain", "key", name="uq_param_def_entity_type_domain_key"
        ),
    )


class ProjectTemplateView(Base):
    __tablename__ = "project_template_views"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_templates.id"), nullable=False
    )
    view_key: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    configs: Mapped[List["ProjectTemplateViewConfig"]] = relationship(
        "ProjectTemplateViewConfig", backref="view", order_by="ProjectTemplateViewConfig.sort_order"
    )

    __table_args__ = (
        UniqueConstraint(
            "project_template_id", "view_key", name="uq_view_template_key"
        ),
    )


class ProjectTemplateViewConfig(Base):
    __tablename__ = "project_template_view_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    view_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_template_views.id"), nullable=False
    )
    entity_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_entity_types.id"),
        nullable=True,
    )
    filter_params: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    display_slots: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectTemplateSlotGroup(Base):
    __tablename__ = "project_template_slot_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_entity_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    min_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_slots: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("entity_type_id", "kind", name="uq_slot_group_entity_type_kind"),
        CheckConstraint("min_slots >= 0", name="ck_slot_group_min_slots_non_negative"),
        CheckConstraint(
            "max_slots IS NULL OR max_slots >= min_slots",
            name="ck_slot_group_max_slots_ge_min",
        ),
    )


class ProjectTemplateSlotDefinition(Base):
    __tablename__ = "project_template_slot_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_key: Mapped[str] = mapped_column(String(100), nullable=False)
    min_occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_occurrences: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("slot_group_id", "slot_key", name="uq_slot_def_group_key"),
        CheckConstraint("min_occurrences >= 0", name="ck_slot_def_min_occurrences_non_negative"),
        CheckConstraint(
            "max_occurrences IS NULL OR max_occurrences >= min_occurrences",
            name="ck_slot_def_max_occurrences_ge_min",
        ),
    )


class ProjectTemplateSlotConstraint(Base):
    __tablename__ = "project_template_slot_constraints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
        nullable=True,
    )
    slot_definition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_slot_definitions.id", ondelete="CASCADE"),
        nullable=True,
    )
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    operator: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    value_string: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_number: Mapped[Optional[float]] = mapped_column(DOUBLE_PRECISION, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_wildcard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "(slot_group_id IS NOT NULL AND slot_definition_id IS NULL) OR "
            "(slot_group_id IS NULL AND slot_definition_id IS NOT NULL)",
            name="ck_slot_constraint_exactly_one_parent",
        ),
    )
