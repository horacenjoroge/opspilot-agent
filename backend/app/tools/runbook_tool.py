from pydantic import BaseModel, Field

from app.schemas.enums import RiskLevel, ToolStatus
from app.tools.base import BaseTool, ToolResult
from app.tools.data import get_scenario_data


class RunbookToolInput(BaseModel):
    scenario: str = Field(..., examples=["database_latency"])


class RunbookTool(BaseTool):
    name = "runbook_tool"
    description = "Retrieve seeded markdown runbook guidance."
    risk_level = RiskLevel.safe
    input_schema = RunbookToolInput

    async def run(self, payload: RunbookToolInput) -> ToolResult:
        runbook = get_scenario_data(payload.scenario)["runbook"]
        return ToolResult(
            status=ToolStatus.success,
            data={"scenario": payload.scenario, "runbook": runbook},
            summary=f"Loaded runbook guidance for {payload.scenario}.",
            error=None,
        )
