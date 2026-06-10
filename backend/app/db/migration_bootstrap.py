from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.schema import CreateColumn

from app.db.base import Base


HEAD_REVISION = "0002_auth_foundation"


def _is_sqlite(connection: Connection) -> bool:
    return connection.dialect.name == "sqlite"


def reconcile_sqlite_schema(connection: Connection) -> bool:
    """Add missing tables, columns, and indexes for legacy local SQLite DBs.

    This keeps pre-Alembic demo databases usable. It only performs additive
    changes that SQLite can apply safely with simple ALTER TABLE statements.
    """

    if not _is_sqlite(connection):
        return False

    changed = False
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    metadata_tables = Base.metadata.tables

    missing_tables = set(metadata_tables.keys()) - existing_tables
    if missing_tables:
        Base.metadata.create_all(bind=connection)
        changed = True
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())

    for table_name, table in metadata_tables.items():
        if table_name not in existing_tables:
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue
            column_sql = str(CreateColumn(column).compile(dialect=connection.dialect))
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))
            changed = True

        existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
        for index in table.indexes:
            if index.name in existing_indexes:
                continue
            index.create(bind=connection)
            changed = True

    return changed


def maybe_bootstrap_unmanaged_database(connection: Connection) -> bool:
    """Stamp a pre-Alembic local DB if it already contains managed tables."""

    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    if not existing_tables:
        return False

    managed_tables = set(Base.metadata.tables.keys())
    if not (existing_tables & managed_tables):
        return False

    has_version_table = "alembic_version" in existing_tables
    if has_version_table:
        current_revision = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
        if current_revision and current_revision != HEAD_REVISION:
            return False
        if current_revision == HEAD_REVISION:
            return reconcile_sqlite_schema(connection)

    reconcile_sqlite_schema(connection)
    connection.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
    connection.execute(text("DELETE FROM alembic_version"))
    connection.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": HEAD_REVISION},
    )
    return True
