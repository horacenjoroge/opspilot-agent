from dataclasses import dataclass

from app.core.config import Settings
from app.schemas.enums import RiskLevel
from app.tools.remediation_tool import ACTION_RISK_LEVELS


class UnknownActionPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class PolicyDecision:
    action_name: str
    risk_level: RiskLevel
    requires_approval: bool


def evaluate_action_policy(action_name: str, settings: Settings) -> PolicyDecision:
    risk_level = ACTION_RISK_LEVELS.get(action_name)
    if risk_level is None:
        raise UnknownActionPolicyError(f"Unknown action '{action_name}' was rejected by policy.")

    if risk_level == RiskLevel.safe:
        return PolicyDecision(action_name=action_name, risk_level=risk_level, requires_approval=False)
    if risk_level == RiskLevel.medium:
        return PolicyDecision(
            action_name=action_name,
            risk_level=risk_level,
            requires_approval=settings.require_approval_for_medium_risk,
        )
    return PolicyDecision(action_name=action_name, risk_level=risk_level, requires_approval=True)
