from typing import Any

from app.llm.base import LLMProvider
from app.services.qwen_client import QwenClient


class QwenProvider(LLMProvider):
    def __init__(self, client: QwenClient) -> None:
        self.client = client

    async def generate_json(self, *, system: str, user: str, schema_name: str) -> dict[str, Any]:
        return await self.client.generate_json(system=system, user=user, schema_name=schema_name)
