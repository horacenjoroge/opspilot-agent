from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider
from app.llm.qwen_provider import QwenProvider
from app.services.qwen_client import build_qwen_client


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockProvider()
    if settings.llm_provider == "qwen":
        return QwenProvider(build_qwen_client(settings))
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
