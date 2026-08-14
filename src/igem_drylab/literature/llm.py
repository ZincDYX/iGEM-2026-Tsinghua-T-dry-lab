from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from typing import Any

import requests


class LlmError(RuntimeError):
    """Raised when an OpenAI-compatible chat endpoint cannot return content."""


@dataclass(frozen=True)
class ChatClient:
    api_key: str
    api_base: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 1400
    timeout_seconds: int = 180
    retries: int = 3

    def complete_json(self, prompt: str, *, response_format: dict[str, Any] | None = None) -> dict[str, Any]:
        content = self.complete(prompt, response_format=response_format)
        parsed = parse_json_object(content)
        if parsed is None:
            raise LlmError("LLM response did not contain a JSON object")
        return parsed

    def complete(self, prompt: str, *, response_format: dict[str, Any] | None = None) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You extract structured information as JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        retry_status = {429, 500, 502, 503, 504}
        last_error: Exception | None = None
        for attempt in range(max(1, self.retries)):
            try:
                response = requests.post(
                    self.api_base,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                if response.status_code in retry_status and attempt < self.retries - 1:
                    _sleep_before_retry(response, attempt)
                    continue
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if not isinstance(content, str) or not content.strip():
                    raise LlmError("LLM response did not include choices[0].message.content")
                return content
            except (requests.RequestException, ValueError, LlmError) as exc:
                last_error = exc
                if attempt >= self.retries - 1:
                    break
                _sleep_before_retry(None, attempt)
        raise LlmError(f"LLM request failed: {last_error}")


def parse_json_object(text: str) -> dict[str, Any] | None:
    block = _extract_json_block(text)
    if block is None:
        return None
    try:
        parsed = json.loads(block)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_json_block(text: str) -> str | None:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end <= start:
        return None
    return stripped[start : end + 1]


def _sleep_before_retry(response: requests.Response | None, attempt: int) -> None:
    retry_after = response.headers.get("Retry-After") if response is not None else None
    try:
        wait = float(retry_after) if retry_after else None
    except ValueError:
        wait = None
    if wait is None:
        wait = 2**attempt + random.uniform(0, 0.5)
    time.sleep(max(0.0, wait))
