from pydantic import BaseModel, Field

from app.schemas.enums import RiskLevel, ToolStatus
from app.tools.base import BaseTool, ToolResult
from app.tools.data import get_scenario_data


class HealthToolInput(BaseModel):
    scenario: str = Field(..., examples=["high_api_error_rate"])
    service_name: str | None = Field(default=None, examples=["api"])


class HealthTool(BaseTool):
    name = "health_tool"
    description = "Return seeded service health states."
    risk_level = RiskLevel.safe
    input_schema = HealthToolInput

    async def run(self, payload: HealthToolInput) -> ToolResult:
        health = get_scenario_data(payload.scenario)["health"]
        if payload.service_name:
            health = {payload.service_name: health.get(payload.service_name, "unknown")}
        return ToolResult(
            status=ToolStatus.success,
            data={"scenario": payload.scenario, "health": health},
            summary=f"Collected health states for {payload.scenario}.",
            error=None,
        )
