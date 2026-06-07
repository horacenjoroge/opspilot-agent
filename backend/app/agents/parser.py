from pydantic import ValidationError

from app.agents.schemas import DiagnosisDecision, FinalReportDecision, RemediationDecision, ToolSelectionDecision, TriageDecision


class AgentOutputValidationError(ValueError):
    pass


def parse_triage_output(payload: dict, *, allowed_tools: set[str]) -> TriageDecision:
    triage = _validate_payload(TriageDecision, payload, "triage")
    unknown_tools = sorted(set(triage.recommended_tools) - allowed_tools)
    if unknown_tools:
        raise AgentOutputValidationError(f"Unknown tools recommended by model: {', '.join(unknown_tools)}")
    return triage


def parse_diagnosis_output(payload: dict) -> DiagnosisDecision:
    return _validate_payload(DiagnosisDecision, payload, "diagnosis")


def parse_tool_selection_output(payload: dict) -> ToolSelectionDecision:
    return _validate_payload(ToolSelectionDecision, payload, "tool_selection")


def parse_remediation_output(payload: dict) -> RemediationDecision:
    return _validate_payload(RemediationDecision, payload, "remediation")


def parse_final_report_output(payload: dict) -> FinalReportDecision:
    return _validate_payload(FinalReportDecision, payload, "final_report")


def _validate_payload(schema, payload: dict, schema_name: str):
    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise AgentOutputValidationError(f"Invalid {schema_name} payload: {exc}") from exc
