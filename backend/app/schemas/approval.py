from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ApprovalStatus, RiskLevel


class ApprovalRequestCreate(BaseModel):
    incident_id: int = Field(..., examples=[1])
    action_name: str = Field(..., examples=["restart_api_workers_simulation"])
    risk_level: RiskLevel = Field(..., examples=["dangerous"])
    reason: str = Field(..., examples=["API workers are failing due to exhausted DB connections."])
    expected_impact: str = Field(..., examples=["May briefly interrupt in-flight requests while workers restart."])
    rollback_plan: str = Field(..., examples=["Redeploy prior worker image and disable restart automation."])
    action_payload_json: dict | None = Field(
        default=None,
        examples=[[{"incident_id": 1, "action_name": "restart_api_workers_simulation", "scenario": "high_api_error_rate"}]],
    )


class ApprovalDecision(BaseModel):
    approved_by: str = Field(..., examples=["oncall.engineer"])


class ApprovalRequestRead(ApprovalRequestCreate):
    id: int = Field(..., examples=[1])
    status: ApprovalStatus = Field(..., examples=["pending"])
    requested_at: datetime
    approved_by: str | None = Field(default=None, examples=["oncall.engineer"])
    approved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
