from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import RiskLevel, ToolStatus
from app.services.audit import AuditService
from app.tools.base import BaseTool, ToolError, ToolResult


ACTION_RISK_LEVELS = {
    "generate_report": RiskLevel.safe,
    "send_status_update": RiskLevel.safe,
    "create_issue": RiskLevel.safe,
    "restart_api_workers_simulation": RiskLevel.dangerous,
    "rollback_deployment_simulation": RiskLevel.dangerous,
    "scale_workers_simulation": RiskLevel.medium,
}


class RemediationToolInput(BaseModel):
    incident_id: int = Field(..., examples=[1])
    action_name: str = Field(..., examples=["restart_api_workers_simulation"])
    scenario: str = Field(..., examples=["high_api_error_rate"])
    actor: str = Field(default="system", examples=["incident.commander"])
    approved: bool = Field(default=False, examples=[False])


class RemediationTool(BaseTool):
    name = "remediation_tool"
    description = "Execute or simulate approved remediation actions."
    risk_level = RiskLevel.dangerous
    input_schema = RemediationToolInput

    def __init__(self, audit_service: AuditService | None = None) -> None:
        self.audit_service = audit_service

    async def run(self, payload: RemediationToolInput) -> ToolResult:
        action_risk = ACTION_RISK_LEVELS.get(payload.action_name)
        if action_risk is None:
            return ToolResult(
                status=ToolStatus.failed,
                data={},
                summary="Rejected unknown remediation action.",
                error=ToolError(
                    code="unknown_action",
                    message="Unknown remediation action was rejected.",
                    details={"action_name": payload.action_name},
                ),
            )

        if action_risk in {RiskLevel.medium, RiskLevel.dangerous} and not payload.approved:
            self._log_action(
                actor=payload.actor,
                action="remediation.blocked",
                target_id=str(payload.incident_id),
                metadata_json={"action_name": payload.action_name, "risk_level": action_risk.value},
            )
            return ToolResult(
                status=ToolStatus.failed,
                data={"action_name": payload.action_name, "risk_level": action_risk.value, "requires_human_approval": True},
                summary=f"{payload.action_name} requires human approval before execution.",
                error=ToolError(
                    code="approval_required",
                    message="Human approval is required before running this action.",
                    details={"action_name": payload.action_name, "risk_level": action_risk.value},
                ),
            )

        result_data: dict[str, Any] = {
            "incident_id": payload.incident_id,
            "scenario": payload.scenario,
            "action_name": payload.action_name,
            "risk_level": action_risk.value,
            "simulated": True,
        }
        self._log_action(
            actor=payload.actor,
            action="remediation.executed",
            target_id=str(payload.incident_id),
            metadata_json=result_data,
        )
        return ToolResult(
            status=ToolStatus.success,
            data=result_data,
            summary=f"Executed simulated remediation action {payload.action_name}.",
            error=None,
        )

    def _log_action(self, *, actor: str, action: str, target_id: str, metadata_json: dict[str, Any]) -> None:
        if self.audit_service is None:
            return
        self.audit_service.log(
            actor=actor,
            action=action,
            target_type="incident",
            target_id=target_id,
            metadata_json=metadata_json,
        )
        self.audit_service.db.commit()
