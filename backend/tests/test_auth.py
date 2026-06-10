from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.main import create_app
from app.schemas.approval import ApprovalRequestCreate
from app.schemas.enums import IncidentStatus, RiskLevel, Severity, UserRole
from app.schemas.incident import IncidentCreate
from app.services.approvals import ApprovalService
from app.services.auth import AuthService, UserAlreadyExistsError
from app.services.incidents import IncidentService


def create_auth_test_app(monkeypatch: pytest.MonkeyPatch, db_session: Session, *, dashboard_auth: bool = False):
    monkeypatch.setenv("ENABLE_AUTH", "true")
    monkeypatch.setenv("ENABLE_DASHBOARD_AUTH", "true" if dashboard_auth else "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    return app, get_settings


@pytest.mark.anyio
async def test_user_creation_and_duplicate_protection(db_session: Session) -> None:
    service = AuthService(db_session)
    user = service.create_user(
        email="operator@opspilot.local",
        name="Ops Operator",
        role=UserRole.operator,
        password="change-me-now",
    )

    assert user.email == "operator@opspilot.local"
    assert user.role == UserRole.operator
    assert user.hashed_password

    with pytest.raises(UserAlreadyExistsError):
        service.create_user(
            email="operator@opspilot.local",
            name="Duplicate",
            role=UserRole.viewer,
            password="change-me-now",
        )


@pytest.mark.anyio
async def test_login_sets_cookie_and_allows_operator_routes(monkeypatch: pytest.MonkeyPatch, db_session: Session) -> None:
    app, settings_cache = create_auth_test_app(monkeypatch, db_session)
    try:
        AuthService(db_session).create_user(
            email="operator@opspilot.local",
            name="Ops Operator",
            role=UserRole.operator,
            password="change-me-now",
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            login = await client.post(
                "/api/auth/login",
                json={"email": "operator@opspilot.local", "password": "change-me-now"},
            )
            create = await client.post(
                "/api/incidents",
                json={
                    "title": "API error rate spike",
                    "description": "5xx responses increasing quickly",
                    "source": "monitoring",
                    "severity": "high",
                },
            )

        assert login.status_code == 200
        assert "set-cookie" in login.headers
        assert create.status_code == 201
        assert create.json()["title"] == "API error rate spike"
    finally:
        settings_cache.cache_clear()


@pytest.mark.anyio
async def test_role_checks_enforce_reviewer_vs_operator(monkeypatch: pytest.MonkeyPatch, db_session: Session) -> None:
    app, settings_cache = create_auth_test_app(monkeypatch, db_session)
    incident = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="Queue backlog",
            description="Jobs are piling up in the queue",
            source="monitoring",
            severity=Severity.high,
        )
    )
    approval = ApprovalService(db_session).create_request(
        ApprovalRequestCreate(
            incident_id=incident.id,
            action_name="scale_workers_simulation",
            risk_level=RiskLevel.dangerous,
            reason="Worker pool appears saturated.",
            expected_impact="More workers will process backlog faster.",
            rollback_plan="Scale back to the previous worker count.",
            action_payload_json={"action_name": "scale_workers_simulation"},
        )
    )

    AuthService(db_session).create_user(
        email="reviewer@opspilot.local",
        name="Risk Reviewer",
        role=UserRole.reviewer,
        password="change-me-now",
    )
    AuthService(db_session).create_user(
        email="viewer@opspilot.local",
        name="Read Only",
        role=UserRole.viewer,
        password="change-me-now",
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as reviewer_client:
            reviewer_login = await reviewer_client.post(
                "/api/auth/login",
                json={"email": "reviewer@opspilot.local", "password": "change-me-now"},
            )
            approve = await reviewer_client.post(
                f"/api/approvals/{approval.id}/approve",
                json={"approved_by": "reviewer@opspilot.local"},
            )
            reviewer_create = await reviewer_client.post(
                "/api/incidents",
                json={
                    "title": "Should fail",
                    "description": "Reviewers cannot create incidents",
                    "source": "manual",
                    "severity": "medium",
                },
            )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as viewer_client:
            viewer_login = await viewer_client.post(
                "/api/auth/login",
                json={"email": "viewer@opspilot.local", "password": "change-me-now"},
            )
            viewer_read = await viewer_client.get("/api/incidents")
            viewer_create = await viewer_client.post(
                "/api/incidents",
                json={
                    "title": "Viewer blocked",
                    "description": "Viewer should not create incidents",
                    "source": "manual",
                    "severity": "low",
                },
            )

        assert reviewer_login.status_code == 200
        assert approve.status_code == 200
        assert reviewer_create.status_code == 403
        assert viewer_login.status_code == 200
        assert viewer_read.status_code == 200
        assert viewer_create.status_code == 403
    finally:
        settings_cache.cache_clear()


@pytest.mark.anyio
async def test_auth_status_is_visible_without_login(monkeypatch: pytest.MonkeyPatch, db_session: Session) -> None:
    app, settings_cache = create_auth_test_app(monkeypatch, db_session)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            response = await client.get("/api/auth/me")

        assert response.status_code == 200
        assert response.json()["auth_enabled"] is True
        assert response.json()["user"] is None
    finally:
        settings_cache.cache_clear()


@pytest.mark.anyio
async def test_auth_disabled_mode_keeps_demo_routes_open(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        create = await client.post(
            "/api/incidents",
            json={
                "title": "Demo still open",
                "description": "Auth disabled should preserve the existing demo flow",
                "source": "manual",
                "severity": "medium",
            },
        )
        demo = await client.post("/api/demo/incidents/high_api_error_rate")

    assert create.status_code == 201
    assert demo.status_code == 201


@pytest.mark.anyio
async def test_dashboard_auth_redirects_to_login(monkeypatch: pytest.MonkeyPatch, db_session: Session) -> None:
    app, settings_cache = create_auth_test_app(monkeypatch, db_session, dashboard_auth=True)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver", follow_redirects=False) as client:
            home = await client.get("/")
            login_page = await client.get("/login")

        assert home.status_code == 303
        assert home.headers["location"].startswith("/login?next=")
        assert login_page.status_code == 200
        assert "Dashboard Login" in login_page.text
    finally:
        settings_cache.cache_clear()
