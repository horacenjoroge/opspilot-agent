# Developer Guide

## Project Structure

- `backend/app/api`: FastAPI routes and dependencies
- `backend/app/agents`: orchestrator, prompt contracts, parser, policies
- `backend/app/llm`: provider abstraction and Qwen integration
- `backend/app/models`: SQLAlchemy models
- `backend/app/schemas`: Pydantic request/response models
- `backend/app/services`: business logic and persistence helpers
- `backend/app/tools`: tool implementations and registry
- `backend/app/templates` and `backend/app/static`: dashboard UI
- `backend/tests`: test suite
- `docs`: documentation set
- `deployment`: production-shaped deployment artifacts

## Coding Architecture Rules

- keep routes thin
- put business logic in services or agents
- never call Qwen directly from route handlers
- validate model output before using it
- treat model output as untrusted input

## How Routes Should Call Services

- routes should parse and validate input
- services should own persistence and business logic
- routes should translate service exceptions into HTTP responses

## How Services Should Call Tools

- go through `ToolRegistry`
- never run unknown tool names
- persist important results to `AgentStep` and audit records

## How the Agent Orchestrator Works

The incident agent coordinates:
- triage
- tool selection
- memory lookup
- tool execution
- diagnosis
- remediation
- policy
- approval or execution
- final report
- memory save

## How to Add a New Endpoint

1. create or extend a route module
2. define schemas
3. add summary/description/response models
4. call services, not raw DB logic from the route
5. add tests
6. update docs

## How to Add a New Model

1. add the SQLAlchemy model
2. register it for DB initialization
3. create matching schemas if needed
4. create services/tests
5. update ERD docs

## How to Add a New Tool

1. add a tool under `backend/app/tools`
2. define input schema and risk level
3. register it in `ToolRegistry`
4. test success and failure behavior
5. update tool docs

## How to Add a New Prompt

1. add prompt helpers under `backend/app/agents/prompts.py`
2. define or reuse a strict JSON schema
3. update parser validation
4. add tests for normal and failure paths

## How to Add a New Demo Scenario

1. add the seeded incident in `DemoService`
2. update the mock provider behavior if needed
3. update evaluation cases
4. add or extend tests

## How to Add a New Test

- use unit tests for schema/service validation
- use integration tests for API and workflow paths
- prefer `MockProvider` by default

## How to Update Docs

- document only implemented behavior as implemented
- mark everything else as future work
- keep judge-facing docs concise and practical

## Git Branch Naming Suggestions

- `feature/<short-name>`
- `fix/<short-name>`
- `docs/<short-name>`

## Commit Message Style

- `feat: add evaluation dashboard route`
- `fix: normalize approval timeline agent steps`
- `docs: add deployment guide`
