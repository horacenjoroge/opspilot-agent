from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.enums import IncidentStatus, RiskLevel, Severity


class TriageDecision(BaseModel):
    severity: Severity = Field(..., examples=["high"])
    incident_type: str = Field(..., examples=["high_api_error_rate"])
    recommended_tools: list[str] = Field(
        ...,
        examples=[["logs_tool", "metrics_tool", "health_tool", "deployment_tool", "runbook_tool"]],
    )
    reasoning_summary: str = Field(
        ...,
        examples=["The alert indicates elevated API errors and requires logs, metrics, health, deployment, and runbook evidence."],
    )
    requires_human_approval: bool = Field(..., examples=[False])


class ToolSelectionDecision(BaseModel):
    incident_type: str = Field(..., examples=["high_api_error_rate"])
    selected_tools: list[str] = Field(
        ...,
        examples=[["logs_tool", "metrics_tool", "health_tool", "deployment_tool", "runbook_tool"]],
    )
    selection_summary: str = Field(
        ...,
        examples=["Validated the evidence-gathering tool plan before backend execution."],
    )


class DiagnosisDecision(BaseModel):
    root_cause_summary: str = Field(..., examples=["Database connections were exhausted in the application pool."])
    evidence_summary: str = Field(..., examples=["Logs and metrics both point to connection exhaustion and degraded API health."])
    confidence: Literal["low", "medium", "high"] = Field(..., examples=["high"])


class RemediationDecision(BaseModel):
    action_name: str = Field(..., examples=["restart_api_workers_simulation"])
    action_summary: str = Field(..., examples=["Restart API workers after validating the database pool is stable."])
    risk_level: RiskLevel = Field(..., examples=["dangerous"])
    requires_human_approval: bool = Field(..., examples=[True])
    reason: str = Field(..., examples=["Restarting workers may clear exhausted DB connections but affects live traffic."])
    expected_impact: str = Field(..., examples=["Short-lived request disruption while workers recycle."])
    rollback_plan: str = Field(..., examples=["Cancel restart and revert to prior worker deployment settings if errors worsen."])


class FinalReportDecision(BaseModel):
    summary: str = Field(..., examples=["OpsPilot completed the investigation and produced a recommended remediation path."])
    incident_status: IncidentStatus = Field(..., examples=["waiting_for_approval"])
    actions_taken: list[str] = Field(..., examples=[["triage", "evidence_collection", "recommendation"]])
    follow_up_items: list[str] = Field(..., examples=[["Review pool limits", "Update runbook notes"]])
