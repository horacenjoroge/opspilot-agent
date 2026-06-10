from enum import StrEnum


class Severity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(StrEnum):
    new = "new"
    triaging = "triaging"
    waiting_for_approval = "waiting_for_approval"
    remediating = "remediating"
    resolved = "resolved"
    failed = "failed"


class RiskLevel(StrEnum):
    safe = "safe"
    medium = "medium"
    dangerous = "dangerous"


class ToolStatus(StrEnum):
    success = "success"
    failed = "failed"


class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class UserRole(StrEnum):
    admin = "admin"
    operator = "operator"
    reviewer = "reviewer"
    viewer = "viewer"
