import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app


@pytest.mark.anyio
async def test_health_endpoint_returns_service_status() -> None:
    get_settings.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "opspilot",
        "llm_provider": "mock",
    }


@pytest.mark.anyio
async def test_ready_endpoint_returns_readiness_checks(app_with_test_db) -> None:
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.get("/ready")

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "ready"
    assert payload["service"] == "opspilot"
    assert payload["llm_provider"] == "mock"
    assert "timestamp" in payload
    assert payload["checks"] == {
        "database": {"ok": True, "detail": "Database connection succeeded."},
        "provider": {"ok": True, "detail": "Mock provider is configured for local/demo readiness."},
    }


@pytest.mark.anyio
async def test_ready_endpoint_returns_503_for_incomplete_qwen_configuration(app_with_test_db, monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("QWEN_API_KEY", "")
    monkeypatch.setenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    get_settings.cache_clear()
    try:
        async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
            response = await client.get("/ready")

        payload = response.json()
        assert response.status_code == 503
        assert payload["status"] == "not_ready"
        assert payload["llm_provider"] == "qwen"
        assert payload["checks"]["database"] == {"ok": True, "detail": "Database connection succeeded."}
        assert payload["checks"]["provider"] == {
            "ok": False,
            "detail": "Missing required Qwen configuration: QWEN_API_KEY.",
        }
    finally:
        get_settings.cache_clear()
