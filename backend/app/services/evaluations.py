from app.agents.incident_agent import IncidentAgent
from app.evals.cases import EVAL_CASES
from app.llm.mock_provider import MockProvider
from app.schemas.evaluation import EvaluationCaseExpectation, EvaluationCaseResult, EvaluationRunSummary
from app.schemas.incident import IncidentRead
from app.schemas.timeline import TimelineItem
from app.services.agent_steps import AgentStepService
from app.services.demo import DemoService
from app.services.incidents import IncidentService
from app.services.timeline import TimelineService


class EvaluationService:
    def __init__(self, incident_service: IncidentService) -> None:
        self.incident_service = incident_service
        self.db = incident_service.db
        self.demo_service = DemoService(incident_service)
        self.timeline_service = TimelineService(self.db)
        self.agent_step_service = AgentStepService(self.db)
        self.provider = MockProvider()

    async def run_all(self) -> EvaluationRunSummary:
        results = [await self.run_case(case["scenario"]) for case in EVAL_CASES]
        passed = len([item for item in results if item.passed])
        return EvaluationRunSummary(
            total=len(results),
            passed=passed,
            failed=len(results) - passed,
            results=results,
        )

    async def run_case(self, scenario_name: str) -> EvaluationCaseResult:
        case = self._get_case(scenario_name)
        incident = self.demo_service.create_demo_incident(scenario_name)
        incident = IncidentRead.model_validate(incident)

        await IncidentAgent(self.db, provider=self.provider).run(incident.id)

        incident_after = IncidentRead.model_validate(self.incident_service.get_incident(incident.id))
        timeline = self.timeline_service.build_incident_timeline(incident.id)
        return self._evaluate_case(case, incident_after, timeline)

    def _evaluate_case(
        self,
        case: dict,
        incident: IncidentRead,
        timeline: list[TimelineItem],
    ) -> EvaluationCaseResult:
        triage_step = self._find_agent_step(timeline, "triage")
        diagnosis_step = self._find_agent_step(timeline, "diagnosis")
        actual_tools = [
            step.tool_name
            for step in self.agent_step_service.list_for_incident(incident.id)
            if step.type == "tool_call" and step.tool_name is not None
        ]
        actual_requires_approval = "approval_request" in [item.category for item in timeline]
        diagnosis_text = ""
        if diagnosis_step:
            diagnosis_details = diagnosis_step.details.get("output_json", {})
            diagnosis_text = (
                f"{diagnosis_details.get('root_cause_summary', '')} "
                f"{diagnosis_details.get('evidence_summary', '')}"
            ).strip()

        actual_severity = incident.severity.value
        if triage_step:
            actual_severity = triage_step.details.get("output_json", {}).get("severity", incident.severity.value)

        checks = {
            "severity": actual_severity == case["expected_severity"],
            "tools": actual_tools == case["expected_tools"],
            "approval": actual_requires_approval is case["expected_requires_approval"],
            "final_status": incident.status == case["expected_final_status"],
            "diagnosis_keywords": all(keyword in diagnosis_text.lower() for keyword in case["expected_diagnosis_keywords"]),
        }
        expected = EvaluationCaseExpectation.model_validate(case)
        return EvaluationCaseResult(
            scenario=case["scenario"],
            passed=all(checks.values()),
            incident_id=incident.id,
            actual_severity=actual_severity,
            actual_tools=actual_tools,
            actual_requires_approval=actual_requires_approval,
            actual_final_status=incident.status,
            diagnosis_text=diagnosis_text,
            checks=checks,
            expected=expected,
        )

    def _find_agent_step(self, timeline: list[TimelineItem], label: str) -> TimelineItem | None:
        for item in timeline:
            if item.category == "agent_step" and item.label == label:
                return item
        return None

    def _get_case(self, scenario_name: str) -> dict:
        for case in EVAL_CASES:
            if case["scenario"] == scenario_name:
                return case
        raise ValueError(f"Unknown evaluation scenario '{scenario_name}'.")
