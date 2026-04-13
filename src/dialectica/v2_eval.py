"""Lightweight benchmark comparison for V1 prompting versus the experimental V2 path."""

from __future__ import annotations

import json
import time
from pathlib import Path
from statistics import mean
from typing import Any

from .canonical import canonicalize_logical_form
from .compiler import compile_hybrid_document, compiled_document_to_dict
from .engine import reason_over_horn_program
from .explainer import explain_reasoning
from .filtering import filter_logical_form
from .parser import parse_document, parse_text
from .prompting import build_dialectica_compact_prompt, build_direct_prompt
from .providers import build_provider
from .scoring import extract_answer_payload, score_answer
from .translator import translate_text


def evaluate_v2_comparison(
    path: str | Path,
    provider_name: str,
    model: str | None = None,
) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)

    provider = build_provider(provider_name, model=model)
    cases: list[dict[str, Any]] = []
    aggregates: dict[str, list[dict[str, Any]]] = {
        "direct": [],
        "dialectica_filtered": [],
        "v2_horn": [],
    }

    for case in dataset:
        context = str(case.get("context", ""))
        question = str(case.get("question", ""))
        answer_type = str(case.get("answer_type", "boolean"))
        language = str(case.get("language", "en"))

        context_form = canonicalize_logical_form(parse_document(context, language=language))
        question_form = canonicalize_logical_form(parse_text(question, language=language))
        filtered_context = filter_logical_form(context_form, question_form)

        direct = _run_model_condition(
            provider=provider,
            case=case,
            name="direct",
            prompt_builder=lambda: build_direct_prompt(case),
            answer_type=answer_type,
        )
        filtered = _run_model_condition(
            provider=provider,
            case=case,
            name="dialectica_filtered",
            prompt_builder=lambda: build_dialectica_compact_prompt(case, filtered_context, question_form),
            answer_type=answer_type,
        )
        v2_horn = _run_v2_horn_condition(case, answer_type=answer_type)

        aggregates["direct"].append(direct)
        aggregates["dialectica_filtered"].append(filtered)
        aggregates["v2_horn"].append(v2_horn)
        cases.append(
            {
                "id": case["id"],
                "context": context,
                "question": question,
                "gold_answer": case.get("gold_answer"),
                "phenomena": case.get("phenomena", []),
                "conditions": [direct, filtered, v2_horn],
            }
        )

    return {
        "dataset_path": str(path),
        "provider": provider_name,
        "model": model,
        "aggregate": {name: _aggregate_condition(values) for name, values in aggregates.items()},
        "cases": cases,
    }


def write_v2_report(report: dict[str, Any], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _run_model_condition(
    *,
    provider,
    case: dict[str, Any],
    name: str,
    prompt_builder,
    answer_type: str,
) -> dict[str, Any]:
    instructions, prompt = prompt_builder()
    response = provider.generate(
        instructions,
        prompt,
        metadata={"gold_answer": case.get("gold_answer"), "case_id": case.get("id"), "condition": name},
    )
    payload = extract_answer_payload(response.text)
    score = score_answer(payload["answer"], case.get("gold_answer"), answer_type, choices=case.get("choices"))
    usage = response.usage or {}
    return {
        "name": name,
        "answer": payload["answer"],
        "correct": bool(score["correct"]),
        "predicted": score["predicted"],
        "gold": score["gold"],
        "latency_seconds": response.latency_seconds,
        "iterations": response.iterations,
        "token_counts": {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
        },
    }


def _run_v2_horn_condition(case: dict[str, Any], *, answer_type: str) -> dict[str, Any]:
    started_at = time.perf_counter()
    document = translate_text(str(case.get("context", "")), query=str(case.get("question", "")))
    compiled_document, compiled = compile_hybrid_document(document)
    reasoning = reason_over_horn_program(compiled["horn"]["artifact"])
    explanation = explain_reasoning(compiled_document, reasoning)
    normalized_answer = _normalize_v2_answer(reasoning.answer, answer_type=answer_type)
    score = score_answer(normalized_answer, case.get("gold_answer"), answer_type, choices=case.get("choices"))
    return {
        "name": "v2_horn",
        "answer": normalized_answer,
        "correct": bool(score["correct"]),
        "predicted": score["predicted"],
        "gold": score["gold"],
        "latency_seconds": time.perf_counter() - started_at,
        "iterations": 1,
        "token_counts": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "reasoning": reasoning.to_dict(),
        "compiled": {
            "horn_status": compiled["horn"]["status"],
            "fol_status": compiled["fol"]["status"],
            "smt_status": compiled["smt"]["status"],
        },
        "explanation": explanation,
        "hybrid_document": compiled_document_to_dict(compiled_document),
    }


def _normalize_v2_answer(answer: str, *, answer_type: str) -> str:
    if answer_type == "boolean":
        return "yes" if answer == "entailed" else "no"
    return answer


def _aggregate_condition(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {}
    return {
        "accuracy": mean(1.0 if item["correct"] else 0.0 for item in results),
        "average_latency_seconds": mean(float(item.get("latency_seconds", 0.0) or 0.0) for item in results),
        "average_total_tokens": mean(int(item.get("token_counts", {}).get("total_tokens", 0) or 0) for item in results),
        "case_count": len(results),
    }

