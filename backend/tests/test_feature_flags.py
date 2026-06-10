import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app


@pytest.mark.anyio
async def test_demo_routes_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_DEMO_ROUTES", "false")
    get_settings.cache_clear()
    app = create_app()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            response = await client.post("/api/demo/incidents/high_api_error_rate")

        assert response.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_eval_routes_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_EVAL_ROUTES", "false")
    get_settings.cache_clear()
    app = create_app()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            response = await client.post("/api/evals/run")

        assert response.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_dashboard_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_DASHBOARD", "false")
    get_settings.cache_clear()
    app = create_app()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            home = await client.get("/")
            incidents = await client.get("/incidents")
            approvals = await client.get("/approvals")
            demo = await client.get("/demo")
            evals = await client.get("/evals")

        assert home.status_code == 404
        assert incidents.status_code == 404
        assert approvals.status_code == 404
        assert demo.status_code == 404
        assert evals.status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_feature_flags_default_to_demo_friendly(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        demo = await client.post("/api/demo/incidents/high_api_error_rate")
        evals = await client.post("/api/evals/run")
        dashboard = await client.get("/")

    assert demo.status_code == 201
    assert evals.status_code == 200
    assert dashboard.status_code == 200
