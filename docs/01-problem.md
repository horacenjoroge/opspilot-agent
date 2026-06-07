# Problem

## One-Line Pitch

OpsPilot is a Qwen-powered incident triage backend that automates first response while keeping dangerous remediation behind human approval.

## Problem Statement

Small engineering teams often run APIs, workers, queues, databases, and scheduled jobs without a dedicated SRE team. When an alert fires, the on-call developer still has to manually inspect logs, metrics, service health, recent deployments, and runbooks before taking action. That manual investigation slows down response time and increases pressure during already noisy incidents.

OpsPilot reduces that response time by giving the backend a controlled workflow agent that investigates incidents with approved tools, assembles evidence, recommends safe remediation, and records every decision in an audit timeline.

## Target Users

- Startup and hackathon teams running backend services without a full SRE function
- Backend engineers handling on-call responsibilities
- Platform leads who want faster triage without giving an LLM direct infrastructure control

## Why Existing Workflows Hurt

- Alert context is fragmented across dashboards, logs, deployment history, and runbooks
- Triage work is repetitive and time-sensitive
- Fully autonomous fixes are too risky for small teams without strong guardrails

## Non-Goals

- Replacing human judgment for dangerous infrastructure actions
- Acting as a general-purpose chat assistant for unrelated support tasks
- Directly executing unapproved tools or arbitrary shell commands

## Product Direction

OpsPilot is designed as an engineering system: the LLM proposes, the backend validates, policies decide what is allowed, and humans approve risky remediation.
