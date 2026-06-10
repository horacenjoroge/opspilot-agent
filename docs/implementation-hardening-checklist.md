# Implementation Hardening Checklist

This file tracks the scoped hardening work so changes are completed in focused batches instead of partially overlapping.

## Prompt 1: Health/readiness only

- [x] Keep `GET /health` as lightweight liveness
- [x] Add `GET /ready`
- [x] Check DB connectivity in `/ready`
- [x] Check provider/config readiness in `/ready`
- [x] Validate `QWEN_API_KEY` and `QWEN_BASE_URL` when `LLM_PROVIDER=qwen`
- [x] Return status, timestamp, provider, and checks
- [x] Add tests
- [x] Update docs

## Prompt 2: Request tracing/errors only

- [x] Add `X-Request-ID` middleware
- [x] Reuse incoming request ID or generate one
- [x] Add request ID to responses
- [x] Include request ID in logs
- [x] Add common error response schema
- [x] Add global exception handlers
- [x] Do not leak secrets or stack traces
- [x] Add tests

## Prompt 3: Feature flags only

- [x] Add `ENABLE_DEMO_ROUTES`
- [x] Add `ENABLE_EVAL_ROUTES`
- [x] Add `ENABLE_DASHBOARD`
- [x] Keep defaults demo-friendly
- [x] Disable route registration or return `404`/disabled response when false
- [x] Add tests
- [x] Update `.env.example` and docs

## Prompt 4: Pagination/filtering only

- [x] Add `limit`/`offset` to incident list
- [x] Add `status`/`severity` filters to incident list
- [x] Add `limit`/`offset` to approvals list
- [x] Add `limit`/`offset` to timeline endpoint
- [x] Add response envelope schemas
- [x] Preserve compatibility where possible
- [x] Add tests
