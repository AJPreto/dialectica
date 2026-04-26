"""Deterministic answer scoring helpers."""

from __future__ import annotations

import math
import re
from typing import Any


BOOLEAN_TRUE = {"yes", "true", "1", "allowed", "correct"}
BOOLEAN_FALSE = {"no", "false", "0", "not allowed", "incorrect"}
TERNARY_UNKNOWN = {
    "unknown",
    "undetermined",
    "uncertain",
    "cannot determine",
    "can't determine",
    "cannot tell",
    "can't tell",
    "insufficient information",
    "insufficient info",
    "not enough information",
    "not enough info",
    "unclear",
    "maybe",
}


def score_answer(answer: str, gold_answer: Any, answer_type: str, choices: list[str] | None = None) -> dict[str, Any]:
    normalized_pred = normalize_answer(answer, answer_type, choices=choices)
    normalized_gold = normalize_answer(gold_answer, answer_type, choices=choices)
    is_correct = normalized_pred == normalized_gold and normalized_gold is not None
    return {
        "correct": is_correct,
        "predicted": normalized_pred,
        "gold": normalized_gold,
    }


def normalize_answer(value: Any, answer_type: str, choices: list[str] | None = None) -> Any:
    if value is None:
        return None
    text = _normalize_text(str(value))
    if answer_type == "boolean":
        if text in BOOLEAN_TRUE:
            return "yes"
        if text in BOOLEAN_FALSE:
            return "no"
        return None
    if answer_type == "ternary":
        if text in BOOLEAN_TRUE:
            return "yes"
        if text in BOOLEAN_FALSE:
            return "no"
        if text in TERNARY_UNKNOWN:
            return "unknown"
        return None
    if answer_type == "multiple_choice":
        if not choices:
            return text
        normalized_choices = {_normalize_text(choice): choice for choice in choices}
        if text in normalized_choices:
            return normalized_choices[text]
        letter_match = re.match(r"^([a-z])[\)\.\:]?$", text)
        if letter_match:
            index = ord(letter_match.group(1)) - ord("a")
            if 0 <= index < len(choices):
                return choices[index]
        return None
    if answer_type == "integer":
        try:
            return int(float(text))
        except ValueError:
            return None
    if answer_type == "number":
        try:
            number = float(text)
        except ValueError:
            return None
        if math.isfinite(number):
            return round(number, 8)
        return None
    return text


def extract_answer_payload(text: str) -> dict[str, str]:
    """Extract a normalized answer payload from model text.

    The caller should prefer structured model output, but this fallback keeps
    the benchmark robust when a provider returns plain text.
    """
    cleaned = text.strip()
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        try:
            import json

            payload = json.loads(json_match.group(0))
            answer = str(payload.get("answer", "")).strip()
            justification = str(payload.get("justification", "")).strip()
            return {"answer": answer, "justification": justification}
        except json.JSONDecodeError:
            pass
    first_line = cleaned.splitlines()[0] if cleaned else ""
    return {"answer": first_line.strip(), "justification": cleaned}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())
