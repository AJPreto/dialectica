"""End-to-end answer evaluation for Direct vs Dialectica prompting."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from .canonical import canonicalize_logical_form
from .parser import parse_document, parse_text
from .prompting import build_dialectica_prompt, build_direct_prompt, build_structured_prompt
from .providers import ProviderError, build_provider
from .scoring import extract_answer_payload, score_answer
from .validation import validate_logical_form


@dataclass
class ConditionResult:
    name: str
    answer: str
    justification: str
    correct: bool
    predicted: Any
    gold: Any
    latency_seconds: float
    usage: dict[str, Any] | None
    prompt: str
    instructions: str
    provider_raw: dict[str, Any] | None
    parser_validation_errors: list[str]


def evaluate_answer_dataset(
    path: str | Path,
    provider_name: str,
    model: str | None = None,
    include_gold_dialectica: bool = False,
) -> dict[str, Any]:
    dataset = _load_dataset(path)
    provider = build_provider(provider_name, model=model)
    cases: list[dict[str, Any]] = []

    aggregate_correct: dict[str, list[bool]] = {}

    for case in dataset:
        context_text = str(case.get("context", ""))
        question_text = str(case.get("question", ""))
        language = str(case.get("language", "en"))
        context_form = canonicalize_logical_form(parse_document(context_text, language=language))
        question_form = canonicalize_logical_form(parse_text(question_text, language=language))
        parser_errors = validate_logical_form(context_form) + validate_logical_form(question_form)

        condition_specs: list[tuple[str, str, str, list[str]]] = []
        direct_instructions, direct_prompt = build_direct_prompt(case)
        condition_specs.append(("direct", direct_instructions, direct_prompt, []))
        structured_instructions, structured_prompt = build_structured_prompt(case)
        condition_specs.append(("structured", structured_instructions, structured_prompt, []))
        dialectica_instructions, dialectica_prompt = build_dialectica_prompt(case, context_form, question_form)
        condition_specs.append(("dialectica_parsed", dialectica_instructions, dialectica_prompt, parser_errors))

        gold_context_form = _maybe_get_gold_logical_form(case, "gold_logical_form")
        gold_question_form = _maybe_get_gold_logical_form(case, "gold_question_logical_form")
        if include_gold_dialectica and gold_context_form and gold_question_form:
            gold_instructions, gold_prompt = build_dialectica_prompt(
                case,
                gold_context_form,
                gold_question_form,
                use_gold=True,
            )
            condition_specs.append(("dialectica_gold", gold_instructions, gold_prompt, []))

        condition_results: list[ConditionResult] = []
        for name, instructions, prompt, validation_errors in condition_specs:
            response = provider.generate(
                instructions,
                prompt,
                metadata={"gold_answer": case.get("gold_answer"), "case_id": case.get("id"), "condition": name},
            )
            payload = extract_answer_payload(response.text)
            score = score_answer(
                payload["answer"],
                case.get("gold_answer"),
                case.get("answer_type", "exact"),
                choices=case.get("choices"),
            )
            aggregate_correct.setdefault(name, []).append(bool(score["correct"]))
            condition_results.append(
                ConditionResult(
                    name=name,
                    answer=payload["answer"],
                    justification=payload["justification"],
                    correct=bool(score["correct"]),
                    predicted=score["predicted"],
                    gold=score["gold"],
                    latency_seconds=response.latency_seconds,
                    usage=response.usage,
                    prompt=prompt,
                    instructions=instructions,
                    provider_raw=response.raw,
                    parser_validation_errors=validation_errors,
                )
            )

        cases.append(
            {
                "id": case["id"],
                "context": context_text,
                "question": question_text,
                "gold_answer": case.get("gold_answer"),
                "answer_type": case.get("answer_type", "exact"),
                "conditions": [asdict(result) for result in condition_results],
                "parsed_context": context_form,
                "parsed_question": question_form,
            }
        )

    aggregates = {
        name: {
            "accuracy": mean(1.0 if flag else 0.0 for flag in flags) if flags else 0.0,
            "case_count": len(flags),
        }
        for name, flags in aggregate_correct.items()
    }

    return {
        "dataset_path": str(path),
        "provider": provider_name,
        "model": model,
        "aggregate": aggregates,
        "cases": cases,
    }


def write_report(report: dict[str, Any], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _load_dataset(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _maybe_get_gold_logical_form(case: dict[str, Any], field: str) -> dict[str, Any] | None:
    if field not in case:
        return None
    return canonicalize_logical_form(case[field])

