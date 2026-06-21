from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CustomType(Base):
    __tablename__ = "custom_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_custom_types_project_name"),
        Index("idx_custom_types_project_id", "project_id"),
    )


class FieldDefinition(Base):
    __tablename__ = "field_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    type_id = Column(
        UUID(as_uuid=True), ForeignKey("custom_types.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    field_type = Column(String(50), nullable=False)  # string, number, boolean, etc.
    required = Column(String(10), default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_field_definitions_project_name"),
        Index("idx_field_definitions_project_id", "project_id"),
    )


class Object(Base):
    __tablename__ = "objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    type_id = Column(
        UUID(as_uuid=True), ForeignKey("custom_types.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_objects_project_name"),
        Index("idx_objects_project_id", "project_id"),
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_object_id = Column(
        UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False
    )
    target_object_id = Column(
        UUID(as_uuid=True), ForeignKey("objects.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_relationships_project_id", "project_id"),
        Index("idx_relationships_source", "source_object_id"),
        Index("idx_relationships_target", "target_object_id"),
    )


class ReasoningJob(Base):
    __tablename__ = "reasoning_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(50), nullable=False, default="queued")  # queued, running, succeeded, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_reasoning_jobs_project_id", "project_id"),
        Index("idx_reasoning_jobs_status", "status"),
    )


class PlanningRun(Base):
    __tablename__ = "planning_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    type = Column(String(255), nullable=False)  # "output_solver", etc
    result = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_planning_runs_status", "status"),
        Index("idx_planning_runs_type", "type"),
    )
