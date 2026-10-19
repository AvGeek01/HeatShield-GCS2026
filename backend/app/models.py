"""SQLAlchemy schema for the HeatShield Delhi pilot."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Node(Base):
    __tablename__ = "nodes"

    node_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="planned")
    firmware_version: Mapped[str | None] = mapped_column(String(40))
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('planned', 'active', 'maintenance', 'retired')", name="status_valid"),
        Index("ix_nodes_location_gist", "location", postgresql_using="gist"),
    )


class Reading(Base):
    __tablename__ = "readings"

    reading_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.node_id", ondelete="RESTRICT"), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    temperature_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    relative_humidity_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    illuminance_lux: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    globe_temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    battery_voltage_v: Mapped[Decimal | None] = mapped_column(Numeric(5, 3))
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)

    __table_args__ = (
        CheckConstraint("relative_humidity_pct BETWEEN 0 AND 100", name="humidity_range"),
        CheckConstraint("illuminance_lux >= 0", name="illuminance_nonnegative"),
        Index("ix_readings_node_observed_at", "node_id", "observed_at"),
        Index("ix_readings_location_gist", "location", postgresql_using="gist"),
    )


class Resource(Base):
    __tablename__ = "resources"

    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="unknown")
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str | None] = mapped_column(String(80))
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        CheckConstraint("resource_type IN ('water', 'shade', 'cooling', 'healthcare', 'other')", name="type_valid"),
        CheckConstraint("status IN ('open', 'limited', 'closed', 'unknown')", name="status_valid"),
        CheckConstraint("capacity IS NULL OR capacity >= 0", name="capacity_nonnegative"),
        Index("ix_resources_location_gist", "location", postgresql_using="gist"),
    )


class GridCell(Base):
    __tablename__ = "grid_cells"

    cell_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    boundary: Mapped[Any] = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=False), nullable=False)
    observed_on: Mapped[date] = mapped_column(Date, nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    air_temperature_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    wbgt_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    population_exposed: Mapped[int | None] = mapped_column(BigInteger)
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        CheckConstraint("population_exposed IS NULL OR population_exposed >= 0", name="population_nonnegative"),
        Index("ix_grid_cells_boundary_gist", "boundary", postgresql_using="gist"),
        Index("ix_grid_cells_observed_on", "observed_on"),
    )


class Intervention(Base):
    __tablename__ = "interventions"

    intervention_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cell_id: Mapped[str] = mapped_column(ForeignKey("grid_cells.cell_id", ondelete="RESTRICT"), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resources.resource_id", ondelete="SET NULL"))
    intervention_type: Mapped[str] = mapped_column(String(24), nullable=False)
    units: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    cost_inr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expected_risk_reduction: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="proposed")
    planned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    implemented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("intervention_type IN ('water', 'shade', 'cooling', 'other')", name="type_valid"),
        CheckConstraint("units > 0", name="units_positive"),
        CheckConstraint("cost_inr IS NULL OR cost_inr >= 0", name="cost_nonnegative"),
        CheckConstraint("expected_risk_reduction IS NULL OR expected_risk_reduction BETWEEN 0 AND 100", name="risk_reduction_range"),
        CheckConstraint("status IN ('proposed', 'approved', 'in_progress', 'completed', 'cancelled')", name="status_valid"),
        Index("ix_interventions_cell_status", "cell_id", "status"),
    )


class PilotSurvey(Base):
    __tablename__ = "pilot_surveys"

    survey_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cell_id: Mapped[str | None] = mapped_column(ForeignKey("grid_cells.cell_id", ondelete="SET NULL"))
    age_band: Mapped[str | None] = mapped_column(String(24))
    work_context: Mapped[str | None] = mapped_column(String(40))
    heat_discomfort_level: Mapped[int | None] = mapped_column(SmallInteger)
    water_access: Mapped[str | None] = mapped_column(String(20))
    shade_access: Mapped[str | None] = mapped_column(String(20))
    experienced_heat_illness: Mapped[bool | None] = mapped_column(Boolean)
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        CheckConstraint("consent_given IS TRUE", name="consent_required"),
        CheckConstraint("heat_discomfort_level IS NULL OR heat_discomfort_level BETWEEN 1 AND 5", name="discomfort_range"),
        CheckConstraint("water_access IS NULL OR water_access IN ('easy', 'difficult', 'none', 'unknown')", name="water_access_valid"),
        CheckConstraint("shade_access IS NULL OR shade_access IN ('easy', 'difficult', 'none', 'unknown')", name="shade_access_valid"),
        Index("ix_pilot_surveys_submitted_at", "submitted_at"),
    )