from geoalchemy2 import Geometry
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from backend.app.database import database_url_from_env
from backend.app.models import Base


def test_initial_schema_has_expected_tables_and_spatial_indexes() -> None:
    assert set(Base.metadata.tables) == {
        "nodes",
        "readings",
        "resources",
        "grid_cells",
        "interventions",
        "pilot_surveys",
    }
    spatial_tables = {"nodes", "readings", "resources", "grid_cells"}
    for table_name in spatial_tables:
        table = Base.metadata.tables[table_name]
        geometry_columns = [column for column in table.columns if isinstance(column.type, Geometry)]
        assert geometry_columns
        spatial_indexes = [index for index in table.indexes if index.dialect_options["postgresql"].get("using") == "gist"]
        assert len(spatial_indexes) == 1
        assert all(column.type.srid == 4326 for column in geometry_columns)


def test_schema_ddl_compiles_for_postgresql() -> None:
    for table in Base.metadata.sorted_tables:
        str(CreateTable(table).compile(dialect=postgresql.dialect()))


def test_database_url_selects_psycopg_driver(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://heatshield:local-only@db:5432/heatshield")
    assert database_url_from_env() == "postgresql+psycopg://heatshield:local-only@db:5432/heatshield"