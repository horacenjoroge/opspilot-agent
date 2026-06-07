import pytest

from app.agents.parser import parse_diagnosis_output, parse_remediation_output, parse_triage_output
from app.llm.mock_provider import MockProvider
from tests.evals.cases import EVAL_CASES


@pytest.mark.anyio
@pytest.mark.parametrize("case", EVAL_CASES, ids=[case["scenario"] for case in EVAL_CASES])
async def test_eval_cases_are_runnable(case) -> None:
    provider = MockProvider()

    triage_payload = await provider.generate_json(
        system="triage",
        user=case["input_alert"],
        schema_name="triage",
    )
    triage = parse_triage_output(triage_payload, allowed_tools=set(case["expected_tools"]) | {"deployment_tool", "logs_tool", "metrics_tool", "health_tool", "runbook_tool"})
    assert triage.severity.value == case["expected_severity"]
    assert triage.recommended_tools == case["expected_tools"]

    diagnosis_payload = await provider.generate_json(
        system="diagnosis",
        user=case["input_alert"],
        schema_name="diagnosis",
    )
    diagnosis = parse_diagnosis_output(diagnosis_payload)
    diagnosis_text = f"{diagnosis.root_cause_summary} {diagnosis.evidence_summary}".lower()
    for keyword in case["expected_diagnosis_keywords"]:
        assert keyword in diagnosis_text

    remediation_payload = await provider.generate_json(
        system="remediation",
        user=case["input_alert"],
        schema_name="remediation",
    )
    remediation = parse_remediation_output(remediation_payload)
    assert remediation.requires_human_approval is case["expected_requires_approval"]
