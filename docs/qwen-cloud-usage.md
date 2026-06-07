# Qwen Cloud Usage

## Model Used

Current primary model:
- `qwen3.7-plus`

Additional configured field:
- `qwen3.7-max` appears in settings as a reasoning-model placeholder but is not currently wired into a separate runtime flow

## Why This Model Was Chosen

`qwen3.7-plus` supports the structured reasoning use case needed for incident classification, diagnosis, and remediation planning while fitting the hackathon requirement to demonstrate Qwen Cloud usage.

## Where Qwen Is Called

Implemented call sites:
- [backend/app/services/qwen_client.py](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/backend/app/services/qwen_client.py:1)
- [backend/app/llm/qwen_provider.py](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/backend/app/llm/qwen_provider.py:1)
- [backend/app/agents/incident_agent.py](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/backend/app/agents/incident_agent.py:1)

## Environment Variables

- `LLM_PROVIDER`
- `QWEN_API_KEY`
- `QWEN_MODEL`
- `QWEN_BASE_URL`

Optional app settings also exist for host, port, database URL, and approval behavior.

## Mock Provider vs Qwen Provider

`MockProvider`
- deterministic
- default for tests and most local development
- keeps the evaluation runner stable

`QwenProvider`
- uses the real Qwen Cloud compatible-mode API
- intended for live demo and final submission proof

## Agent Steps That Use Qwen

- alert classification
- tool selection normalization
- diagnosis
- remediation recommendation
- final report generation

## How Structured Outputs Are Validated

- Qwen responses are requested as JSON objects
- Pydantic validates triage, tool selection, diagnosis, remediation, and final report payloads
- invalid payloads do not directly control execution

## How API Failures Are Handled

- timeout handling with retries
- invalid JSON detection
- HTTP/network errors surfaced through structured errors
- incident agent safe fallbacks when provider output cannot be trusted

## How to Test With Mock Mode

```env
LLM_PROVIDER=mock
```

Then run:

```bash
cd backend
source .venv/bin/activate
pytest
```

## How to Test With Qwen Mode

```env
LLM_PROVIDER=qwen
QWEN_API_KEY=your_key_here
QWEN_MODEL=qwen3.7-plus
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

Optional live smoke test:

```bash
cd backend
QWEN_API_KEY='your_key' QWEN_MODEL='qwen3.7-plus' QWEN_BASE_URL='https://dashscope-intl.aliyuncs.com/compatible-mode/v1' ./.venv/bin/pytest tests/test_qwen_client.py -k live_smoke_call
```

## Safety Reminder

Never commit API keys, tokens, or `.env` files.
