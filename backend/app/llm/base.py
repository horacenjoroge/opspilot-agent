from typing import Any, Protocol


class LLMProvider(Protocol):
    async def generate_json(self, *, system: str, user: str, schema_name: str) -> dict[str, Any]:
        ...
