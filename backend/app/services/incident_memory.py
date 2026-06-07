import re
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.incident_memory import IncidentMemory
from app.schemas.agent_step import AgentStepCreate
from app.schemas.incident_memory import IncidentMemoryRead
from app.schemas.enums import ToolStatus
from app.services.agent_steps import AgentStepService
from app.services.audit import AuditService
from app.services.incidents import IncidentService


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "while",
    "with",
}


@dataclass(frozen=True)
class SimilarIncidentMemory:
    memory: IncidentMemory
    score: int


class IncidentMemoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.incident_service = IncidentService(db)
        self.agent_step_service = AgentStepService(db)
        self.audit_service = AuditService(db)

    def create_or_update_from_incident(
        self,
        incident_id: int,
        *,
        incident_type: str | None = None,
        confidence: str | None = None,
        successful_fix: str | None = None,
        failed_fix: str | None = None,
    ) -> IncidentMemory:
        incident = self.incident_service.get_incident(incident_id)
        steps = self.agent_step_service.list_for_incident(incident_id)

        resolved_incident_type = incident_type or self._extract_incident_type(steps) or incident.source.replace("demo:", "")
        resolved_confidence = confidence or self._extract_confidence(steps) or "medium"
        resolved_successful_fix = successful_fix or self._extract_successful_fix(incident_id, steps) or incident.recommended_action
        tools_used = self._extract_tools_used(steps)
        root_cause = incident.root_cause_summary or incident.final_report or incident.description

        memory = (
            self.db.query(IncidentMemory)
            .filter(IncidentMemory.incident_id == incident_id)
            .one_or_none()
        )

        if memory is None:
            memory = IncidentMemory(
                incident_id=incident_id,
                incident_type=resolved_incident_type,
                symptoms=incident.description,
                tools_used=tools_used,
                root_cause=root_cause,
                successful_fix=resolved_successful_fix,
                failed_fix=failed_fix,
                confidence=resolved_confidence,
            )
            self.db.add(memory)
        else:
            memory.incident_type = resolved_incident_type
            memory.symptoms = incident.description
            memory.tools_used = tools_used
            memory.root_cause = root_cause
            memory.successful_fix = resolved_successful_fix
            memory.failed_fix = failed_fix
            memory.confidence = resolved_confidence

        self.db.flush()
        self.audit_service.log(
            actor="system",
            action="memory.saved",
            target_type="incident",
            target_id=str(incident_id),
            metadata_json={
                "memory_id": memory.id,
                "incident_type": memory.incident_type,
                "confidence": memory.confidence,
            },
        )
        self.agent_step_service.create_step(
            AgentStepCreate(
                incident_id=incident_id,
                step_number=self.agent_step_service.next_step_number(incident_id),
                type="memory_saved",
                output_json={
                    "memory_id": memory.id,
                    "incident_type": memory.incident_type,
                    "confidence": memory.confidence,
                    "successful_fix": memory.successful_fix,
                    "failed_fix": memory.failed_fix,
                },
                model_summary=f"Saved reusable incident memory for incident type '{memory.incident_type}'.",
                status=ToolStatus.success,
            )
        )
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def find_similar(
        self,
        *,
        incident_type: str | None,
        symptoms: str,
        exclude_incident_id: int | None = None,
        limit: int = 3,
    ) -> list[SimilarIncidentMemory]:
        query = self.db.query(IncidentMemory)
        if exclude_incident_id is not None:
            query = query.filter(IncidentMemory.incident_id != exclude_incident_id)

        symptom_keywords = self._keywords(symptoms)
        ranked: list[SimilarIncidentMemory] = []

        for memory in query.all():
            score = 0
            if incident_type and memory.incident_type == incident_type:
                score += 5
            memory_keywords = self._keywords(" ".join(filter(None, [memory.symptoms, memory.root_cause, memory.successful_fix or ""])))
            score += len(symptom_keywords & memory_keywords)
            if score > 0:
                ranked.append(SimilarIncidentMemory(memory=memory, score=score))

        ranked.sort(key=lambda item: (item.score, item.memory.created_at), reverse=True)
        return ranked[:limit]

    def memories_for_prompt(self, memories: Iterable[SimilarIncidentMemory]) -> str:
        lines: list[str] = []
        for item in memories:
            memory = item.memory
            lines.append(
                (
                    f"- incident_type={memory.incident_type}; "
                    f"confidence={memory.confidence}; "
                    f"root_cause={memory.root_cause}; "
                    f"successful_fix={memory.successful_fix or 'unknown'}; "
                    f"tools_used={', '.join(memory.tools_used)}"
                )
            )
        return "\n".join(lines) if lines else "No similar incident memory found."

    def memories_for_timeline(self, memories: Iterable[SimilarIncidentMemory]) -> list[dict[str, object]]:
        return [
            {
                "memory_id": item.memory.id,
                "incident_id": item.memory.incident_id,
                "incident_type": item.memory.incident_type,
                "root_cause": item.memory.root_cause,
                "successful_fix": item.memory.successful_fix,
                "confidence": item.memory.confidence,
                "score": item.score,
            }
            for item in memories
        ]

    def list_used_for_incident(self, incident_id: int) -> list[IncidentMemoryRead]:
        memories: list[IncidentMemoryRead] = []
        steps = self.agent_step_service.list_for_incident(incident_id)
        for step in reversed(steps):
            if step.type != "memory_lookup" or not step.output_json:
                continue
            for item in step.output_json.get("memories", []):
                memory_id = item.get("memory_id")
                if memory_id is None:
                    continue
                memory = self.db.get(IncidentMemory, memory_id)
                if memory is not None:
                    memories.append(IncidentMemoryRead.model_validate(memory))
            break
        return memories

    def _extract_incident_type(self, steps: list) -> str | None:
        triage_step = self._latest_step(steps, "triage")
        if triage_step and triage_step.output_json:
            return triage_step.output_json.get("incident_type")
        return None

    def _extract_confidence(self, steps: list) -> str | None:
        diagnosis_step = self._latest_step(steps, "diagnosis")
        if diagnosis_step and diagnosis_step.output_json:
            return diagnosis_step.output_json.get("confidence")
        return None

    def _extract_successful_fix(self, incident_id: int, steps: list) -> str | None:
        remediation_step = self._latest_step(steps, "remediation_execution")
        if remediation_step and remediation_step.input_json:
            action_name = remediation_step.input_json.get("action_name")
            if action_name:
                return str(action_name)

        for audit_log in reversed(self.audit_service.list_for_target(target_type="incident", target_id=str(incident_id))):
            if audit_log.action == "remediation.executed":
                action_name = audit_log.metadata_json.get("action_name")
                if action_name:
                    return str(action_name)

        recommendation_step = self._latest_step(steps, "remediation_recommendation")
        if recommendation_step and recommendation_step.output_json:
            action_name = recommendation_step.output_json.get("action_name")
            if action_name:
                return str(action_name)
        return None

    def _extract_tools_used(self, steps: list) -> list[str]:
        tool_names = [step.tool_name for step in steps if step.tool_name]
        return list(dict.fromkeys(tool_names))

    def _latest_step(self, steps: list, step_type: str):
        for step in reversed(steps):
            if step.type == step_type:
                return step
        return None

    def _keywords(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9_]+", text.lower())
            if len(token) > 2 and token not in STOPWORDS
        }
