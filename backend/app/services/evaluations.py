from datetime import datetime, timezone

from app.models.evaluation import EvaluationCaseResult as EvaluationCaseResultRecord
from app.models.evaluation import EvaluationRun
from app.agents.incident_agent import IncidentAgent
from app.core.config import get_settings
from app.evals.cases import EVAL_CASES
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.schemas.evaluation import (
    EvaluationCaseExpectation,
    EvaluationCaseResult,
    EvaluationHistoryItem,
    EvaluationHistoryResponse,
    EvaluationRunSummary,
)
from app.schemas.incident import IncidentRead
from app.schemas.timeline import TimelineItem
from app.services.agent_steps import AgentStepService
from app.services.demo import DemoService
from app.services.incidents import IncidentService
from app.services.timeline import TimelineService


class EvaluationService:
    def __init__(self, incident_service: IncidentService, provider: LLMProvider | None = None) -> None:
        self.incident_service = incident_service
        self.db = incident_service.db
        self.demo_service = DemoService(incident_service)
        self.timeline_service = TimelineService(self.db)
        self.agent_step_service = AgentStepService(self.db)
        settings = get_settings()
        self.provider = provider or get_llm_provider(settings)
        self.provider_name = settings.llm_provider if provider is None else provider.__class__.__name__.replace("Provider", "").lower()

    async def run_all(self) -> EvaluationRunSummary:
        started_at = datetime.now(timezone.utc)
        run_record = EvaluationRun(
            provider=self.provider_name,
            status="running",
            total_cases=len(EVAL_CASES),
            details_json={"mode": "all_cases"},
        )
        self.db.add(run_record)
        self.db.commit()
        self.db.refresh(run_record)

        try:
            results = [await self._run_case_with_persistence(case["scenario"], run_record) for case in EVAL_CASES]
            passed = len([item for item in results if item.passed])
            self._complete_run(
                run_record,
                status="completed",
                started_at=started_at,
                passed_cases=passed,
                failed_cases=len(results) - passed,
            )
            return EvaluationRunSummary(
                total=len(results),
                passed=passed,
                failed=len(results) - passed,
                results=results,
            )
        except Exception as exc:
            self._complete_run(
                run_record,
                status="failed",
                started_at=started_at,
                passed_cases=run_record.passed_cases,
                failed_cases=max(run_record.failed_cases, 1),
                details_json={
                    **(run_record.details_json or {}),
                    "error_message": str(exc),
                },
            )
            raise

    async def run_case(self, scenario_name: str) -> EvaluationCaseResult:
        started_at = datetime.now(timezone.utc)
        run_record = EvaluationRun(
            provider=self.provider_name,
            status="running",
            total_cases=1,
            details_json={"mode": "single_case", "scenario": scenario_name},
        )
        self.db.add(run_record)
        self.db.commit()
        self.db.refresh(run_record)

        try:
            result = await self._run_case_with_persistence(scenario_name, run_record)
            self._complete_run(
                run_record,
                status="completed",
                started_at=started_at,
                passed_cases=1 if result.passed else 0,
                failed_cases=0 if result.passed else 1,
            )
            return result
        except Exception as exc:
            self._complete_run(
                run_record,
                status="failed",
                started_at=started_at,
                passed_cases=run_record.passed_cases,
                failed_cases=run_record.failed_cases or 1,
                details_json={
                    **(run_record.details_json or {}),
                    "error_message": str(exc),
                },
            )
            raise

    async def _run_case_with_persistence(self, scenario_name: str, run_record: EvaluationRun) -> EvaluationCaseResult:
        try:
            case = self._get_case(scenario_name)
            incident = self.demo_service.create_demo_incident(scenario_name)
            incident = IncidentRead.model_validate(incident)

            await IncidentAgent(self.db, provider=self.provider).run(incident.id)

            incident_after = IncidentRead.model_validate(self.incident_service.get_incident(incident.id))
            timeline = self.timeline_service.build_incident_timeline(incident.id)
            result = self._evaluate_case(case, incident_after, timeline)
            self._persist_case_result(run_record, result)
            return result
        except Exception as exc:
            self._persist_case_failure(run_record, scenario_name, str(exc))
            raise

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

    def list_history(self, *, limit: int = 10, offset: int = 0) -> EvaluationHistoryResponse:
        query = self.db.query(EvaluationRun).order_by(EvaluationRun.started_at.desc(), EvaluationRun.id.desc())
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return EvaluationHistoryResponse(
            items=[
                EvaluationHistoryItem(
                    id=item.id,
                    provider=item.provider,
                    status=item.status,
                    total_cases=item.total_cases,
                    passed_cases=item.passed_cases,
                    failed_cases=item.failed_cases,
                    started_at=item.started_at,
                    completed_at=item.completed_at,
                    duration_ms=item.duration_ms,
                    details_json=item.details_json,
                )
                for item in items
            ],
            meta={"total": total, "limit": limit, "offset": offset},
        )

    def latest_run(self) -> EvaluationRun | None:
        return (
            self.db.query(EvaluationRun)
            .order_by(EvaluationRun.started_at.desc(), EvaluationRun.id.desc())
            .first()
        )

    def _persist_case_result(self, run_record: EvaluationRun, result: EvaluationCaseResult) -> None:
        case_record = EvaluationCaseResultRecord(
            evaluation_run_id=run_record.id,
            case_name=result.scenario,
            status="completed",
            passed=result.passed,
            score=100 if result.passed else 0,
            details_json=result.model_dump(mode="json"),
        )
        self.db.add(case_record)
        self.db.flush()
        if result.passed:
            run_record.passed_cases += 1
        else:
            run_record.failed_cases += 1

    def _persist_case_failure(self, run_record: EvaluationRun, scenario_name: str, error_message: str) -> None:
        case_record = EvaluationCaseResultRecord(
            evaluation_run_id=run_record.id,
            case_name=scenario_name,
            status="failed",
            passed=False,
            score=0,
            error_message=error_message,
            details_json={"scenario": scenario_name},
        )
        self.db.add(case_record)
        run_record.failed_cases += 1
        self.db.commit()

    def _complete_run(
        self,
        run_record: EvaluationRun,
        *,
        status: str,
        started_at: datetime,
        passed_cases: int,
        failed_cases: int,
        details_json: dict | None = None,
    ) -> None:
        completed_at = datetime.now(timezone.utc)
        run_record.status = status
        run_record.passed_cases = passed_cases
        run_record.failed_cases = failed_cases
        run_record.completed_at = completed_at
        run_record.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        if details_json is not None:
            run_record.details_json = details_json
        self.db.commit()
        self.db.refresh(run_record)
