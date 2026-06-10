from datetime import datetime

from sqlalchemy.orm import Session

from app.models.approval import ApprovalRequest
from app.models.audit_log import AuditLog
from app.schemas.timeline import TimelineItem
from app.services.agent_steps import AgentStepService
from app.services.approvals import ApprovalService
from app.services.audit import AuditService


class TimelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.agent_step_service = AgentStepService(db)
        self.approval_service = ApprovalService(db)
        self.audit_service = AuditService(db)

    def build_incident_timeline(
        self,
        incident_id: int,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[TimelineItem]:
        items: list[tuple[datetime, TimelineItem]] = []

        for step in self.agent_step_service.list_for_incident(incident_id):
            items.append(
                (
                    step.created_at,
                    TimelineItem(
                        occurred_at=step.created_at,
                        category="agent_step",
                        label=step.type if step.tool_name is None else step.tool_name,
                        status=step.status.value,
                        details={
                            "step_number": step.step_number,
                            "title": step.title,
                            "tool_name": step.tool_name,
                            "model_summary": step.model_summary,
                            "input_json": step.input_json,
                            "output_json": step.output_json,
                        },
                    ),
                )
            )

        for approval in self.approval_service.list_requests():
            if approval.incident_id != incident_id:
                continue
            items.append(
                (
                    approval.requested_at,
                    TimelineItem(
                        occurred_at=approval.requested_at,
                        category="approval_request",
                        label=approval.action_name,
                        status=approval.status.value,
                        details={
                            "risk_level": approval.risk_level.value,
                            "reason": approval.reason,
                            "expected_impact": approval.expected_impact,
                            "rollback_plan": approval.rollback_plan,
                            "approved_by": approval.approved_by,
                        },
                    ),
                )
            )

        for audit_log in self.audit_service.list_for_target(target_type="incident", target_id=str(incident_id)):
            items.append(
                (
                    audit_log.created_at,
                    TimelineItem(
                        occurred_at=audit_log.created_at,
                        category="audit_log",
                        label=audit_log.action,
                        status="recorded",
                        details=audit_log.metadata_json,
                    ),
                )
            )

        items.sort(key=lambda item: item[0])
        timeline = [item for _, item in items]
        if offset:
            timeline = timeline[offset:]
        if limit is not None:
            timeline = timeline[:limit]
        return timeline

    def count_incident_timeline_items(self, incident_id: int) -> int:
        return len(self.build_incident_timeline(incident_id))
