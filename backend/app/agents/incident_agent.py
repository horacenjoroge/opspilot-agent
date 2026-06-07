from typing import Any

from sqlalchemy.orm import Session

from app.agents.parser import (
    AgentOutputValidationError,
    parse_diagnosis_output,
    parse_final_report_output,
    parse_remediation_output,
    parse_triage_output,
)
from app.agents.policies import evaluate_action_policy
from app.agents.prompts import (
    diagnosis_system_prompt,
    diagnosis_user_prompt,
    final_report_system_prompt,
    final_report_user_prompt,
    remediation_system_prompt,
    remediation_user_prompt,
    triage_system_prompt,
    triage_user_prompt,
)
from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.schemas.agent_step import AgentStepCreate
from app.schemas.enums import IncidentStatus, ToolStatus
from app.services.agent_steps import AgentStepService
from app.services.approvals import ApprovalService
from app.services.audit import AuditService
from app.services.incidents import IncidentService
from app.tools.registry import ToolNotFoundError, ToolRegistry


class IncidentAgent:
    def __init__(
        self,
        db: Session,
        *,
        provider: LLMProvider | None = None,
        max_steps: int = 10,
    ) -> None:
        self.db = db
        self.settings = get_settings()
        self.provider = provider or get_llm_provider(self.settings)
        self.max_steps = max_steps
        self.incident_service = IncidentService(db)
        self.agent_step_service = AgentStepService(db)
        self.approval_service = ApprovalService(db)
        self.audit_service = AuditService(db)
        self.registry = ToolRegistry(audit_service=self.audit_service)

    async def run(self, incident_id: int) -> dict[str, Any]:
        incident = self.incident_service.get_incident(incident_id)
        step_number = 0

        def next_step() -> int:
            nonlocal step_number
            step_number += 1
            if step_number > self.max_steps:
                raise MaxStepsExceededError(f"Agent exceeded max_steps={self.max_steps}.")
            return step_number

        try:
            incident = self.incident_service.update_status(incident_id, IncidentStatus.triaging)
            scenario = self._extract_scenario(incident.source, incident.description)

            triage_payload = await self.provider.generate_json(
                system=triage_system_prompt(),
                user=triage_user_prompt(
                    incident_title=incident.title,
                    incident_description=incident.description,
                    source=incident.source,
                ),
                schema_name="triage",
            )
            triage = parse_triage_output(triage_payload, allowed_tools=set(self.registry.list_tools()))
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="triage",
                output_json=triage.model_dump(mode="json"),
                model_summary=triage.reasoning_summary,
                status=ToolStatus.success,
            )

            evidence_summaries: list[str] = []
            tool_results: dict[str, Any] = {}
            for tool_name in triage.recommended_tools:
                tool_result = await self.registry.execute(tool_name, {"scenario": scenario, "query": "connection"})
                tool_results[tool_name] = tool_result.model_dump(mode="json")
                evidence_summaries.append(tool_result.summary)
                self._record_step(
                    incident_id=incident_id,
                    step_number=next_step(),
                    step_type="tool_call",
                    tool_name=tool_name,
                    input_json={"scenario": scenario, "query": "connection"},
                    output_json=tool_result.model_dump(mode="json"),
                    model_summary=tool_result.summary,
                    status=tool_result.status,
                )

            diagnosis_payload = await self.provider.generate_json(
                system=diagnosis_system_prompt(),
                user=diagnosis_user_prompt(
                    incident_context=incident.description,
                    evidence_summary="\n".join(evidence_summaries),
                ),
                schema_name="diagnosis",
            )
            diagnosis = parse_diagnosis_output(diagnosis_payload)
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="diagnosis",
                output_json=diagnosis.model_dump(mode="json"),
                model_summary=diagnosis.root_cause_summary,
                status=ToolStatus.success,
            )

            remediation_payload = await self.provider.generate_json(
                system=remediation_system_prompt(),
                user=remediation_user_prompt(
                    diagnosis_summary=diagnosis.root_cause_summary,
                    available_actions=[
                        "generate_report",
                        "send_status_update",
                        "create_issue",
                        "restart_api_workers_simulation",
                        "rollback_deployment_simulation",
                        "scale_workers_simulation",
                    ],
                ),
                schema_name="remediation",
            )
            remediation = parse_remediation_output(remediation_payload)
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="remediation_recommendation",
                output_json=remediation.model_dump(mode="json"),
                model_summary=remediation.action_summary,
                status=ToolStatus.success,
            )

            decision = evaluate_action_policy(remediation.action_name, self.settings)
            final_status = IncidentStatus.resolved
            final_report = None

            if decision.requires_approval:
                self.approval_service.create_request_from_policy(
                    incident_id=incident_id,
                    action_name=remediation.action_name,
                    reason=remediation.reason,
                    expected_impact=remediation.expected_impact,
                    rollback_plan=remediation.rollback_plan,
                    action_payload_json={
                        "incident_id": incident_id,
                        "action_name": remediation.action_name,
                        "scenario": scenario,
                    },
                )
                final_status = IncidentStatus.waiting_for_approval
            else:
                remediation_result = await self.registry.execute(
                    "remediation_tool",
                    {
                        "incident_id": incident_id,
                        "action_name": remediation.action_name,
                        "scenario": scenario,
                        "actor": "agent",
                        "approved": True,
                    },
                )
                self._record_step(
                    incident_id=incident_id,
                    step_number=next_step(),
                    step_type="remediation_execution",
                    tool_name="remediation_tool",
                    input_json={
                        "incident_id": incident_id,
                        "action_name": remediation.action_name,
                        "scenario": scenario,
                        "approved": True,
                    },
                    output_json=remediation_result.model_dump(mode="json"),
                    model_summary=remediation_result.summary,
                    status=remediation_result.status,
                )
                final_report_payload = await self.provider.generate_json(
                    system=final_report_system_prompt(),
                    user=final_report_user_prompt(
                        incident_summary=diagnosis.root_cause_summary,
                        actions_taken=["triage", *triage.recommended_tools, remediation.action_name],
                        final_status=IncidentStatus.resolved.value,
                    ),
                    schema_name="final_report",
                )
                report = parse_final_report_output(final_report_payload)
                final_report = report.summary
                self._record_step(
                    incident_id=incident_id,
                    step_number=next_step(),
                    step_type="final_report",
                    output_json=report.model_dump(mode="json"),
                    model_summary=report.summary,
                    status=ToolStatus.success,
                )

            incident = self.incident_service.update_incident_fields(
                incident_id,
                status=final_status,
                root_cause_summary=diagnosis.root_cause_summary,
                recommended_action=remediation.action_summary,
                final_report=final_report,
            )
            return {
                "incident_id": incident.id,
                "status": incident.status.value,
                "recommended_action": incident.recommended_action,
            }
        except (AgentOutputValidationError, ToolNotFoundError, MaxStepsExceededError) as exc:
            incident = self.incident_service.update_incident_fields(
                incident_id,
                status=IncidentStatus.failed,
                final_report=str(exc),
            )
            self.audit_service.log(
                actor="agent",
                action="agent.failed",
                target_type="incident",
                target_id=str(incident.id),
                metadata_json={"error": str(exc)},
            )
            self.db.commit()
            return {"incident_id": incident.id, "status": incident.status.value, "error": str(exc)}

    def _record_step(
        self,
        *,
        incident_id: int,
        step_number: int,
        step_type: str,
        status: ToolStatus,
        tool_name: str | None = None,
        input_json: dict | None = None,
        output_json: dict | None = None,
        model_summary: str | None = None,
    ) -> None:
        self.agent_step_service.create_step(
            AgentStepCreate(
                incident_id=incident_id,
                step_number=step_number,
                type=step_type,
                tool_name=tool_name,
                input_json=input_json,
                output_json=output_json,
                model_summary=model_summary,
                status=status,
            )
        )

    def _extract_scenario(self, source: str, description: str) -> str:
        if source.startswith("demo:"):
            return source.split("demo:", 1)[1]
        normalized = f"{source} {description}".lower()
        if "queue" in normalized and "backlog" in normalized:
            return "queue_backlog"
        if "database latency" in normalized or "db latency" in normalized:
            return "database_latency"
        if "tool failure" in normalized:
            return "tool_failure"
        if "api error" in normalized or "5xx" in normalized or "error rate" in normalized:
            return "high_api_error_rate"
        return "ambiguous_alert"


class MaxStepsExceededError(ValueError):
    pass
