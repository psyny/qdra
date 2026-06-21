import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Float, Integer, String, Text, UniqueConstraint, func, CheckConstraint
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

    parameter_definitions: Mapped[List["ProjectTemplateParameterDefinition"]] = relationship(
        "ProjectTemplateParameterDefinition", backref="entity_type", order_by="ProjectTemplateParameterDefinition.sort_order"
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
    type: Mapped[str] = mapped_column(String(50), nullable=False)
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
        UniqueConstraint("entity_type_id", "type", name="uq_slot_group_entity_type_type"),
        CheckConstraint("min_slots >= 0", name="ck_slot_group_min_slots_non_negative"),
        CheckConstraint(
            "max_slots IS NULL OR max_slots >= min_slots",
            name="ck_slot_group_max_slots_ge_min",
        ),
    )

    default_slot: Mapped[Optional["ProjectTemplateDefaultSlot"]] = relationship(
        "ProjectTemplateDefaultSlot", backref="slot_group", uselist=False
    )
    per_slots: Mapped[List["ProjectTemplatePerSlot"]] = relationship(
        "ProjectTemplatePerSlot", backref="slot_group", order_by="ProjectTemplatePerSlot.sort_order",
        cascade="all, delete-orphan"
    )


class Operator(str, Enum):
    EQ = "="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    IN = "in"
    EXISTS = "exists"


class ProjectTemplateDefaultSlot(Base):
    __tablename__ = "project_template_default_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    options: Mapped[List["ProjectTemplateDefaultOption"]] = relationship(
        "ProjectTemplateDefaultOption", backref="default_slot", order_by="ProjectTemplateDefaultOption.sort_order",
        cascade="all, delete-orphan"
    )


class ProjectTemplateDefaultOption(Base):
    __tablename__ = "project_template_default_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    default_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_default_slots.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parameter_constraints: Mapped[List["ProjectTemplateDefaultParameterConstraint"]] = relationship(
        "ProjectTemplateDefaultParameterConstraint", backref="default_option",
        cascade="all, delete-orphan"
    )


class ProjectTemplateDefaultParameterConstraint(Base):
    __tablename__ = "project_template_default_parameter_constraints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    default_option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_default_options.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    operator: Mapped[Operator] = mapped_column(String(50), nullable=False)
    value_string: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_number: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_wildcard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectTemplatePerSlot(Base):
    __tablename__ = "project_template_per_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_slot_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    options: Mapped[List["ProjectTemplatePerOption"]] = relationship(
        "ProjectTemplatePerOption", backref="per_slot", order_by="ProjectTemplatePerOption.sort_order",
        cascade="all, delete-orphan"
    )


class ProjectTemplatePerOption(Base):
    __tablename__ = "project_template_per_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    per_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_per_slots.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parameter_constraints: Mapped[List["ProjectTemplatePerParameterConstraint"]] = relationship(
        "ProjectTemplatePerParameterConstraint", backref="per_option",
        cascade="all, delete-orphan"
    )


class ProjectTemplatePerParameterConstraint(Base):
    __tablename__ = "project_template_per_parameter_constraints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    per_option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_template_per_options.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    operator: Mapped[Operator] = mapped_column(String(50), nullable=False)
    value_string: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_number: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_wildcard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


