# Comprehensive Architecture

## System Overview

OpsPilot is a backend-controlled incident-response agent designed for SRE-style workflows. It accepts incidents, uses Qwen Cloud or a mock provider for reasoning, gathers evidence through allowlisted tools, applies a backend risk policy, pauses for approval when needed, simulates remediation, records a timeline, and produces evaluation results.

## Main Components

- Frontend/dashboard: FastAPI-served Jinja pages for incidents, approvals, demo scenarios, and evaluation runs
- FastAPI backend: main application runtime, routing, OpenAPI docs, static files
- Incident API: create, list, fetch, update, run agent, read timeline
- Agent orchestrator: controlled workflow loop with max-step limit and safe fallbacks
- Qwen provider/client: `QwenProvider`, `QwenClient`, and `MockProvider`
- Tool registry: allowlisted tool loading and execution
- Incident service: incident persistence and state updates
- Approval service: approval request lifecycle and simulated post-approval execution
- Remediation service: implemented through the remediation tool and approval workflow
- Audit log service: append-only audit records for important actions
- Database: SQLite-backed SQLAlchemy models
- Mock/real tools: logs, metrics, health, deployment, runbook, remediation, notification
- Alibaba Cloud ECS deployment: documented target shape with Docker and Nginx artifacts

## System Architecture Diagram

```mermaid
flowchart LR
    User[User / Judge]
    Dashboard[FastAPI Dashboard]
    API[FastAPI API]
    Agent[Incident Agent Orchestrator]
    Qwen[Qwen Cloud / Mock Provider]
    Registry[Tool Registry]
    Logs[logs_tool]
    Metrics[metrics_tool]
    Health[health_tool]
    Deploy[deployment_tool]
    Runbook[runbook_tool]
    Remediation[remediation_tool]
    Notify[notification_tool]
    Approval[Approval Service]
    Audit[Audit Service]
    DB[(SQLite Database)]
    ECS[Alibaba Cloud ECS]

    User --> Dashboard
    User --> API
    Dashboard --> API
    API --> Agent
    Agent --> Qwen
    Agent --> Registry
    Registry --> Logs
    Registry --> Metrics
    Registry --> Health
    Registry --> Deploy
    Registry --> Runbook
    Registry --> Remediation
    Registry --> Notify
    Agent --> Approval
    Agent --> Audit
    Approval --> Audit
    Agent --> DB
    Approval --> DB
    Audit --> DB
    Dashboard --> DB
    API --> DB
    ECS --> API
```

## Incident Workflow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard/API
    participant A as Agent
    participant Q as Qwen/Mock
    participant T as Tool Registry
    participant P as Approval Service
    participant DB as Database

    U->>D: Create or seed incident
    D->>DB: Save Incident
    U->>D: Run agent
    D->>A: Start workflow
    A->>Q: Triage request
    Q-->>A: Strict JSON triage
    A->>DB: Save AgentStep(triage/tool_selection)
    A->>T: Execute allowlisted tools
    T-->>A: Tool results
    A->>DB: Save AgentStep(tool_call...)
    A->>Q: Diagnosis request with evidence + memory
    Q-->>A: Strict JSON diagnosis
    A->>Q: Remediation request
    Q-->>A: Strict JSON remediation
    A->>DB: Save AgentStep(policy_decision)
    alt Dangerous action
        A->>P: Create approval request
        P->>DB: Save ApprovalRequest + AgentStep
        U->>D: Approve action
        D->>P: Approve request
        P->>DB: Save AgentStep(remediation/final_report)
    else Safe action
        A->>T: Execute remediation_tool
        A->>DB: Save AgentStep(remediation/final_report)
    end
    A->>DB: Save IncidentMemory
```

## Approval Workflow Diagram

```mermaid
flowchart TD
    Start[Remediation recommendation]
    Policy[Backend risk policy]
    Safe[Execute directly]
    Pending[Create ApprovalRequest]
    Approve[Approve]
    Reject[Reject]
    Simulate[Simulated remediation]
    Resolve[Resolve incident]
    Stop[Stop execution]

    Start --> Policy
    Policy -->|safe| Safe
    Policy -->|medium/dangerous| Pending
    Pending --> Approve
    Pending --> Reject
    Approve --> Simulate
    Simulate --> Resolve
    Reject --> Stop
```

## Tool Invocation Diagram

```mermaid
flowchart TD
    Model[Qwen structured output]
    Validate[Allowlist + schema validation]
    Registry[ToolRegistry]
    Tool[Selected Tool]
    Result[ToolResult]
    Step[AgentStep]
    Timeline[Timeline / Dashboard]

    Model --> Validate
    Validate --> Registry
    Registry --> Tool
    Tool --> Result
    Result --> Step
    Step --> Timeline
```

## Why the Model Does Not Execute Infrastructure Actions Directly

- model output is untrusted
- tool names are validated against the backend allowlist
- remediation actions run only through backend-owned services/tools
- risky actions create `ApprovalRequest` records first
- the dashboard and API expose approval explicitly before simulated execution

## How Backend Validation Works

- Qwen responses must be strict JSON
- Pydantic schemas validate triage, tool selection, diagnosis, remediation, and final report payloads
- unknown tools are rejected
- provider timeout or invalid JSON triggers a safe fallback path

## How Tool Allowlisting Works

- the registry owns the executable tool set
- only registered tool names can run
- the agent validates tool output before continuing
- there is no arbitrary shell or dynamic code execution surface from model output

## How Human Approval Prevents Unsafe Automation

- backend policy owns risk classification
- dangerous actions always require approval
- rejected approvals never execute
- approved actions still use simulated remediation, not direct infrastructure control
