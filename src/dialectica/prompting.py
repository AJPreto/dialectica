"""Prompt builders for answer evaluation experiments."""

from __future__ import annotations

import json
from typing import Any

from .canonical import serialize_logical_form


ANSWER_SCHEMA_INSTRUCTIONS = (
    'Return JSON only with exactly these keys: "answer" and "justification". '
    '"answer" must contain only the final answer value. '
    '"justification" must be a brief explanation grounded in the provided information.'
)


def build_direct_prompt(case: dict[str, Any]) -> tuple[str, str]:
    instructions = (
        "You are solving a benchmark task. "
        "Answer only from the supplied context. "
        f"{ANSWER_SCHEMA_INSTRUCTIONS}"
    )
    prompt = _format_case(case)
    return instructions, prompt


def build_structured_prompt(case: dict[str, Any]) -> tuple[str, str]:
    instructions = (
        "You are solving a benchmark task. "
        "Before deciding, identify the relevant facts, conditions, constraints, negations, and exceptions internally. "
        "Do not reveal chain-of-thought. "
        f"{ANSWER_SCHEMA_INSTRUCTIONS}"
    )
    prompt = _format_case(case)
    return instructions, prompt


def build_dialectica_prompt(
    case: dict[str, Any],
    context_form: dict[str, Any],
    question_form: dict[str, Any],
    use_gold: bool = False,
) -> tuple[str, str]:
    instructions = (
        "You are solving a benchmark task using Dialectica, a logical intermediate representation. "
        "Prioritize the structured representation when it clarifies constraints, conditions, exceptions, and entailments. "
        "If the structure is ambiguous, rely on the source text conservatively. "
        f"{ANSWER_SCHEMA_INSTRUCTIONS}"
    )
    sections = [
        f"Mode: {'gold' if use_gold else 'parsed'} Dialectica representation",
        _format_case(case),
        "Context logical form JSON:",
        json.dumps(context_form, indent=2),
        "Context canonical serialization:",
        serialize_logical_form(context_form),
        "Question logical form JSON:",
        json.dumps(question_form, indent=2),
        "Question canonical serialization:",
        serialize_logical_form(question_form),
    ]
    if case.get("gold_encoding"):
        sections.extend(
            [
                "Formal encoding hints:",
                json.dumps(case["gold_encoding"], indent=2),
            ]
        )
    return instructions, "\n\n".join(sections)


def _format_case(case: dict[str, Any]) -> str:
    parts = [f"Question ID: {case['id']}"]
    if case.get("context"):
        parts.extend(["Context:", str(case["context"])])
    if case.get("question"):
        parts.extend(["Question:", str(case["question"])])
    if case.get("answer_type"):
        parts.append(f"Expected answer type: {case['answer_type']}")
    if case.get("choices"):
        parts.append("Choices: " + ", ".join(str(choice) for choice in case["choices"]))
    return "\n".join(parts)

