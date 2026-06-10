import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("opspilot.qwen")

from app.core.config import Settings, get_settings


@dataclass
class QwenClientError(Exception):
    kind: str
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "message": self.message,
            "details": self.details or {},
        }


class QwenClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.transport = transport

    async def generate_json(self, *, system: str, user: str, schema_name: str) -> dict[str, Any]:
        if not self.api_key:
            raise QwenClientError(
                kind="configuration_error",
                message="QWEN_API_KEY is required when using the Qwen provider.",
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: QwenClientError | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info("Calling Qwen model=%s schema=%s attempt=%d", self.model, schema_name, attempt + 1)
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = self._extract_content(data)
                return json.loads(content)
            except httpx.TimeoutException:
                last_error = QwenClientError(
                    kind="timeout_error",
                    message=f"Timed out while calling Qwen for schema '{schema_name}'.",
                    details={"attempt": attempt + 1},
                )
            except httpx.HTTPStatusError as exc:
                raise QwenClientError(
                    kind="http_error",
                    message=f"Qwen returned HTTP {exc.response.status_code}.",
                    details={"status_code": exc.response.status_code},
                ) from exc
            except json.JSONDecodeError as exc:
                raise QwenClientError(
                    kind="invalid_json",
                    message="Qwen returned non-JSON content.",
                    details={"schema_name": schema_name},
                ) from exc
            except httpx.HTTPError as exc:
                raise QwenClientError(
                    kind="network_error",
                    message="Network error while calling Qwen.",
                    details={"error_type": exc.__class__.__name__},
                ) from exc
            except (KeyError, IndexError, TypeError) as exc:
                raise QwenClientError(
                    kind="invalid_response",
                    message="Qwen response payload did not contain a parsable assistant message.",
                    details={"schema_name": schema_name},
                ) from exc

        if last_error is not None:
            raise last_error
        raise QwenClientError(kind="unknown_error", message="Unknown error while calling Qwen.")

    def _extract_content(self, payload: dict[str, Any]) -> str:
        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            return "".join(text_parts)
        raise TypeError("Unexpected assistant content format")


def build_qwen_client(settings: Settings | None = None) -> QwenClient:
    resolved_settings = settings or get_settings()
    return QwenClient(
        api_key=resolved_settings.qwen_api_key,
        model=resolved_settings.qwen_model,
        base_url=resolved_settings.qwen_base_url,
    )
