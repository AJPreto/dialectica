"""Model providers for answer evaluation."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderResponse:
    text: str
    latency_seconds: float
    usage: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


class ProviderError(RuntimeError):
    """Raised when a model provider call fails."""


class BaseProvider:
    def generate(self, instructions: str, prompt: str, metadata: dict[str, Any] | None = None) -> ProviderResponse:
        raise NotImplementedError


class OracleProvider(BaseProvider):
    """Offline provider for smoke-testing the harness."""

    def generate(self, instructions: str, prompt: str, metadata: dict[str, Any] | None = None) -> ProviderResponse:
        start = time.perf_counter()
        answer = ""
        if metadata and "gold_answer" in metadata:
            answer = str(metadata["gold_answer"])
        payload = {"answer": answer, "justification": "Oracle provider returned the benchmark gold answer."}
        return ProviderResponse(
            text=json.dumps(payload),
            latency_seconds=time.perf_counter() - start,
            usage=None,
            raw={"provider": "oracle"},
        )


class OpenAIResponsesProvider(BaseProvider):
    """Minimal OpenAI Responses API client using the standard library."""

    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is not set.")

    def generate(self, instructions: str, prompt: str, metadata: dict[str, Any] | None = None) -> ProviderResponse:
        url = f"{self.base_url}/responses"
        body = {
            "model": self.model,
            "instructions": instructions,
            "input": prompt,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "dialectica_eval_answer",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["answer", "justification"],
                        "properties": {
                            "answer": {"type": "string"},
                            "justification": {"type": "string"},
                        },
                    },
                    "strict": True,
                }
            },
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started_at = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"OpenAI API request failed with status {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"OpenAI API request failed: {exc.reason}") from exc
        latency = time.perf_counter() - started_at
        output_text = _extract_output_text(raw)
        return ProviderResponse(
            text=output_text,
            latency_seconds=latency,
            usage=raw.get("usage"),
            raw=raw,
        )


def build_provider(provider_name: str, model: str | None = None) -> BaseProvider:
    normalized = provider_name.casefold()
    if normalized == "oracle":
        return OracleProvider()
    if normalized == "openai":
        if not model:
            raise ProviderError("--model is required when provider=openai")
        return OpenAIResponsesProvider(model=model)
    raise ProviderError(f"Unsupported provider: {provider_name}")


def _extract_output_text(raw: dict[str, Any]) -> str:
    output_text = raw.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    chunks: list[str] = []
    for item in raw.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(content["text"])
    if chunks:
        return "\n".join(chunks)
    raise ProviderError("OpenAI response did not contain output text.")

