"""Model providers for answer evaluation."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


TOKEN_KEYS = ("input_tokens", "output_tokens", "total_tokens", "cached_tokens", "reasoning_tokens")
ANSWER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer", "justification"],
    "properties": {
        "answer": {"type": "string"},
        "justification": {"type": "string"},
    },
}


def token_counts(usage: dict[str, Any] | None) -> dict[str, int]:
    """Return all token counters as ints, defaulting missing ones to zero."""
    usage = usage if isinstance(usage, dict) else {}
    return {key: int(usage.get(key, 0) or 0) for key in TOKEN_KEYS}


@dataclass
class ProviderResponse:
    text: str
    latency_seconds: float
    usage: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    iterations: int = 1


class ProviderError(RuntimeError):
    """Raised when a model provider call fails."""


class BaseProvider(ABC):
    @abstractmethod
    def generate(self, instructions: str, prompt: str, metadata: dict[str, Any] | None = None) -> ProviderResponse:
        """Generate a structured answer for a benchmark prompt."""


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
            iterations=1,
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
                    "schema": ANSWER_SCHEMA,
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
            usage=_normalize_usage(raw.get("usage")),
            raw=raw,
            iterations=1,
        )


class OllamaProvider(BaseProvider):
    """Local Ollama provider with a localhost-only safety default."""

    def __init__(self, model: str, base_url: str | None = None) -> None:
        self.model = model
        default_base = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434/api"
        self.base_url = (base_url or default_base).rstrip("/")
        _validate_ollama_base_url(self.base_url)

    def generate(self, instructions: str, prompt: str, metadata: dict[str, Any] | None = None) -> ProviderResponse:
        url = f"{self.base_url}/chat"
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        "Return a JSON object that matches this schema exactly:\n"
                        f"{json.dumps(ANSWER_SCHEMA, indent=2)}"
                    ),
                },
            ],
            "stream": False,
            "format": ANSWER_SCHEMA,
            "options": {
                "temperature": 0,
            },
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started_at = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Ollama API request failed with status {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(
                "Ollama API request failed. Make sure a local Ollama server is running at "
                f"{self.base_url}. Original error: {exc.reason}"
            ) from exc

        latency = time.perf_counter() - started_at
        message = raw.get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Ollama response did not contain message.content.")
        return ProviderResponse(
            text=content,
            latency_seconds=latency,
            usage=_normalize_ollama_usage(raw),
            raw=raw,
            iterations=1,
        )


def build_provider(provider_name: str, model: str | None = None) -> BaseProvider:
    normalized = provider_name.strip().casefold()
    if normalized == "oracle":
        return OracleProvider()
    if normalized == "openai":
        if not model:
            raise ProviderError("--model is required when provider=openai")
        return OpenAIResponsesProvider(model=model)
    if normalized == "ollama":
        if not model:
            raise ProviderError("--model is required when provider=ollama")
        return OllamaProvider(model=model)
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


def _normalize_usage(usage: dict[str, Any] | None) -> dict[str, int] | None:
    if not isinstance(usage, dict):
        return None
    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}
    return {
        "input_tokens": int(usage.get("input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
        "cached_tokens": int(input_details.get("cached_tokens", 0) or 0),
        "reasoning_tokens": int(output_details.get("reasoning_tokens", 0) or 0),
    }


def _normalize_ollama_usage(raw: dict[str, Any]) -> dict[str, int]:
    input_tokens = int(raw.get("prompt_eval_count", 0) or 0)
    output_tokens = int(raw.get("eval_count", 0) or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cached_tokens": 0,
        "reasoning_tokens": 0,
    }


def _validate_ollama_base_url(base_url: str) -> None:
    if os.environ.get("DIALECTICA_ALLOW_REMOTE_OLLAMA") == "1":
        return
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").casefold()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return
    raise ProviderError(
        "Remote Ollama endpoints are blocked by default to avoid sending repo contents off-machine. "
        "Use a localhost URL or set DIALECTICA_ALLOW_REMOTE_OLLAMA=1 to override intentionally."
    )
