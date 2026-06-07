# Qwen Cloud Usage

## Primary Model

The planned hackathon model is `qwen3.7-plus`.

## Provider Strategy

- Local development and tests use `MockProvider`.
- Final demo and submission switch to `QwenProvider`.
- Route handlers never call Qwen directly; they go through the provider abstraction and service layer.

## Planned Integration Points

- `backend/app/llm/qwen_provider.py`
- `backend/app/services/qwen_client.py`

These files now contain the Qwen Cloud integration surface. `QwenProvider` implements the provider abstraction, while `QwenClient` is the only component responsible for making outbound model requests, handling timeouts and retries, and parsing strict JSON responses.

## Environment Variables

```env
LLM_PROVIDER=mock
QWEN_API_KEY=
QWEN_MODEL=qwen3.7-plus
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_REASONING_MODEL=qwen3.7-max
```

## Switching Providers

- Use `LLM_PROVIDER=mock` for local tests and repeatable development.
- Use `LLM_PROVIDER=qwen` for the final hackathon demo once Qwen credentials are supplied through environment variables.
- Local tests remain on `MockProvider` by default, with an optional live smoke test for Qwen when `QWEN_API_KEY` is set.
- Match the base URL to the key type. For most hackathon pay-as-you-go setups, use `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`.

## Hackathon Alignment

This design satisfies the hackathon requirement because the final system will clearly show Qwen Cloud usage through a dedicated backend provider, while still preserving safe local development with a mock implementation.
