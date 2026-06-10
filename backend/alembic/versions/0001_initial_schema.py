"""initial schema with evaluation history

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("severity", sa.Enum("low", "medium", "high", "critical", name="severity_enum"), nullable=False),
        sa.Column("status", sa.Enum("new", "triaging", "waiting_for_approval", "remediating", "resolved", "failed", name="incident_status_enum"), nullable=False),
        sa.Column("root_cause_summary", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("final_report", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_id", "incidents", ["id"])
    op.create_index("ix_incidents_status_severity", "incidents", ["status", "severity"])
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"])

    op.create_table(
        "agent_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=True),
        sa.Column("input_json", sa.JSON(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("model_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("success", "failed", name="tool_status_enum"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_steps_id", "agent_steps", ["id"])
    op.create_index("ix_agent_steps_incident_id", "agent_steps", ["incident_id"])
    op.create_index("ix_agent_steps_incident_id_step_number", "agent_steps", ["incident_id", "step_number"])

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("action_name", sa.String(), nullable=False),
        sa.Column("risk_level", sa.Enum("safe", "medium", "dangerous", name="risk_level_enum"), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="approval_status_enum"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expected_impact", sa.Text(), nullable=False),
        sa.Column("rollback_plan", sa.Text(), nullable=False),
        sa.Column("action_payload_json", sa.JSON(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_requests_id", "approval_requests", ["id"])
    op.create_index("ix_approval_requests_incident_id", "approval_requests", ["incident_id"])
    op.create_index("ix_approval_requests_incident_id_status", "approval_requests", ["incident_id", "status"])
    op.create_index("ix_approval_requests_status_requested_at", "approval_requests", ["status", "requested_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_target_created_at", "audit_logs", ["target_type", "target_id", "created_at"])

    op.create_table(
        "incident_memories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("incident_type", sa.String(), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("tools_used", sa.JSON(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("successful_fix", sa.Text(), nullable=True),
        sa.Column("failed_fix", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_id"),
    )
    op.create_index("ix_incident_memories_id", "incident_memories", ["id"])
    op.create_index("ix_incident_memories_incident_id", "incident_memories", ["incident_id"])
    op.create_index("ix_incident_memories_incident_type", "incident_memories", ["incident_type"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("total_cases", sa.Integer(), nullable=False),
        sa.Column("passed_cases", sa.Integer(), nullable=False),
        sa.Column("failed_cases", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_runs_id", "evaluation_runs", ["id"])
    op.create_index("ix_evaluation_runs_status_started_at", "evaluation_runs", ["status", "started_at"])
    op.create_index("ix_evaluation_runs_provider_started_at", "evaluation_runs", ["provider", "started_at"])

    op.create_table(
        "evaluation_case_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=False),
        sa.Column("case_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_case_results_id", "evaluation_case_results", ["id"])
    op.create_index("ix_evaluation_case_results_evaluation_run_id", "evaluation_case_results", ["evaluation_run_id"])
    op.create_index("ix_eval_case_results_run_case", "evaluation_case_results", ["evaluation_run_id", "case_name"])


def downgrade() -> None:
    op.drop_index("ix_eval_case_results_run_case", table_name="evaluation_case_results")
    op.drop_index("ix_evaluation_case_results_evaluation_run_id", table_name="evaluation_case_results")
    op.drop_index("ix_evaluation_case_results_id", table_name="evaluation_case_results")
    op.drop_table("evaluation_case_results")

    op.drop_index("ix_evaluation_runs_provider_started_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_status_started_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_id", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")

    op.drop_index("ix_incident_memories_incident_type", table_name="incident_memories")
    op.drop_index("ix_incident_memories_incident_id", table_name="incident_memories")
    op.drop_index("ix_incident_memories_id", table_name="incident_memories")
    op.drop_table("incident_memories")

    op.drop_index("ix_audit_logs_target_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_approval_requests_status_requested_at", table_name="approval_requests")
    op.drop_index("ix_approval_requests_incident_id_status", table_name="approval_requests")
    op.drop_index("ix_approval_requests_incident_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_id", table_name="approval_requests")
    op.drop_table("approval_requests")

    op.drop_index("ix_agent_steps_incident_id_step_number", table_name="agent_steps")
    op.drop_index("ix_agent_steps_incident_id", table_name="agent_steps")
    op.drop_index("ix_agent_steps_id", table_name="agent_steps")
    op.drop_table("agent_steps")

    op.drop_index("ix_incidents_created_at", table_name="incidents")
    op.drop_index("ix_incidents_status_severity", table_name="incidents")
    op.drop_index("ix_incidents_id", table_name="incidents")
    op.drop_table("incidents")
