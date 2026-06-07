import os

import httpx
import pytest

from app.agents.parser import AgentOutputValidationError, parse_triage_output
from app.agents.prompts import triage_system_prompt, triage_user_prompt
from app.agents.schemas import TriageDecision
from app.llm.qwen_provider import QwenProvider
from app.services.qwen_client import QwenClient, QwenClientError


@pytest.mark.anyio
async def test_qwen_client_retries_timeout_and_returns_structured_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    client = QwenClient(
        api_key="test-key",
        model="qwen3.7-plus",
        base_url="https://example.com",
        max_retries=1,
        timeout_seconds=0.01,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(QwenClientError) as exc_info:
        await client.generate_json(system="system", user="user", schema_name="triage")

    assert exc_info.value.kind == "timeout_error"
    assert exc_info.value.to_dict()["details"]["attempt"] == 2


@pytest.mark.anyio
async def test_qwen_provider_rejects_invalid_json_content() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not-json"}}]},
        )

    provider = QwenProvider(
        QwenClient(
            api_key="test-key",
            model="qwen3.7-plus",
            base_url="https://example.com",
            transport=httpx.MockTransport(handler),
        )
    )

    with pytest.raises(QwenClientError) as exc_info:
        await provider.generate_json(system="system", user="user", schema_name="triage")

    assert exc_info.value.kind == "invalid_json"


@pytest.mark.anyio
async def test_qwen_provider_can_parse_valid_json_response() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"severity":"high","incident_type":"high_api_error_rate","recommended_tools":["logs_tool"],"reasoning_summary":"Use logs first.","requires_human_approval":false}'
                        }
                    }
                ]
            },
        )

    provider = QwenProvider(
        QwenClient(
            api_key="test-key",
            model="qwen3.7-plus",
            base_url="https://example.com",
            transport=httpx.MockTransport(handler),
        )
    )

    response = await provider.generate_json(
        system=triage_system_prompt(),
        user=triage_user_prompt(
            incident_title="API errors",
            incident_description="5xx errors are rising",
            source="alertmanager",
        ),
        schema_name="triage",
    )

    triage = parse_triage_output(response, allowed_tools={"logs_tool"})
    assert isinstance(triage, TriageDecision)
    assert triage.severity == "high"


def test_prompt_parser_rejects_missing_fields_and_unknown_tools() -> None:
    with pytest.raises(AgentOutputValidationError):
        parse_triage_output(
            {
                "severity": "high",
                "incident_type": "high_api_error_rate",
            },
            allowed_tools={"logs_tool"},
        )

    with pytest.raises(AgentOutputValidationError):
        parse_triage_output(
            {
                "severity": "high",
                "incident_type": "high_api_error_rate",
                "recommended_tools": ["shell_exec_tool"],
                "reasoning_summary": "Needs shell access.",
                "requires_human_approval": True,
            },
            allowed_tools={"logs_tool"},
        )


@pytest.mark.anyio
@pytest.mark.skipif(
    not os.getenv("QWEN_API_KEY"),
    reason="Set QWEN_API_KEY and LLM_PROVIDER=qwen to run the live Qwen smoke test.",
)
async def test_qwen_live_smoke_call() -> None:
    provider = QwenProvider(
        QwenClient(
            api_key=os.environ["QWEN_API_KEY"],
            model=os.getenv("QWEN_MODEL", "qwen3.7-plus"),
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        )
    )

    response = await provider.generate_json(
        system=triage_system_prompt(),
        user=triage_user_prompt(
            incident_title="Smoke test",
            incident_description="Ambiguous alert for live provider verification.",
            source="manual",
        ),
        schema_name="triage",
    )

    assert isinstance(response, dict)
