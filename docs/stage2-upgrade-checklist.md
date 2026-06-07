# Stage 2 Upgrade Checklist

## Evidence-first timeline
- [x] Incident created step stored
- [x] Qwen classification step stored
- [x] Tool selection step stored
- [x] Tool call steps stored
- [x] Diagnosis step stored
- [x] Risk policy step stored
- [x] Approval step stored
- [x] Remediation step stored
- [x] Final report step stored
- [x] Timeline visible in dashboard

## Risk policy
- [x] Action risk map exists
- [x] Dangerous actions require approval
- [x] Unknown actions rejected
- [x] Model cannot override policy
- [x] Rejected approval blocks execution
- [x] Approved action executes simulation

## Structured Qwen output
- [x] Triage schema exists
- [x] Tool selection schema exists
- [x] Diagnosis schema exists
- [x] Remediation schema exists
- [x] Final report schema exists
- [x] Invalid JSON fallback exists
- [x] Qwen timeout fallback exists

## Tool registry
- [x] Tool base interface exists
- [x] Registry exists
- [x] Allowed tools registered
- [x] Unknown tools rejected
- [x] Tool errors captured
- [x] Tool outputs saved

## Incident memory
- [x] Memory model exists
- [x] Memory saved after resolution
- [x] Similar memory retrieved
- [x] Memory added to Qwen context
- [x] Memory visible in timeline or report

## Evaluation
- [x] High API error-rate scenario exists
- [x] Queue backlog scenario exists
- [x] Database latency scenario exists
- [x] Ambiguous alert scenario exists
- [x] Tool failure scenario exists
- [x] Expected outputs defined
- [x] Evaluation runner exists
- [x] PASS/FAIL results produced
- [x] Evaluation result visible to user or documented

## Dashboard
- [x] Demo launcher exists
- [x] Incident list exists
- [x] Incident detail exists
- [x] Timeline visible
- [x] Approval buttons work
- [x] Final report visible
- [x] Evaluation results visible

## Docs
- [x] README updated
- [x] Stage 2 strategy doc created
- [x] Implementation upgrade plan created
- [x] Agent design updated
- [x] Tool system updated
- [x] Human approval docs updated
- [x] Testing docs updated
- [x] Demo script updated
- [ ] Devpost draft updated
