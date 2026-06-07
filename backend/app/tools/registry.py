from app.services.audit import AuditService
from app.tools.base import BaseTool, ToolResult
from app.tools.deployment_tool import DeploymentTool
from app.tools.health_tool import HealthTool
from app.tools.logs_tool import LogsTool
from app.tools.metrics_tool import MetricsTool
from app.tools.notification_tool import NotificationTool
from app.tools.remediation_tool import RemediationTool
from app.tools.runbook_tool import RunbookTool


class ToolNotFoundError(ValueError):
    pass


class ToolRegistry:
    def __init__(self, audit_service: AuditService | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_defaults(audit_service)

    def _register_defaults(self, audit_service: AuditService | None) -> None:
        for tool in [
            LogsTool(),
            MetricsTool(),
            HealthTool(),
            DeploymentTool(),
            RunbookTool(),
            RemediationTool(audit_service=audit_service),
            NotificationTool(audit_service=audit_service),
        ]:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Unknown tool '{name}' was rejected by the allowlist.")
        return tool

    def list_tools(self) -> list[str]:
        return sorted(self._tools)

    async def execute(self, name: str, payload: dict) -> ToolResult:
        tool = self.get_tool(name)
        return await tool.execute(payload)
