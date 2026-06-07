def triage_system_prompt() -> str:
    return (
        "You are OpsPilot, a production incident triage assistant. "
        "Return strict JSON only with no markdown, prose, or code fences."
    )


def triage_user_prompt(*, incident_title: str, incident_description: str, source: str) -> str:
    return f"""
Investigate the following incident and return strict JSON only.

Incident title: {incident_title}
Source: {source}
Description: {incident_description}

Required JSON schema:
{{
  "severity": "low|medium|high|critical",
  "incident_type": "string",
  "recommended_tools": ["allowed_tool_name"],
  "reasoning_summary": "string",
  "requires_human_approval": false
}}
""".strip()


def diagnosis_system_prompt() -> str:
    return (
        "You are OpsPilot. Diagnose production incidents from evidence and respond with strict JSON only."
    )


def diagnosis_user_prompt(*, incident_context: str, evidence_summary: str) -> str:
    return f"""
Return strict JSON only based on the incident context and collected evidence.

Incident context: {incident_context}
Evidence summary: {evidence_summary}

Required JSON schema:
{{
  "root_cause_summary": "string",
  "evidence_summary": "string",
  "confidence": "low|medium|high"
}}
""".strip()


def remediation_system_prompt() -> str:
    return (
        "You are OpsPilot. Recommend a remediation action in strict JSON only. "
        "Do not execute actions or suggest unknown tool names."
    )


def remediation_user_prompt(*, diagnosis_summary: str, available_actions: list[str]) -> str:
    return f"""
Return strict JSON only for the safest appropriate remediation recommendation.

Diagnosis summary: {diagnosis_summary}
Available actions: {", ".join(available_actions)}

Required JSON schema:
{{
  "action_name": "string",
  "action_summary": "string",
  "risk_level": "safe|medium|dangerous",
  "requires_human_approval": true,
  "reason": "string",
  "expected_impact": "string",
  "rollback_plan": "string"
}}
""".strip()


def final_report_system_prompt() -> str:
    return "You are OpsPilot. Generate a final incident report using strict JSON only."


def final_report_user_prompt(*, incident_summary: str, actions_taken: list[str], final_status: str) -> str:
    return f"""
Return strict JSON only for the final report.

Incident summary: {incident_summary}
Actions taken: {", ".join(actions_taken)}
Final status: {final_status}

Required JSON schema:
{{
  "summary": "string",
  "incident_status": "new|triaging|waiting_for_approval|remediating|resolved|failed",
  "actions_taken": ["string"],
  "follow_up_items": ["string"]
}}
""".strip()
