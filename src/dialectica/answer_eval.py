"""End-to-end answer evaluation for Direct vs Dialectica prompting."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from .canonical import canonicalize_logical_form
from .fingerprint import fingerprint_logical_form
from .parser import parse_document, parse_text
from .prompting import (
    build_dialectica_prompt,
    build_dialectica_structural_prompt,
    build_direct_prompt,
    build_structured_prompt,
)
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
    token_counts: dict[str, int]
    iterations: int
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
    aggregate_latency: dict[str, list[float]] = {}
    aggregate_iterations: dict[str, list[int]] = {}
    aggregate_tokens: dict[str, dict[str, int]] = {}

    for case in dataset:
        context_text = str(case.get("context", ""))
        question_text = str(case.get("question", ""))
        language = str(case.get("language", "en"))
        context_form = canonicalize_logical_form(parse_document(context_text, language=language))
        question_form = canonicalize_logical_form(parse_text(question_text, language=language))
        context_fingerprint = fingerprint_logical_form(context_form)
        question_fingerprint = fingerprint_logical_form(question_form)
        parser_errors = validate_logical_form(context_form) + validate_logical_form(question_form)

        condition_specs: list[tuple[str, str, str, list[str]]] = []
        direct_instructions, direct_prompt = build_direct_prompt(case)
        condition_specs.append(("direct", direct_instructions, direct_prompt, []))
        structured_instructions, structured_prompt = build_structured_prompt(case)
        condition_specs.append(("structured", structured_instructions, structured_prompt, []))
        dialectica_instructions, dialectica_prompt = build_dialectica_prompt(case, context_form, question_form)
        condition_specs.append(("dialectica_parsed", dialectica_instructions, dialectica_prompt, parser_errors))
        structural_instructions, structural_prompt = build_dialectica_structural_prompt(
            case,
            context_form,
            question_form,
            context_fingerprint,
            question_fingerprint,
        )
        condition_specs.append(("dialectica_structural", structural_instructions, structural_prompt, parser_errors))

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
            gold_context_fingerprint = fingerprint_logical_form(gold_context_form)
            gold_question_fingerprint = fingerprint_logical_form(gold_question_form)
            gold_structural_instructions, gold_structural_prompt = build_dialectica_structural_prompt(
                case,
                gold_context_form,
                gold_question_form,
                gold_context_fingerprint,
                gold_question_fingerprint,
                use_gold=True,
            )
            condition_specs.append(("dialectica_gold_structural", gold_structural_instructions, gold_structural_prompt, []))

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
            token_counts = _normalize_token_counts(response.usage)
            aggregate_correct.setdefault(name, []).append(bool(score["correct"]))
            aggregate_latency.setdefault(name, []).append(response.latency_seconds)
            aggregate_iterations.setdefault(name, []).append(response.iterations)
            token_bucket = aggregate_tokens.setdefault(name, _empty_token_counts())
            for key, value in token_counts.items():
                token_bucket[key] += value
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
                    token_counts=token_counts,
                    iterations=response.iterations,
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
                "parsed_context_fingerprint": context_fingerprint,
                "parsed_question_fingerprint": question_fingerprint,
            }
        )

    aggregates = {}
    for name, flags in aggregate_correct.items():
        case_count = len(flags)
        token_totals = aggregate_tokens.get(name, _empty_token_counts())
        aggregates[name] = {
            "accuracy": mean(1.0 if flag else 0.0 for flag in flags) if flags else 0.0,
            "case_count": case_count,
            "average_latency_seconds": mean(aggregate_latency.get(name, [0.0])) if case_count else 0.0,
            "total_iterations": sum(aggregate_iterations.get(name, [])),
            "average_iterations": mean(aggregate_iterations.get(name, [0])) if case_count else 0.0,
            "total_input_tokens": token_totals["input_tokens"],
            "total_output_tokens": token_totals["output_tokens"],
            "total_tokens": token_totals["total_tokens"],
            "total_cached_tokens": token_totals["cached_tokens"],
            "total_reasoning_tokens": token_totals["reasoning_tokens"],
            "average_input_tokens": (token_totals["input_tokens"] / case_count) if case_count else 0.0,
            "average_output_tokens": (token_totals["output_tokens"] / case_count) if case_count else 0.0,
            "average_total_tokens": (token_totals["total_tokens"] / case_count) if case_count else 0.0,
        }

    return {
        "dataset_path": str(path),
        "provider": provider_name,
        "model": model,
        "aggregate": aggregates,
        "performance_summary": build_performance_summary(
            dataset_path=path,
            provider=provider_name,
            model=model,
            cases=cases,
            aggregates=aggregates,
        ),
        "cases": cases,
    }


def write_report(report: dict[str, Any], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_performance_summary(summary: dict[str, Any], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def build_performance_summary(
    *,
    dataset_path: str | Path,
    provider: str,
    model: str | None,
    cases: list[dict[str, Any]],
    aggregates: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_path": str(dataset_path),
        "provider": provider,
        "model": model,
        "aggregate": aggregates,
        "cases": [
            {
                "id": case["id"],
                "question": case["question"],
                "gold_answer": case["gold_answer"],
                "conditions": [
                    {
                        "name": condition["name"],
                        "correct": condition["correct"],
                        "predicted": condition["predicted"],
                        "gold": condition["gold"],
                        "iterations": condition["iterations"],
                        "latency_seconds": condition["latency_seconds"],
                        "token_counts": condition["token_counts"],
                    }
                    for condition in case["conditions"]
                ],
            }
            for case in cases
        ],
    }


def _load_dataset(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _maybe_get_gold_logical_form(case: dict[str, Any], field: str) -> dict[str, Any] | None:
    if field not in case:
        return None
    return canonicalize_logical_form(case[field])


def _normalize_token_counts(usage: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(usage, dict):
        return _empty_token_counts()
    return {
        "input_tokens": int(usage.get("input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
        "cached_tokens": int(usage.get("cached_tokens", 0) or 0),
        "reasoning_tokens": int(usage.get("reasoning_tokens", 0) or 0),
    }


def _empty_token_counts() -> dict[str, int]:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
        "reasoning_tokens": 0,
    }
