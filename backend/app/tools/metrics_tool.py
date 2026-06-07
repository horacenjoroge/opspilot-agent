from pydantic import BaseModel, Field

from app.schemas.enums import RiskLevel, ToolStatus
from app.tools.base import BaseTool, ToolResult
from app.tools.data import get_scenario_data


class MetricsToolInput(BaseModel):
    scenario: str = Field(..., examples=["queue_backlog"])
    metric_names: list[str] | None = Field(default=None, examples=[["queue_depth", "latency_p95_ms"]])


class MetricsTool(BaseTool):
    name = "metrics_tool"
    description = "Return seeded metrics like error rate, latency, DB connections, and queue depth."
    risk_level = RiskLevel.safe
    input_schema = MetricsToolInput

    async def run(self, payload: MetricsToolInput) -> ToolResult:
        metrics = get_scenario_data(payload.scenario)["metrics"]
        if payload.metric_names:
            metrics = {name: metrics[name] for name in payload.metric_names if name in metrics}
        return ToolResult(
            status=ToolStatus.success,
            data={"scenario": payload.scenario, "metrics": metrics},
            summary=f"Collected {len(metrics)} metrics for {payload.scenario}.",
            error=None,
        )
