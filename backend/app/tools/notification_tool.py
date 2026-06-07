from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import RiskLevel, ToolStatus
from app.services.audit import AuditService
from app.tools.base import BaseTool, ToolResult


class NotificationToolInput(BaseModel):
    incident_id: int = Field(..., examples=[1])
    action_name: str = Field(..., examples=["send_status_update"])
    channel: str = Field(..., examples=["slack"])
    message: str = Field(..., examples=["Investigating API error spike."])
    actor: str = Field(default="system", examples=["incident.commander"])


class NotificationTool(BaseTool):
    name = "notification_tool"
    description = "Simulate Slack, email, or status-page updates."
    risk_level = RiskLevel.safe
    input_schema = NotificationToolInput

    def __init__(self, audit_service: AuditService | None = None) -> None:
        self.audit_service = audit_service

    async def run(self, payload: NotificationToolInput) -> ToolResult:
        result_data: dict[str, Any] = {
            "incident_id": payload.incident_id,
            "action_name": payload.action_name,
            "channel": payload.channel,
            "message": payload.message,
            "simulated": True,
        }
        if self.audit_service is not None:
            self.audit_service.log(
                actor=payload.actor,
                action="notification.sent",
                target_type="incident",
                target_id=str(payload.incident_id),
                metadata_json=result_data,
            )
            self.audit_service.db.commit()
        return ToolResult(
            status=ToolStatus.success,
            data=result_data,
            summary=f"Simulated notification via {payload.channel}.",
            error=None,
        )
