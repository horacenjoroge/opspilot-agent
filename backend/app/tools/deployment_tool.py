from pydantic import BaseModel, Field

from app.schemas.enums import RiskLevel, ToolStatus
from app.tools.base import BaseTool, ToolResult
from app.tools.data import get_scenario_data


class DeploymentToolInput(BaseModel):
    scenario: str = Field(..., examples=["high_api_error_rate"])


class DeploymentTool(BaseTool):
    name = "deployment_tool"
    description = "Return seeded recent deployment metadata and changed files."
    risk_level = RiskLevel.safe
    input_schema = DeploymentToolInput

    async def run(self, payload: DeploymentToolInput) -> ToolResult:
        deployment = get_scenario_data(payload.scenario)["deployment"]
        return ToolResult(
            status=ToolStatus.success,
            data={"scenario": payload.scenario, "deployment": deployment},
            summary=f"Retrieved deployment context for {payload.scenario}.",
            error=None,
        )
