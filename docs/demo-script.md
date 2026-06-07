# 3-Minute Demo Script

## 0:00-0:20 Problem

"Small teams often do not have 24/7 SRE coverage, but incidents still need fast, safe triage. Most AI demos stop at chat or summarization. OpsPilot is different: it is an evidence-first SRE autopilot that investigates incidents, applies backend safety policy, and keeps humans in control of risky actions."

## 0:20-0:45 Create Incident Alert

"Here I’m launching the `high_api_error_rate` scenario. OpsPilot creates a real incident record in the backend, stores it, and makes it visible in the incident dashboard."

## 0:45-1:25 Agent Triage and Tool Calls

"Now I run the agent. Qwen classifies severity and incident type using strict JSON. The backend validates the selected tools against an allowlist, then gathers evidence from logs, metrics, health, deployments, and the runbook. Every step is stored in the incident timeline."

## 1:25-1:55 Diagnosis

"With evidence collected, Qwen generates a diagnosis. OpsPilot also checks incident memory so it can compare this incident with similar past failures. The diagnosis and memory usage are both persisted and visible."

## 1:55-2:20 Human Approval

"Next, Qwen recommends a remediation, but the model is not allowed to execute it. The backend risk policy marks the restart action as dangerous, so OpsPilot creates an approval request and pauses for a human decision."

## 2:20-2:40 Remediation and Incident Report

"I approve the action. OpsPilot performs a simulated remediation, stores the approval decision, records the remediation step, saves incident memory, and generates the final incident report."

## 2:40-3:00 Architecture, Qwen Cloud, Alibaba Cloud Deployment

"To finish, I show the architecture and evaluation view. OpsPilot uses Qwen Cloud for structured reasoning, FastAPI and SQLAlchemy for the backend, and Docker plus an Alibaba Cloud ECS deployment shape for hosting. The evaluation runner proves the same workflow passes across multiple seeded scenarios."
