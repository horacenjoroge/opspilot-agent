from app.schemas.agent_step import AgentStepCreate
from app.schemas.enums import ToolStatus
from app.services.agent_steps import AgentStepService


def test_agent_steps_are_ordered_and_sensitive_values_redacted(db_session) -> None:
    service = AgentStepService(db_session)

    second = service.create_step(
        AgentStepCreate(
            incident_id=1,
            step_number=2,
            type="tool_call",
            tool_name="metrics_tool",
            input_json={"token": "secret-value"},
            output_json={"status": "ok"},
            model_summary="Checked metrics.",
            status=ToolStatus.success,
        )
    )
    first = service.create_step(
        AgentStepCreate(
            incident_id=1,
            step_number=1,
            type="tool_call",
            tool_name="logs_tool",
            input_json={"query": "errors"},
            output_json={"authorization": "Bearer abc"},
            model_summary="Checked logs.",
            status=ToolStatus.success,
        )
    )

    ordered_steps = service.list_for_incident(1)

    assert [step.id for step in ordered_steps] == [first.id, second.id]
    assert second.input_json == {"token": "***redacted***"}
    assert first.output_json == {"authorization": "***redacted***"}
