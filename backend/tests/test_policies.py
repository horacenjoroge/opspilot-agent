import pytest

from app.agents.policies import UnknownActionPolicyError, evaluate_action_policy
from app.core.config import Settings


def test_policy_requires_approval_for_dangerous_and_medium_actions_by_default() -> None:
    settings = Settings()

    dangerous = evaluate_action_policy("restart_api_workers_simulation", settings)
    medium = evaluate_action_policy("scale_workers_simulation", settings)
    safe = evaluate_action_policy("generate_report", settings)

    assert dangerous.requires_approval is True
    assert medium.requires_approval is True
    assert safe.requires_approval is False


def test_policy_can_relax_medium_actions_but_not_dangerous_actions() -> None:
    settings = Settings(REQUIRE_APPROVAL_FOR_MEDIUM_RISK=False)

    medium = evaluate_action_policy("scale_workers_simulation", settings)
    dangerous = evaluate_action_policy("rollback_deployment_simulation", settings)

    assert medium.requires_approval is False
    assert dangerous.requires_approval is True


def test_policy_rejects_unknown_actions() -> None:
    with pytest.raises(UnknownActionPolicyError):
        evaluate_action_policy("shell_exec_tool", Settings())
