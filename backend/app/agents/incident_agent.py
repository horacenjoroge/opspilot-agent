import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger("opspilot.agent")

from app.agents.parser import (
    AgentOutputValidationError,
    parse_diagnosis_output,
    parse_final_report_output,
    parse_remediation_output,
    parse_tool_selection_output,
    parse_triage_output,
)
from app.agents.schemas import DiagnosisDecision, FinalReportDecision, RemediationDecision, TriageDecision
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
from app.services.qwen_client import QwenClientError
from app.schemas.agent_step import AgentStepCreate
from app.schemas.enums import IncidentStatus, RiskLevel, ToolStatus
from app.services.agent_steps import AgentStepService
from app.services.approvals import ApprovalService
from app.services.audit import AuditService
from app.services.incident_memory import IncidentMemoryService
from app.services.incidents import IncidentService
from app.tools.registry import ToolNotFoundError, ToolRegistry


class IncidentAgent:
    def __init__(
        self,
        db: Session,
        *,
        provider: LLMProvider | None = None,
        max_steps: int = 20,
    ) -> None:
        self.db = db
        self.settings = get_settings()
        self.provider = provider or get_llm_provider(self.settings)
        self.max_steps = max_steps
        self.incident_service = IncidentService(db)
        self.agent_step_service = AgentStepService(db)
        self.approval_service = ApprovalService(db)
        self.audit_service = AuditService(db)
        self.memory_service = IncidentMemoryService(db)
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

            triage, triage_status = await self._generate_triage(
                incident_title=incident.title,
                incident_description=incident.description,
                source=incident.source,
            )
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="triage",
                title=f"Triage — {triage.incident_type} ({triage.severity})",
                output_json=triage.model_dump(mode="json"),
                model_summary=triage.reasoning_summary,
                status=triage_status,
            )

            tool_selection = parse_tool_selection_output(
                {
                    "incident_type": triage.incident_type,
                    "selected_tools": triage.recommended_tools,
                    "selection_summary": f"Validated {len(triage.recommended_tools)} tool selections against the backend allowlist.",
                }
            )
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="tool_selection",
                title=f"Tool Selection — {len(triage.recommended_tools)} tools approved",
                output_json=tool_selection.model_dump(mode="json"),
                model_summary=tool_selection.selection_summary,
                status=ToolStatus.success,
            )

            similar_memories = self.memory_service.find_similar(
                incident_type=triage.incident_type,
                symptoms=incident.description,
                exclude_incident_id=incident_id,
            )
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="memory_lookup",
                title=f"Memory Lookup — {len(similar_memories)} similar incident{'s' if len(similar_memories) != 1 else ''} found",
                output_json={"memories": self.memory_service.memories_for_timeline(similar_memories)},
                model_summary=(
                    f"Loaded {len(similar_memories)} similar incident memories for diagnosis context."
                    if similar_memories
                    else "No similar incident memories were found."
                ),
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
                    title=f"Tool Call — {tool_name}",
                    tool_name=tool_name,
                    input_json={"scenario": scenario, "query": "connection"},
                    output_json=tool_result.model_dump(mode="json"),
                    model_summary=tool_result.summary,
                    status=tool_result.status,
                )

            diagnosis, diagnosis_status = await self._generate_diagnosis(
                incident_context=incident.description,
                evidence_summary="\n".join(evidence_summaries),
                memory_context=self.memory_service.memories_for_prompt(similar_memories),
            )
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="diagnosis",
                title=f"Diagnosis — {diagnosis.confidence} confidence",
                output_json=diagnosis.model_dump(mode="json"),
                model_summary=diagnosis.root_cause_summary,
                status=diagnosis_status,
            )

            available_actions = [
                "generate_report",
                "send_status_update",
                "create_issue",
                "restart_api_workers_simulation",
                "rollback_deployment_simulation",
                "scale_workers_simulation",
                "clear_queue_simulation",
                "disable_feature_flag_simulation",
            ]
            remediation, remediation_status = await self._generate_remediation(
                diagnosis_summary=diagnosis.root_cause_summary,
                available_actions=available_actions,
            )
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="remediation_recommendation",
                title=f"Remediation — recommend {remediation.action_name} ({remediation.risk_level.value})",
                output_json=remediation.model_dump(mode="json"),
                model_summary=remediation.action_summary,
                status=remediation_status,
            )

            decision = evaluate_action_policy(remediation.action_name, self.settings)
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="policy_decision",
                title=f"Policy Decision — {decision.action_name} is {decision.risk_level.value}{', approval required' if decision.requires_approval else ', auto-approved'}",
                output_json={
                    "action_name": decision.action_name,
                    "risk_level": decision.risk_level.value,
                    "requires_approval": decision.requires_approval,
                },
                model_summary=(
                    f"Backend policy classified {decision.action_name} as {decision.risk_level.value} "
                    f"and requires approval={decision.requires_approval}."
                ),
                status=ToolStatus.success,
            )
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
                    title=f"Execution — {remediation.action_name}",
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
            report, report_status = await self._generate_final_report(
                incident_summary=diagnosis.root_cause_summary,
                actions_taken=[
                    "triage",
                    "tool_selection",
                    *triage.recommended_tools,
                    remediation.action_name,
                ],
                final_status=final_status,
            )
            final_report = report.summary
            self._record_step(
                incident_id=incident_id,
                step_number=next_step(),
                step_type="final_report",
                title=f"Final Report — {final_status.value}",
                output_json=report.model_dump(mode="json"),
                model_summary=report.summary,
                status=report_status,
            )

            incident = self.incident_service.update_incident_fields(
                incident_id,
                status=final_status,
                root_cause_summary=diagnosis.root_cause_summary,
                recommended_action=remediation.action_summary,
                final_report=final_report,
            )
            if final_status == IncidentStatus.resolved:
                self.memory_service.create_or_update_from_incident(
                    incident_id,
                    incident_type=triage.incident_type,
                    confidence=diagnosis.confidence,
                    successful_fix=remediation.action_name,
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

    async def _generate_triage(
        self,
        *,
        incident_title: str,
        incident_description: str,
        source: str,
    ) -> tuple[TriageDecision, ToolStatus]:
        try:
            payload = await self.provider.generate_json(
                system=triage_system_prompt(),
                user=triage_user_prompt(
                    incident_title=incident_title,
                    incident_description=incident_description,
                    source=source,
                    allowed_tools=self.registry.list_tools(),
                ),
                schema_name="triage",
            )
            triage = parse_triage_output(payload, allowed_tools=set(self.registry.list_tools()))
            return triage, ToolStatus.success
        except QwenClientError as exc:
            logger.error("Qwen triage call failed: %s — %s", exc.kind, exc.message)
            return self._fallback_triage(), ToolStatus.failed
        except AgentOutputValidationError as exc:
            if "Unknown tools recommended by model" in str(exc):
                raise
            logger.error("Triage output validation failed: %s", exc)
            return self._fallback_triage(), ToolStatus.failed

    async def _generate_diagnosis(
        self,
        *,
        incident_context: str,
        evidence_summary: str,
        memory_context: str,
    ) -> tuple[DiagnosisDecision, ToolStatus]:
        try:
            payload = await self.provider.generate_json(
                system=diagnosis_system_prompt(),
                user=diagnosis_user_prompt(
                    incident_context=incident_context,
                    evidence_summary=evidence_summary,
                    memory_context=memory_context,
                ),
                schema_name="diagnosis",
            )
            return parse_diagnosis_output(payload), ToolStatus.success
        except (QwenClientError, AgentOutputValidationError) as exc:
            logger.error("Qwen diagnosis call failed: %s", exc)
            return self._fallback_diagnosis(evidence_summary), ToolStatus.failed

    async def _generate_remediation(
        self,
        *,
        diagnosis_summary: str,
        available_actions: list[str],
    ) -> tuple[RemediationDecision, ToolStatus]:
        try:
            payload = await self.provider.generate_json(
                system=remediation_system_prompt(),
                user=remediation_user_prompt(
                    diagnosis_summary=diagnosis_summary,
                    available_actions=available_actions,
                ),
                schema_name="remediation",
            )
            return parse_remediation_output(payload), ToolStatus.success
        except (QwenClientError, AgentOutputValidationError) as exc:
            logger.error("Qwen remediation call failed: %s", exc)
            return self._fallback_remediation(), ToolStatus.failed

    async def _generate_final_report(
        self,
        *,
        incident_summary: str,
        actions_taken: list[str],
        final_status: IncidentStatus,
    ) -> tuple[FinalReportDecision, ToolStatus]:
        try:
            payload = await self.provider.generate_json(
                system=final_report_system_prompt(),
                user=final_report_user_prompt(
                    incident_summary=incident_summary,
                    actions_taken=actions_taken,
                    final_status=final_status.value,
                ),
                schema_name="final_report",
            )
            return parse_final_report_output(payload), ToolStatus.success
        except (QwenClientError, AgentOutputValidationError) as exc:
            logger.error("Qwen final report call failed: %s", exc)
            return self._fallback_final_report(incident_summary, actions_taken, final_status), ToolStatus.failed

    def _fallback_triage(self) -> TriageDecision:
        return TriageDecision(
            severity="medium",
            incident_type="fallback_investigation",
            recommended_tools=["logs_tool", "metrics_tool", "health_tool", "runbook_tool"],
            reasoning_summary="Fallback triage activated because model output was unavailable or invalid. Use broad read-only investigation tools.",
            requires_human_approval=False,
        )

    def _fallback_diagnosis(self, evidence_summary: str) -> DiagnosisDecision:
        summary = evidence_summary or "Evidence is limited because model diagnosis was unavailable."
        return DiagnosisDecision(
            root_cause_summary="Fallback diagnosis: collected evidence should be reviewed manually because model diagnosis was unavailable.",
            evidence_summary=summary,
            confidence="low",
        )

    def _fallback_remediation(self) -> RemediationDecision:
        return RemediationDecision(
            action_name="generate_report",
            action_summary="Generate a structured incident report and hand off for manual review.",
            risk_level=RiskLevel.safe,
            requires_human_approval=False,
            reason="Fallback remediation avoids risky actions when model guidance is unavailable.",
            expected_impact="Preserves investigation evidence without changing infrastructure state.",
            rollback_plan="No rollback is required for report generation.",
        )

    def _fallback_final_report(
        self,
        incident_summary: str,
        actions_taken: list[str],
        final_status: IncidentStatus,
    ) -> FinalReportDecision:
        return FinalReportDecision(
            summary=(
                "Fallback final report: OpsPilot completed a safe degraded workflow because model output was unavailable. "
                f"Incident summary: {incident_summary}"
            ),
            incident_status=final_status,
            actions_taken=actions_taken,
            follow_up_items=[
                "Review the provider failure or invalid model payload.",
                "Confirm the diagnosis manually before any further risky remediation.",
            ],
        )

    def _record_step(
        self,
        *,
        incident_id: int,
        step_number: int,
        step_type: str,
        status: ToolStatus,
        title: str | None = None,
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
                title=title,
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
