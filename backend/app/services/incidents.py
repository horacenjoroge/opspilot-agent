from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate
from app.schemas.enums import IncidentStatus
from app.services.audit import AuditService


class IncidentNotFoundError(ValueError):
    pass


class IncidentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_service = AuditService(db)

    def create_incident(self, payload: IncidentCreate) -> Incident:
        incident = Incident(**payload.model_dump())
        self.db.add(incident)
        self.db.flush()
        self.audit_service.log(
            actor="system",
            action="incident.created",
            target_type="incident",
            target_id=str(incident.id),
            metadata_json={
                "severity": incident.severity.value,
                "source": incident.source,
                "status": incident.status.value,
            },
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def list_incidents(self) -> list[Incident]:
        return self.db.query(Incident).order_by(Incident.created_at.desc(), Incident.id.desc()).all()

    def get_incident(self, incident_id: int) -> Incident:
        incident = self.db.get(Incident, incident_id)
        if incident is None:
            raise IncidentNotFoundError(f"Incident {incident_id} was not found.")
        return incident

    def update_status(self, incident_id: int, status: IncidentStatus) -> Incident:
        incident = self.get_incident(incident_id)
        incident.status = status
        self.db.flush()
        self.audit_service.log(
            actor="system",
            action="incident.status_updated",
            target_type="incident",
            target_id=str(incident.id),
            metadata_json={"status": status.value},
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update_incident_fields(
        self,
        incident_id: int,
        *,
        status: IncidentStatus | None = None,
        root_cause_summary: str | None = None,
        recommended_action: str | None = None,
        final_report: str | None = None,
    ) -> Incident:
        incident = self.get_incident(incident_id)
        metadata: dict[str, str] = {}
        if status is not None:
            incident.status = status
            metadata["status"] = status.value
        if root_cause_summary is not None:
            incident.root_cause_summary = root_cause_summary
            metadata["root_cause_summary"] = root_cause_summary
        if recommended_action is not None:
            incident.recommended_action = recommended_action
            metadata["recommended_action"] = recommended_action
        if final_report is not None:
            incident.final_report = final_report
            metadata["final_report"] = final_report

        self.db.flush()
        self.audit_service.log(
            actor="system",
            action="incident.updated",
            target_type="incident",
            target_id=str(incident.id),
            metadata_json=metadata,
        )
        self.db.commit()
        self.db.refresh(incident)
        return incident
