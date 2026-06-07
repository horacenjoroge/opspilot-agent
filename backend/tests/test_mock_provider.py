import pytest

from app.core.config import Settings
from app.llm.factory import get_llm_provider
from app.llm.mock_provider import MockProvider


@pytest.mark.anyio
async def test_mock_provider_returns_expected_tools_for_high_api_error_rate() -> None:
    provider = MockProvider()

    response = await provider.generate_json(
        system="triage",
        user="Production alert: API error rate is spiking with sustained 5xx responses.",
        schema_name="triage",
    )

    assert response["incident_type"] == "high_api_error_rate"
    assert response["recommended_tools"] == [
        "logs_tool",
        "metrics_tool",
        "health_tool",
        "deployment_tool",
        "runbook_tool",
    ]


@pytest.mark.anyio
async def test_mock_provider_returns_queue_backlog_and_ambiguous_scenarios() -> None:
    provider = MockProvider()

    queue_response = await provider.generate_json(
        system="triage",
        user="There is a queue backlog building in the background workers.",
        schema_name="triage",
    )
    ambiguous_response = await provider.generate_json(
        system="triage",
        user="This is an ambiguous alert with partial evidence only.",
        schema_name="triage",
    )

    assert queue_response["recommended_tools"] == ["metrics_tool", "health_tool", "runbook_tool"]
    assert ambiguous_response["recommended_tools"] == ["logs_tool", "metrics_tool", "health_tool", "runbook_tool"]


def test_factory_uses_mock_provider_by_default() -> None:
    provider = get_llm_provider(Settings())

    assert isinstance(provider, MockProvider)
