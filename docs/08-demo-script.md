# Demo Script

## Goal

Keep the demo under 3 minutes and show an engineering workflow rather than a chat exchange.

| Time | Scene |
|---|---|
| 0:00-0:20 | Explain the incident triage problem for small engineering teams |
| 0:20-0:45 | Launch the `high_api_error_rate` demo incident from the dashboard |
| 0:45-1:20 | Show Qwen severity classification, selected tools, and evidence-first timeline growth |
| 1:20-1:50 | Show diagnosis, confidence, and dangerous remediation recommendation |
| 1:50-2:15 | Show backend risk policy forcing a human approval step |
| 2:15-2:35 | Approve the action and show simulated remediation plus final report |
| 2:35-3:00 | Close on architecture, Qwen Cloud usage, evaluation coverage, and deployment readiness |

## Required Story Beats

- The agent uses Qwen for reasoning, not direct execution.
- Tool calls are visible and explainable.
- Risky remediation pauses for approval.
- The backend records an audit timeline.

## Evidence-First Demo Sequence

1. Open the dashboard and explain that OpsPilot is a workflow agent, not a chatbot.
2. Launch the `high_api_error_rate` scenario from `/demo`.
3. Show the created incident in the incident list.
4. Open the incident detail page and run the agent.
5. Point out the Qwen severity classification in the timeline.
6. Show the selected tools coming from the validated allowlist.
7. Show logs, metrics, health, deployment, and runbook evidence appearing in order.
8. Explain that the diagnosis is backed by collected evidence, not free-form model guesswork.
9. Show the dangerous remediation recommendation.
10. Explain that the backend risk policy blocks direct execution.
11. Open the approval board and approve the request.
12. Return to the incident detail page to show the remediation result and resolved status.
13. Show the final report.
14. Explain that the memory layer saves this incident for reuse.
15. Open `/evals` and show the scenario PASS or FAIL results in the dashboard.

## Demo Emphasis

The main scenario should be `high_api_error_rate` because it clearly demonstrates evidence gathering, diagnosis, approval, simulated remediation, and final reporting in a way judges can follow quickly.

## Honesty Notes For The Demo

- Implemented now: evidence-first timeline, Qwen classification, selected tools, diagnosis, approval flow, remediation, final report, incident memory, and a visible evaluation results screen
