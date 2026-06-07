from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(self, *, actor: str, action: str, target_type: str, target_id: str, metadata_json: dict) -> AuditLog:
        audit_log = AuditLog(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata_json=metadata_json,
        )
        self.db.add(audit_log)
        self.db.flush()
        return audit_log

    def list_for_target(self, *, target_type: str, target_id: str) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.target_type == target_type, AuditLog.target_id == target_id)
            .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
            .all()
        )
