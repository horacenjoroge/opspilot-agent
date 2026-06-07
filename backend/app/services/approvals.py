from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.policies import evaluate_action_policy
from app.core.config import get_settings
from app.models.approval import ApprovalRequest
from app.schemas.approval import ApprovalRequestCreate
from app.schemas.enums import ApprovalStatus, IncidentStatus
from app.services.audit import AuditService
from app.services.incidents import IncidentService


class ApprovalNotFoundError(ValueError):
    pass


class ApprovalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_service = AuditService(db)
        self.incident_service = IncidentService(db)

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

    def list_requests(self) -> list[ApprovalRequest]:
        return (
            self.db.query(ApprovalRequest)
            .order_by(ApprovalRequest.requested_at.desc(), ApprovalRequest.id.desc())
            .all()
        )

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
        self.incident_service.update_incident_fields(
            approval_request.incident_id,
            status=IncidentStatus.resolved,
            final_report=f"Approved remediation '{action_name}' executed by {approved_by}. Incident resolved.",
        )
