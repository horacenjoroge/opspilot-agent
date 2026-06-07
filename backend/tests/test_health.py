from httpx import ASGITransport, AsyncClient
import pytest

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
