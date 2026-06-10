from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.policies import evaluate_action_policy
from app.core.config import get_settings
from app.models.approval import ApprovalRequest
from app.schemas.agent_step import AgentStepCreate
from app.schemas.approval import ApprovalRequestCreate
from app.schemas.enums import ApprovalStatus, IncidentStatus, ToolStatus
from app.services.agent_steps import AgentStepService
from app.services.audit import AuditService
from app.services.incident_memory import IncidentMemoryService
from app.services.incidents import IncidentService


class ApprovalNotFoundError(ValueError):
    pass


class ApprovalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_service = AuditService(db)
        self.agent_step_service = AgentStepService(db)
        self.incident_service = IncidentService(db)
        self.memory_service = IncidentMemoryService(db)

    def create_request(self, payload: ApprovalRequestCreate) -> ApprovalRequest:
        approval_request = ApprovalRequest(
            **payload.model_dump(),
            status=ApprovalStatus.pending,
        )
        self.db.add(approval_request)
        self.db.flush()
        self.audit_service.log(
            actor="system",
            action="approval.requested",
            target_type="approval_request",
            target_id=str(approval_request.id),
            metadata_json={
                "incident_id": approval_request.incident_id,
                "action_name": approval_request.action_name,
                "risk_level": approval_request.risk_level.value,
            },
        )
        self.agent_step_service.create_step(
            AgentStepCreate(
                incident_id=approval_request.incident_id,
                step_number=self.agent_step_service.next_step_number(approval_request.incident_id),
                type="approval_request_created",
                output_json={
                    "approval_request_id": approval_request.id,
                    "action_name": approval_request.action_name,
                    "risk_level": approval_request.risk_level.value,
                    "reason": approval_request.reason,
                    "expected_impact": approval_request.expected_impact,
                    "rollback_plan": approval_request.rollback_plan,
                },
                model_summary=f"Approval required for action '{approval_request.action_name}'.",
                status=ToolStatus.success,
            )
        )
        self.db.commit()
        self.db.refresh(approval_request)
        return approval_request

    def create_request_from_policy(
        self,
        *,
        incident_id: int,
        action_name: str,
        reason: str,
        expected_impact: str,
        rollback_plan: str,
        action_payload_json: dict | None = None,
    ) -> ApprovalRequest:
        decision = evaluate_action_policy(action_name, get_settings())
        if not decision.requires_approval:
            raise ValueError(f"Action '{action_name}' does not require approval under current policy.")
        return self.create_request(
            ApprovalRequestCreate(
                incident_id=incident_id,
                action_name=action_name,
                risk_level=decision.risk_level,
                reason=reason,
                expected_impact=expected_impact,
                rollback_plan=rollback_plan,
                action_payload_json=action_payload_json,
            )
        )

    def list_requests(self, *, limit: int | None = None, offset: int = 0) -> list[ApprovalRequest]:
        query = self.db.query(ApprovalRequest).order_by(ApprovalRequest.requested_at.desc(), ApprovalRequest.id.desc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def count_requests(self) -> int:
        return self.db.query(ApprovalRequest).count()

    def get_request(self, approval_id: int) -> ApprovalRequest:
        approval_request = self.db.get(ApprovalRequest, approval_id)
        if approval_request is None:
            raise ApprovalNotFoundError(f"Approval request {approval_id} was not found.")
        return approval_request

    def approve_request(self, approval_id: int, approved_by: str) -> ApprovalRequest:
        approval_request = self.get_request(approval_id)
        approval_request.status = ApprovalStatus.approved
        approval_request.approved_by = approved_by
        approval_request.approved_at = datetime.now(timezone.utc)
        self.db.flush()
        self.audit_service.log(
            actor=approved_by,
            action="approval.approved",
            target_type="approval_request",
            target_id=str(approval_request.id),
            metadata_json={"incident_id": approval_request.incident_id},
        )
        self.agent_step_service.create_step(
            AgentStepCreate(
                incident_id=approval_request.incident_id,
                step_number=self.agent_step_service.next_step_number(approval_request.incident_id),
                type="approval_decision",
                output_json={
                    "approval_request_id": approval_request.id,
                    "decision": ApprovalStatus.approved.value,
                    "approved_by": approved_by,
                },
                model_summary=f"Approval request {approval_request.id} approved by {approved_by}.",
                status=ToolStatus.success,
            )
        )
        self._execute_pending_action(approval_request, approved_by)
        self.db.commit()
        self.db.refresh(approval_request)
        return approval_request

    def reject_request(self, approval_id: int, approved_by: str) -> ApprovalRequest:
        approval_request = self.get_request(approval_id)
        approval_request.status = ApprovalStatus.rejected
        approval_request.approved_by = approved_by
        approval_request.approved_at = datetime.now(timezone.utc)
        self.db.flush()
        self.audit_service.log(
            actor=approved_by,
            action="approval.rejected",
            target_type="approval_request",
            target_id=str(approval_request.id),
            metadata_json={"incident_id": approval_request.incident_id},
        )
        self.agent_step_service.create_step(
            AgentStepCreate(
                incident_id=approval_request.incident_id,
                step_number=self.agent_step_service.next_step_number(approval_request.incident_id),
                type="approval_decision",
                output_json={
                    "approval_request_id": approval_request.id,
                    "decision": ApprovalStatus.rejected.value,
                    "approved_by": approved_by,
                },
                model_summary=f"Approval request {approval_request.id} rejected by {approved_by}.",
                status=ToolStatus.success,
            )
        )
        self.db.commit()
        self.db.refresh(approval_request)
        return approval_request

    def _execute_pending_action(self, approval_request: ApprovalRequest, approved_by: str) -> None:
        if not approval_request.action_payload_json:
            return
        self.audit_service.log(
            actor=approved_by,
            action="remediation.executed",
            target_type="incident",
            target_id=str(approval_request.incident_id),
            metadata_json={
                **approval_request.action_payload_json,
                "approved": True,
                "approved_by": approved_by,
                "approval_request_id": approval_request.id,
            },
        )
        action_name = approval_request.action_payload_json.get("action_name", approval_request.action_name)
        self.agent_step_service.create_step(
            AgentStepCreate(
                incident_id=approval_request.incident_id,
                step_number=self.agent_step_service.next_step_number(approval_request.incident_id),
                type="remediation_execution",
                tool_name="remediation_tool",
                input_json=approval_request.action_payload_json,
                output_json={
                    "action_name": action_name,
                    "approved_by": approved_by,
                    "approval_request_id": approval_request.id,
                    "result": "approved_remediation_executed",
                },
                model_summary=f"Approved remediation '{action_name}' executed by {approved_by}.",
                status=ToolStatus.success,
            )
        )
        self.incident_service.update_incident_fields(
            approval_request.incident_id,
            status=IncidentStatus.resolved,
            final_report=f"Approved remediation '{action_name}' executed by {approved_by}. Incident resolved.",
        )
        self.agent_step_service.create_step(
            AgentStepCreate(
                incident_id=approval_request.incident_id,
                step_number=self.agent_step_service.next_step_number(approval_request.incident_id),
                type="final_report",
                output_json={
                    "summary": f"Approved remediation '{action_name}' executed by {approved_by}. Incident resolved.",
                    "incident_status": IncidentStatus.resolved.value,
                    "actions_taken": [action_name],
                    "follow_up_items": ["Review the remediation outcome and update the runbook if needed."],
                },
                model_summary=f"Approved remediation '{action_name}' executed by {approved_by}. Incident resolved.",
                status=ToolStatus.success,
            )
        )
        self.memory_service.create_or_update_from_incident(approval_request.incident_id, successful_fix=action_name)
