"""Create initial HeatShield PostGIS schema.

Revision ID: 0001_heatshield
Revises:
Create Date: 2026-10-19
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


revision = "0001_heatshield"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "nodes",
        sa.Column("node_id", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="planned", nullable=False),
        sa.Column("firmware_version", sa.String(length=40), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('planned', 'active', 'maintenance', 'retired')", name="status_valid"),
        sa.PrimaryKeyConstraint("node_id", name="pk_nodes"),
    )
    op.create_index("ix_nodes_location_gist", "nodes", ["location"], unique=False, postgresql_using="gist")

    op.create_table(
        "resources",
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(length=24), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.CheckConstraint("resource_type IN ('water', 'shade', 'cooling', 'healthcare', 'other')", name="type_valid"),
        sa.CheckConstraint("status IN ('open', 'limited', 'closed', 'unknown')", name="status_valid"),
        sa.CheckConstraint("capacity IS NULL OR capacity >= 0", name="capacity_nonnegative"),
        sa.PrimaryKeyConstraint("resource_id", name="pk_resources"),
    )
    op.create_index("ix_resources_location_gist", "resources", ["location"], unique=False, postgresql_using="gist")

    op.create_table(
        "grid_cells",
        sa.Column("cell_id", sa.String(length=80), nullable=False),
        sa.Column("boundary", Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("air_temperature_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("wbgt_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("population_exposed", sa.BigInteger(), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        sa.CheckConstraint("population_exposed IS NULL OR population_exposed >= 0", name="population_nonnegative"),
        sa.PrimaryKeyConstraint("cell_id", name="pk_grid_cells"),
    )
    op.create_index("ix_grid_cells_boundary_gist", "grid_cells", ["boundary"], unique=False, postgresql_using="gist")
    op.create_index("ix_grid_cells_observed_on", "grid_cells", ["observed_on"], unique=False)

    op.create_table(
        "readings",
        sa.Column("reading_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("node_id", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("temperature_c", sa.Numeric(5, 2), nullable=False),
        sa.Column("relative_humidity_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("illuminance_lux", sa.Numeric(10, 2), nullable=False),
        sa.Column("globe_temperature_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("battery_voltage_v", sa.Numeric(5, 3), nullable=True),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
        sa.CheckConstraint("relative_humidity_pct BETWEEN 0 AND 100", name="humidity_range"),
        sa.CheckConstraint("illuminance_lux >= 0", name="illuminance_nonnegative"),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.node_id"], name="fk_readings_node_id_nodes", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("reading_id", name="pk_readings"),
    )
    op.create_index("ix_readings_node_observed_at", "readings", ["node_id", "observed_at"], unique=False)
    op.create_index("ix_readings_location_gist", "readings", ["location"], unique=False, postgresql_using="gist")

    op.create_table(
        "interventions",
        sa.Column("intervention_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cell_id", sa.String(length=80), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intervention_type", sa.String(length=24), nullable=False),
        sa.Column("units", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("cost_inr", sa.Numeric(12, 2), nullable=True),
        sa.Column("expected_risk_reduction", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="proposed", nullable=False),
        sa.Column("planned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("implemented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("intervention_type IN ('water', 'shade', 'cooling', 'other')", name="type_valid"),
        sa.CheckConstraint("units > 0", name="units_positive"),
        sa.CheckConstraint("cost_inr IS NULL OR cost_inr >= 0", name="cost_nonnegative"),
        sa.CheckConstraint("expected_risk_reduction IS NULL OR expected_risk_reduction BETWEEN 0 AND 100", name="risk_reduction_range"),
        sa.CheckConstraint("status IN ('proposed', 'approved', 'in_progress', 'completed', 'cancelled')", name="status_valid"),
        sa.ForeignKeyConstraint(["cell_id"], ["grid_cells.cell_id"], name="fk_interventions_cell_id_grid_cells", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.resource_id"], name="fk_interventions_resource_id_resources", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("intervention_id", name="pk_interventions"),
    )
    op.create_index("ix_interventions_cell_status", "interventions", ["cell_id", "status"], unique=False)

    op.create_table(
        "pilot_surveys",
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("cell_id", sa.String(length=80), nullable=True),
        sa.Column("age_band", sa.String(length=24), nullable=True),
        sa.Column("work_context", sa.String(length=40), nullable=True),
        sa.Column("heat_discomfort_level", sa.SmallInteger(), nullable=True),
        sa.Column("water_access", sa.String(length=20), nullable=True),
        sa.Column("shade_access", sa.String(length=20), nullable=True),
        sa.Column("experienced_heat_illness", sa.Boolean(), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False),
        sa.CheckConstraint("consent_given IS TRUE", name="consent_required"),
        sa.CheckConstraint("heat_discomfort_level IS NULL OR heat_discomfort_level BETWEEN 1 AND 5", name="discomfort_range"),
        sa.CheckConstraint("water_access IS NULL OR water_access IN ('easy', 'difficult', 'none', 'unknown')", name="water_access_valid"),
        sa.CheckConstraint("shade_access IS NULL OR shade_access IN ('easy', 'difficult', 'none', 'unknown')", name="shade_access_valid"),
        sa.ForeignKeyConstraint(["cell_id"], ["grid_cells.cell_id"], name="fk_pilot_surveys_cell_id_grid_cells", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("survey_id", name="pk_pilot_surveys"),
    )
    op.create_index("ix_pilot_surveys_submitted_at", "pilot_surveys", ["submitted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pilot_surveys_submitted_at", table_name="pilot_surveys")
    op.drop_table("pilot_surveys")
    op.drop_index("ix_interventions_cell_status", table_name="interventions")
    op.drop_table("interventions")
    op.drop_index("ix_readings_location_gist", table_name="readings")
    op.drop_index("ix_readings_node_observed_at", table_name="readings")
    op.drop_table("readings")
    op.drop_index("ix_grid_cells_observed_on", table_name="grid_cells")
    op.drop_index("ix_grid_cells_boundary_gist", table_name="grid_cells")
    op.drop_table("grid_cells")
    op.drop_index("ix_resources_location_gist", table_name="resources")
    op.drop_table("resources")
    op.drop_index("ix_nodes_location_gist", table_name="nodes")
    op.drop_table("nodes")