from sqlalchemy import create_engine, inspect, text

from app.db.base import Base
from app.db.migration_bootstrap import HEAD_REVISION, maybe_bootstrap_unmanaged_database
from app.models import EvaluationCaseResult, EvaluationRun, Incident


def test_models_import_correctly() -> None:
    assert Incident.__tablename__ == "incidents"
    assert EvaluationRun.__tablename__ == "evaluation_runs"
    assert EvaluationCaseResult.__tablename__ == "evaluation_case_results"


def test_sqlite_test_db_creates_expected_tables(db_session) -> None:
    inspector = inspect(db_session.bind)
    table_names = set(inspector.get_table_names())

    assert {
        "incidents",
        "agent_steps",
        "approval_requests",
        "audit_logs",
        "incident_memories",
        "evaluation_runs",
        "evaluation_case_results",
        "users",
        "user_sessions",
    }.issubset(table_names)


def test_expected_indexes_exist_on_sqlite_test_db(db_session) -> None:
    inspector = inspect(db_session.bind)

    incident_indexes = {item["name"] for item in inspector.get_indexes("incidents")}
    approval_indexes = {item["name"] for item in inspector.get_indexes("approval_requests")}
    agent_step_indexes = {item["name"] for item in inspector.get_indexes("agent_steps")}
    audit_indexes = {item["name"] for item in inspector.get_indexes("audit_logs")}

    assert "ix_incidents_status_severity" in incident_indexes
    assert "ix_incidents_created_at" in incident_indexes
    assert "ix_approval_requests_incident_id_status" in approval_indexes
    assert "ix_approval_requests_status_requested_at" in approval_indexes
    assert "ix_agent_steps_incident_id_step_number" in agent_step_indexes
    assert "ix_audit_logs_target_created_at" in audit_indexes


def test_existing_unmanaged_sqlite_db_can_be_bootstrapped_to_head(tmp_path) -> None:
    database_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE incidents (id INTEGER PRIMARY KEY, title VARCHAR NOT NULL)"))

        with engine.begin() as connection:
            bootstrapped = maybe_bootstrap_unmanaged_database(connection)

        assert bootstrapped is True

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "alembic_version" in tables
        assert {"users", "user_sessions", "evaluation_runs", "evaluation_case_results"}.issubset(tables)

        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

        assert revision == HEAD_REVISION
    finally:
        engine.dispose()


def test_existing_db_with_empty_alembic_version_table_can_be_bootstrapped(tmp_path) -> None:
    database_path = tmp_path / "legacy_with_empty_version.db"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE incidents (id INTEGER PRIMARY KEY, title VARCHAR NOT NULL)"))
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))

        with engine.begin() as connection:
            bootstrapped = maybe_bootstrap_unmanaged_database(connection)

        assert bootstrapped is True

        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

        assert revision == HEAD_REVISION
    finally:
        engine.dispose()


def test_stamped_legacy_db_gets_missing_columns_added(tmp_path) -> None:
    database_path = tmp_path / "stamped_legacy.db"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE incidents (
                        id INTEGER NOT NULL PRIMARY KEY,
                        title VARCHAR NOT NULL,
                        description TEXT NOT NULL,
                        source VARCHAR NOT NULL,
                        severity VARCHAR(8) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE approval_requests (
                        id INTEGER NOT NULL PRIMARY KEY,
                        incident_id INTEGER NOT NULL,
                        action_name VARCHAR NOT NULL,
                        risk_level VARCHAR(16) NOT NULL,
                        status VARCHAR(16) NOT NULL,
                        reason TEXT NOT NULL,
                        expected_impact TEXT NOT NULL,
                        rollback_plan TEXT NOT NULL,
                        requested_at DATETIME,
                        approved_by VARCHAR,
                        approved_at DATETIME
                    )
                    """
                )
            )
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                {"revision": HEAD_REVISION},
            )

        with engine.begin() as connection:
            repaired = maybe_bootstrap_unmanaged_database(connection)

        assert repaired is True

        approval_columns = {column["name"] for column in inspect(engine).get_columns("approval_requests")}
        assert "action_payload_json" in approval_columns
    finally:
        engine.dispose()
