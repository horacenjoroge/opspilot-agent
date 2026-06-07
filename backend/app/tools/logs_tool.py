from pydantic import BaseModel, Field

from app.schemas.enums import RiskLevel, ToolStatus
from app.tools.base import BaseTool, ToolExecutionError, ToolResult
from app.tools.data import get_scenario_data


class LogsToolInput(BaseModel):
    scenario: str = Field(..., examples=["high_api_error_rate"])
    query: str = Field(default="errors", examples=["database connection errors"])


class LogsTool(BaseTool):
    name = "logs_tool"
    description = "Read seeded logs and return relevant incident errors."
    risk_level = RiskLevel.safe
    input_schema = LogsToolInput

    async def run(self, payload: LogsToolInput) -> ToolResult:
        scenario_data = get_scenario_data(payload.scenario)
        if payload.scenario == "tool_failure":
            raise ToolExecutionError(
                code="tool_unavailable",
                message="The log index is unavailable for this incident window.",
                details={"scenario": payload.scenario},
            )

        matching_logs = [line for line in scenario_data["logs"] if payload.query.lower() in line.lower()]
        if not matching_logs:
            matching_logs = scenario_data["logs"]
        return ToolResult(
            status=ToolStatus.success,
            data={"scenario": payload.scenario, "logs": matching_logs},
            summary=f"Retrieved {len(matching_logs)} log lines for {payload.scenario}.",
            error=None,
        )
