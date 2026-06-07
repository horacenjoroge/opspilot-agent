from typing import Any

from app.llm.base import LLMProvider
from app.schemas.enums import RiskLevel, Severity


class MockProvider(LLMProvider):
    async def generate_json(self, *, system: str, user: str, schema_name: str) -> dict[str, Any]:
        scenario = self._detect_scenario(user)

        if schema_name == "triage":
            return self._triage_response(scenario)
        if schema_name == "diagnosis":
            return self._diagnosis_response(scenario)
        if schema_name == "remediation":
            return self._remediation_response(scenario)
        if schema_name == "final_report":
            return self._final_report_response(scenario)
        raise ValueError(f"Unsupported mock schema: {schema_name}")

    def _detect_scenario(self, text: str) -> str:
        normalized = text.lower().replace("_", " ")
        if "queue" in normalized and "backlog" in normalized:
            return "queue_backlog"
        if "database latency" in normalized or "db latency" in normalized:
            return "database_latency"
        if "tool failure" in normalized or "log index" in normalized or "dependency may fail" in normalized:
            return "tool_failure"
        if "api error" in normalized or "5xx" in normalized or "error rate" in normalized:
            return "high_api_error_rate"
        if "ambiguous" in normalized:
            return "ambiguous_alert"
        return "ambiguous_alert"

    def _triage_response(self, scenario: str) -> dict[str, Any]:
        if scenario == "queue_backlog":
            return {
                "severity": Severity.high.value,
                "incident_type": scenario,
                "recommended_tools": ["metrics_tool", "health_tool", "runbook_tool"],
                "reasoning_summary": "Queue depth and worker health need inspection before any action.",
                "requires_human_approval": False,
            }
        if scenario == "database_latency":
            return {
                "severity": Severity.high.value,
                "incident_type": scenario,
                "recommended_tools": ["metrics_tool", "logs_tool", "runbook_tool"],
                "reasoning_summary": "Database latency alerts need metrics, logs, and runbook guidance.",
                "requires_human_approval": False,
            }
        if scenario == "tool_failure":
            return {
                "severity": Severity.medium.value,
                "incident_type": scenario,
                "recommended_tools": ["logs_tool", "health_tool"],
                "reasoning_summary": "Start with logs and health because one investigation dependency may fail.",
                "requires_human_approval": False,
            }
        if scenario == "high_api_error_rate":
            return {
                "severity": Severity.high.value,
                "incident_type": scenario,
                "recommended_tools": [
                    "logs_tool",
                    "metrics_tool",
                    "health_tool",
                    "deployment_tool",
                    "runbook_tool",
                ],
                "reasoning_summary": "Elevated API errors require logs, metrics, health, deployment, and runbook evidence.",
                "requires_human_approval": False,
            }
        return {
            "severity": Severity.medium.value,
            "incident_type": "ambiguous_alert",
            "recommended_tools": ["logs_tool", "metrics_tool", "health_tool", "runbook_tool"],
            "reasoning_summary": "Use broad read-only investigation tools when the alert is ambiguous.",
            "requires_human_approval": False,
        }

    def _diagnosis_response(self, scenario: str) -> dict[str, Any]:
        mapping = {
            "high_api_error_rate": {
                "root_cause_summary": "The API error spike is consistent with database connection exhaustion in the application pool.",
                "evidence_summary": "Logs show connection limit errors while metrics show elevated 5xx responses and degraded health.",
                "confidence": "high",
            },
            "queue_backlog": {
                "root_cause_summary": "The queue backlog indicates workers are saturated and falling behind incoming job volume.",
                "evidence_summary": "Queue depth is growing while worker health remains degraded.",
                "confidence": "high",
            },
            "database_latency": {
                "root_cause_summary": "Database latency is spiking due to slow queries and rising connection pressure.",
                "evidence_summary": "Latency metrics increased alongside database wait indicators.",
                "confidence": "medium",
            },
            "tool_failure": {
                "root_cause_summary": "The investigation is incomplete because one tool failed during evidence gathering.",
                "evidence_summary": "Available health and log signals are mixed and require fallback handling.",
                "confidence": "low",
            },
        }
        return mapping.get(
            scenario,
            {
                "root_cause_summary": "The alert signal is ambiguous and needs broader investigation.",
                "evidence_summary": "Current evidence is inconclusive, so the safest path is read-only investigation.",
                "confidence": "low",
            },
        )

    def _remediation_response(self, scenario: str) -> dict[str, Any]:
        if scenario == "high_api_error_rate":
            return {
                "action_name": "restart_api_workers_simulation",
                "action_summary": "Restart API workers after validating the database pool is stable.",
                "risk_level": RiskLevel.dangerous.value,
                "requires_human_approval": True,
                "reason": "Restarting workers may clear exhausted DB connections but affects live traffic.",
                "expected_impact": "Short-lived request disruption while workers recycle.",
                "rollback_plan": "Cancel restart and revert to previous worker deployment settings if errors worsen.",
            }
        if scenario == "queue_backlog":
            return {
                "action_name": "scale_workers_simulation",
                "action_summary": "Scale worker capacity to drain the backlog.",
                "risk_level": RiskLevel.medium.value,
                "requires_human_approval": True,
                "reason": "Increasing worker count changes runtime capacity and should be reviewed.",
                "expected_impact": "Faster backlog reduction with a temporary infrastructure cost increase.",
                "rollback_plan": "Scale down to the previous worker count if throughput or stability worsens.",
            }
        if scenario == "database_latency":
            return {
                "action_name": "generate_report",
                "action_summary": "Create a report and escalate for DBA review.",
                "risk_level": RiskLevel.safe.value,
                "requires_human_approval": False,
                "reason": "The safest MVP action is to document evidence before making DB changes.",
                "expected_impact": "Captures the issue clearly for follow-up remediation.",
                "rollback_plan": "No rollback is needed for reporting actions.",
            }
        return {
            "action_name": "generate_report",
            "action_summary": "Generate a report with the current evidence and request manual follow-up.",
            "risk_level": RiskLevel.safe.value,
            "requires_human_approval": False,
            "reason": "Ambiguous or partial evidence should not trigger risky remediation.",
            "expected_impact": "Preserves findings without changing infrastructure state.",
            "rollback_plan": "No rollback is needed for reporting actions.",
        }

    def _final_report_response(self, scenario: str) -> dict[str, Any]:
        return {
            "summary": f"OpsPilot completed the {scenario} investigation with structured evidence and a remediation recommendation.",
            "incident_status": "resolved" if scenario == "database_latency" else "waiting_for_approval",
            "actions_taken": ["triage", "evidence_collection", "recommendation"],
            "follow_up_items": ["Review capacity guardrails", "Update the incident runbook"],
        }
