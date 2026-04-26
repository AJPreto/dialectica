"""Diagnostic benchmark comparison for Dialectica reasoning paths."""

from __future__ import annotations

import json
import time
from pathlib import Path
from statistics import mean
from typing import Any

from .canonical import canonicalize_logical_form
from .compiler import compile_hybrid_document, compiled_document_to_dict
from .engine import ReasoningResult, reason_over_fol_program, reason_over_horn_program
from .explainer import explain_fol_reasoning, explain_reasoning
from .filtering import filter_logical_form
from .fingerprint import fingerprint_logical_form
from .ir import Atom, HybridDocument, Negation
from .parser import parse_document, parse_text
from .prompting import (
    build_dialectica_compact_prompt,
    build_dialectica_structural_compact_prompt,
    build_direct_prompt,
)
from .providers import build_provider
from .reporting import DISPLAY_LABELS
from .scoring import extract_answer_payload, score_answer
from .translator import translate_text


MODEL_MODES = (
    "direct",
    "dialectica_compact",
    "dialectica_filtered",
    "dialectica_filtered_structural",
)
DEFAULT_MODE_ORDER = [*MODEL_MODES, "horn_reasoner", "fol_reasoner"]
EXPORT_TARGETS = ("horn", "fol", "smt")
DIAGNOSTIC_CATEGORY_MAP = {
    "contradiction_sensitivity": "contradiction_detection",
    "negation_handling_score": "negation",
    "exception_handling_score": "conditions_exceptions",
}


def evaluate_reasoning_comparison(
    path: str | Path,
    provider_name: str,
    model: str | None = None,
) -> dict[str, Any]:
    dataset = _load_dataset(path)
    provider = build_provider(provider_name, model=model)
    cases: list[dict[str, Any]] = []
    condition_buckets: dict[str, list[dict[str, Any]]] = {mode: [] for mode in DEFAULT_MODE_ORDER}

    for raw_case in dataset:
        case = _normalize_case(raw_case)
        context_form = canonicalize_logical_form(parse_document(case["context"], language=case["language"]))
        question_form = canonicalize_logical_form(parse_text(case["question"], language=case["language"]))
        filtered_context_form = filter_logical_form(context_form, question_form)
        filtered_context_fingerprint = fingerprint_logical_form(filtered_context_form)
        question_fingerprint = fingerprint_logical_form(question_form)

        conditions = [
            _run_model_condition(
                provider=provider,
                case=case,
                name="direct",
                prompt_builder=lambda: build_direct_prompt(case),
            ),
            _run_model_condition(
                provider=provider,
                case=case,
                name="dialectica_compact",
                prompt_builder=lambda: build_dialectica_compact_prompt(case, context_form, question_form),
            ),
            _run_model_condition(
                provider=provider,
                case=case,
                name="dialectica_filtered",
                prompt_builder=lambda: build_dialectica_compact_prompt(case, filtered_context_form, question_form),
            ),
            _run_model_condition(
                provider=provider,
                case=case,
                name="dialectica_filtered_structural",
                prompt_builder=lambda: build_dialectica_structural_compact_prompt(
                    case,
                    filtered_context_form,
                    question_form,
                    filtered_context_fingerprint,
                    question_fingerprint,
                ),
            ),
            _run_horn_reasoner_condition(case),
            _run_fol_reasoner_condition(case),
        ]
        for result in conditions:
            result["expected_reasoning_depth"] = case["expected_reasoning_depth"]

        for result in conditions:
            condition_buckets.setdefault(result["name"], []).append(result)

        cases.append(
            {
                "id": case["id"],
                "context": case["context"],
                "question": case["question"],
                "gold_answer": case["gold_answer"],
                "answer_type": case["answer_type"],
                "choices": case["choices"],
                "difficulty": case["difficulty"],
                "category": case["category"],
                "categories": case["categories"],
                "paraphrase_group": case["paraphrase_group"],
                "phenomena": case["phenomena"],
                "expectations": {
                    "expected_answer": case["expected_answer"],
                    "expected_horn_answer": case["expected_horn_answer"],
                    "expected_inference_success": case["expected_inference_success"],
                    "expected_contradiction_flag": case["expected_contradiction_flag"],
                    "expected_exportability": case["expected_exportability"],
                    "expected_reasoning_depth": case["expected_reasoning_depth"],
                    "expected_failure_mode": case["expected_failure_mode"],
                    "expected_behavior": case["expected_behavior"],
                },
                "conditions": conditions,
            }
        )

    aggregate = {
        name: _aggregate_condition(results)
        for name, results in condition_buckets.items()
        if results
    }
    category_summary = _summarize_categories(cases)
    difficulty_summary = _summarize_scalar_groups(cases, field="difficulty")
    reasoning_depth_summary = _summarize_scalar_groups(cases, field="expected_reasoning_depth")
    diagnostics = _build_diagnostics(cases, aggregate)
    comparison_table = _build_comparison_table(aggregate, diagnostics)
    error_report = _build_error_report(cases)

    return {
        "dataset_path": str(path),
        "provider": provider_name,
        "model": model,
        "mode_order": _ordered_modes(aggregate),
        "aggregate": aggregate,
        "category_summary": category_summary,
        "difficulty_summary": difficulty_summary,
        "reasoning_depth_summary": reasoning_depth_summary,
        "diagnostics": diagnostics,
        "comparison_table": comparison_table,
        "error_report": error_report,
        "cases": cases,
    }


def write_reasoning_report(report: dict[str, Any], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _load_dataset(path: str | Path) -> list[dict[str, Any]]:
    dataset_path = Path(path)
    try:
        with dataset_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in reasoning benchmark dataset {dataset_path}: {exc.msg}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"Reasoning benchmark dataset {dataset_path} must be a JSON array of case objects.")
    for index, case in enumerate(payload, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Reasoning benchmark dataset {dataset_path} case {index} must be an object.")
        if "id" not in case:
            raise ValueError(f"Reasoning benchmark dataset {dataset_path} case {index} is missing required field 'id'.")
    return payload


def _normalize_case(raw_case: dict[str, Any]) -> dict[str, Any]:
    categories = raw_case.get("categories")
    if isinstance(categories, list) and categories:
        normalized_categories = [str(item) for item in categories]
    elif raw_case.get("category"):
        normalized_categories = [str(raw_case["category"])]
    elif raw_case.get("phenomena"):
        normalized_categories = [str(item) for item in raw_case["phenomena"]]
    else:
        normalized_categories = ["uncategorized"]

    gold_answer = str(raw_case.get("gold_answer", ""))
    expected_answer = str(raw_case.get("expected_answer", gold_answer))
    expected_inference_success = bool(raw_case.get("expected_inference_success", True))
    expected_horn_answer = str(
        raw_case.get(
            "expected_horn_answer",
            "entailed" if expected_answer.casefold() in {"yes", "true", "1"} and expected_inference_success else "not_entailed",
        )
    )
    expected_exportability = {
        str(target): str(status)
        for target, status in (raw_case.get("expected_exportability") or {}).items()
    }

    return {
        "id": str(raw_case["id"]),
        "context": str(raw_case.get("context", "")),
        "question": str(raw_case.get("question", "")),
        "gold_answer": gold_answer,
        "expected_answer": expected_answer,
        "answer_type": str(raw_case.get("answer_type", "boolean")),
        "choices": [str(choice) for choice in raw_case.get("choices", [])],
        "language": str(raw_case.get("language", "en")),
        "difficulty": str(raw_case.get("difficulty", "unspecified")),
        "category": str(raw_case.get("category", normalized_categories[0])),
        "categories": normalized_categories,
        "paraphrase_group": raw_case.get("paraphrase_group"),
        "phenomena": [str(item) for item in raw_case.get("phenomena", [])],
        "expected_horn_answer": expected_horn_answer,
        "expected_inference_success": expected_inference_success,
        "expected_contradiction_flag": bool(raw_case.get("expected_contradiction_flag", False)),
        "expected_exportability": expected_exportability,
        "expected_reasoning_depth": int(raw_case.get("expected_reasoning_depth", 0) or 0),
        "expected_failure_mode": raw_case.get("expected_failure_mode"),
        "expected_behavior": str(raw_case.get("expected_behavior", "")),
    }


def _run_model_condition(
    *,
    provider,
    case: dict[str, Any],
    name: str,
    prompt_builder,
) -> dict[str, Any]:
    instructions, prompt = prompt_builder()
    response = provider.generate(
        instructions,
        prompt,
        metadata={"gold_answer": case["gold_answer"], "case_id": case["id"], "condition": name},
    )
    payload = extract_answer_payload(response.text)
    score = score_answer(payload["answer"], case["gold_answer"], case["answer_type"], choices=case.get("choices"))
    usage = response.usage or {}
    return {
        "name": name,
        "label": DISPLAY_LABELS.get(name, name.replace("_", " ").title()),
        "answer": payload["answer"],
        "justification": payload["justification"],
        "correct": bool(score["correct"]),
        "predicted": score["predicted"],
        "gold": score["gold"],
        "latency_seconds": float(response.latency_seconds),
        "iterations": int(response.iterations),
        "token_counts": {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
            "cached_tokens": int(usage.get("cached_tokens", 0) or 0),
            "reasoning_tokens": int(usage.get("reasoning_tokens", 0) or 0),
        },
        "prompt_characters": len(prompt),
        "prompt_words": len(prompt.split()),
        "instructions_characters": len(instructions),
        "instructions_words": len(instructions.split()),
    }


def _run_horn_reasoner_condition(case: dict[str, Any]) -> dict[str, Any]:
    started_at = time.perf_counter()
    document = translate_text(case["context"], query=case["question"])
    compiled_document, compiled = compile_hybrid_document(document)
    reasoning = reason_over_horn_program(compiled["horn"]["artifact"])
    explanation = explain_reasoning(compiled_document, reasoning)
    normalized_answer = _normalize_reasoner_answer(reasoning.answer, answer_type=case["answer_type"])
    score = score_answer(normalized_answer, case["gold_answer"], case["answer_type"], choices=case.get("choices"))
    compiled_statuses = {target: str(compiled.get(target, {}).get("status", "unsupported")) for target in EXPORT_TARGETS}
    contradiction = _detect_contradictions(compiled_document)
    explanation_proxy = _score_explanation_proxy(
        compiled_document=compiled_document,
        reasoning=reasoning,
        explanation=explanation,
        horn_status=compiled_statuses["horn"],
    )
    exportability_match = {
        target: (
            compiled_statuses[target] == case["expected_exportability"].get(target)
            if case["expected_exportability"].get(target) is not None
            else None
        )
        for target in EXPORT_TARGETS
    }
    return {
        "name": "horn_reasoner",
        "label": DISPLAY_LABELS.get("horn_reasoner", "Horn Reasoner"),
        "answer": normalized_answer,
        "raw_reasoning_answer": reasoning.answer,
        "correct": bool(score["correct"]),
        "predicted": score["predicted"],
        "gold": score["gold"],
        "latency_seconds": round(time.perf_counter() - started_at, 6),
        "iterations": 1,
        "token_counts": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cached_tokens": 0, "reasoning_tokens": 0},
        "reasoning_depth_observed": len(reasoning.trace),
        "reasoning": reasoning.to_dict(),
        "compiled": {
            "statuses": compiled_statuses,
            "notes": {target: compiled.get(target, {}).get("notes", []) for target in EXPORT_TARGETS},
            "statement_exportability": _summarize_statement_exportability(compiled_document),
        },
        "contradiction": contradiction,
        "explanation": explanation,
        "explanation_proxy": explanation_proxy,
        "expected_match": {
            "horn_answer": reasoning.answer == case["expected_horn_answer"],
            "contradiction_flag": contradiction["flag"] == case["expected_contradiction_flag"],
            "exportability": exportability_match,
        },
        "hybrid_document": compiled_document_to_dict(compiled_document),
    }


def _run_fol_reasoner_condition(case: dict[str, Any]) -> dict[str, Any]:
    started_at = time.perf_counter()
    document = translate_text(case["context"], query=case["question"])
    compiled_document, compiled = compile_hybrid_document(document)
    reasoning = reason_over_fol_program(compiled["fol"]["artifact"].get("program", {}))
    explanation = explain_fol_reasoning(compiled_document, reasoning)
    normalized_answer = _normalize_reasoner_answer(reasoning.answer, answer_type=case["answer_type"])
    score = score_answer(normalized_answer, case["gold_answer"], case["answer_type"], choices=case.get("choices"))
    compiled_statuses = {target: str(compiled.get(target, {}).get("status", "unsupported")) for target in EXPORT_TARGETS}
    contradiction = _detect_contradictions(compiled_document)
    return {
        "name": "fol_reasoner",
        "label": DISPLAY_LABELS.get("fol_reasoner", "FOL Reasoner"),
        "answer": normalized_answer,
        "raw_reasoning_answer": reasoning.answer,
        "correct": bool(score["correct"]),
        "predicted": score["predicted"],
        "gold": score["gold"],
        "latency_seconds": round(time.perf_counter() - started_at, 6),
        "iterations": 1,
        "token_counts": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cached_tokens": 0, "reasoning_tokens": 0},
        "reasoning_depth_observed": len(reasoning.trace),
        "reasoning": reasoning.to_dict(),
        "compiled": {
            "statuses": compiled_statuses,
            "notes": {target: compiled.get(target, {}).get("notes", []) for target in EXPORT_TARGETS},
            "statement_exportability": _summarize_statement_exportability(compiled_document),
        },
        "contradiction": contradiction,
        "explanation": explanation,
        "hybrid_document": compiled_document_to_dict(compiled_document),
    }


def _normalize_reasoner_answer(answer: str, *, answer_type: str) -> str:
    if answer_type == "boolean":
        return "yes" if answer == "entailed" else "no"
    if answer_type == "ternary":
        if answer == "entailed":
            return "yes"
        if answer == "refuted":
            return "no"
        return "unknown"
    return answer


def _aggregate_condition(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {}
    correct_flags = [1.0 if item.get("correct") else 0.0 for item in results]
    latencies = [float(item.get("latency_seconds", 0.0) or 0.0) for item in results]
    total_tokens = [int(item.get("token_counts", {}).get("total_tokens", 0) or 0) for item in results]
    reasoning_depths = [
        float(item.get("expected_reasoning_depth", 0.0) or 0.0)
        for item in results
        if item.get("correct")
    ]
    return {
        "accuracy": _safe_mean(correct_flags),
        "average_latency_seconds": _safe_mean(latencies),
        "average_total_tokens": _safe_mean(total_tokens),
        "case_count": len(results),
        "average_reasoning_depth_solved": _safe_mean(reasoning_depths),
    }


def _summarize_categories(cases: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for case in cases:
        for category in case.get("categories", []):
            bucket = summary.setdefault(category, _new_group_bucket())
            _update_group_bucket(bucket, case)
    return {category: _finalize_group_bucket(bucket) for category, bucket in sorted(summary.items())}


def _summarize_scalar_groups(cases: list[dict[str, Any]], *, field: str) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for case in cases:
        key = str(case.get("expectations", {}).get(field, case.get(field, "unspecified")))
        bucket = summary.setdefault(key, _new_group_bucket())
        _update_group_bucket(bucket, case)
    sort_key = (lambda item: int(item[0])) if field == "expected_reasoning_depth" else (lambda item: item[0])
    return {key: _finalize_group_bucket(bucket) for key, bucket in sorted(summary.items(), key=sort_key)}


def _new_group_bucket() -> dict[str, Any]:
    return {
        "case_count": 0,
        "modes": {},
    }


def _update_group_bucket(bucket: dict[str, Any], case: dict[str, Any]) -> None:
    bucket["case_count"] += 1
    expected_depth = int(case.get("expectations", {}).get("expected_reasoning_depth", 0) or 0)
    for condition in case.get("conditions", []):
        mode_bucket = bucket["modes"].setdefault(condition["name"], _new_mode_bucket())
        mode_bucket["correct"].append(1.0 if condition.get("correct") else 0.0)
        mode_bucket["latency"].append(float(condition.get("latency_seconds", 0.0) or 0.0))
        mode_bucket["tokens"].append(float(condition.get("token_counts", {}).get("total_tokens", 0) or 0.0))
        if condition.get("correct"):
            mode_bucket["depths"].append(float(expected_depth))


def _new_mode_bucket() -> dict[str, list[float]]:
    return {
        "correct": [],
        "latency": [],
        "tokens": [],
        "depths": [],
    }


def _finalize_group_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    modes = {
        mode: {
            "accuracy": _safe_mean(values["correct"]),
            "average_latency_seconds": _safe_mean(values["latency"]),
            "average_total_tokens": _safe_mean(values["tokens"]),
            "average_reasoning_depth_solved": _safe_mean(values["depths"]),
        }
        for mode, values in bucket.get("modes", {}).items()
    }
    return {
        "case_count": bucket.get("case_count", 0),
        "modes": modes,
    }


def _build_diagnostics(cases: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    diagnostics = {
        "category_wise_accuracy": _category_accuracy_snapshot(cases),
        "difficulty_wise_accuracy": _difficulty_accuracy_snapshot(cases),
        "paraphrase_stability": _paraphrase_stability(cases),
        "export_success_rate": _export_success_rate(cases),
        "explanation_faithfulness_proxy": _explanation_faithfulness_proxy(cases),
        "partial_formalization_correctness": _partial_formalization_correctness(cases),
        "average_reasoning_depth_handled": _average_reasoning_depth_handled(cases, aggregate),
    }
    for diagnostic_name, category_name in DIAGNOSTIC_CATEGORY_MAP.items():
        diagnostics[diagnostic_name] = _subset_accuracy(cases, category_name)
    diagnostics["contradiction_sensitivity"]["horn_reasoner_flag_match_rate"] = _contradiction_flag_match_rate(cases)
    diagnostics["contradiction_sensitivity"]["horn_reasoner_false_positive_rate"] = _contradiction_false_positive_rate(cases)
    return diagnostics


def _category_accuracy_snapshot(cases: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot: dict[str, dict[str, list[float]]] = {}
    for case in cases:
        for category in case.get("categories", []):
            bucket = snapshot.setdefault(category, {})
            for condition in case.get("conditions", []):
                bucket.setdefault(condition["name"], []).append(1.0 if condition.get("correct") else 0.0)
    return {
        category: {
            mode: _safe_mean(values)
            for mode, values in sorted(mode_buckets.items(), key=lambda item: _mode_sort_key(item[0]))
        }
        for category, mode_buckets in sorted(snapshot.items())
    }


def _difficulty_accuracy_snapshot(cases: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot: dict[str, dict[str, list[float]]] = {}
    for case in cases:
        bucket = snapshot.setdefault(str(case.get("difficulty", "unspecified")), {})
        for condition in case.get("conditions", []):
            bucket.setdefault(condition["name"], []).append(1.0 if condition.get("correct") else 0.0)
    return {
        difficulty: {
            mode: _safe_mean(values)
            for mode, values in sorted(mode_buckets.items(), key=lambda item: _mode_sort_key(item[0]))
        }
        for difficulty, mode_buckets in sorted(snapshot.items())
    }


def _subset_accuracy(cases: list[dict[str, Any]], category_name: str) -> dict[str, Any]:
    subset = [case for case in cases if category_name in case.get("categories", [])]
    if not subset:
        return {"case_count": 0, "modes": {}}
    mode_scores: dict[str, list[float]] = {}
    for case in subset:
        for condition in case.get("conditions", []):
            mode_scores.setdefault(condition["name"], []).append(1.0 if condition.get("correct") else 0.0)
    return {
        "case_count": len(subset),
        "modes": {
            mode: {"accuracy": _safe_mean(values)}
            for mode, values in sorted(mode_scores.items(), key=lambda item: _mode_sort_key(item[0]))
        },
    }


def _paraphrase_stability(cases: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        group = case.get("paraphrase_group")
        if not group:
            continue
        groups.setdefault(str(group), []).append(case)

    group_results: dict[str, Any] = {}
    mode_totals: dict[str, dict[str, float]] = {}
    for group_name, group_cases in sorted(groups.items()):
        if len(group_cases) < 2:
            continue
        mode_details: dict[str, Any] = {}
        for mode in _ordered_modes({mode: {} for mode in DEFAULT_MODE_ORDER}):
            predictions = []
            correctness = []
            for case in group_cases:
                condition = _condition_map(case).get(mode)
                if condition is None:
                    continue
                predictions.append(condition.get("predicted"))
                correctness.append(bool(condition.get("correct")))
            if not predictions:
                continue
            stable = len({repr(item) for item in predictions}) == 1
            stable_and_correct = stable and all(correctness)
            mode_details[mode] = {
                "stable": stable,
                "stable_and_correct": stable_and_correct,
                "predictions": predictions,
            }
            totals = mode_totals.setdefault(mode, {"groups": 0.0, "stable": 0.0, "stable_and_correct": 0.0})
            totals["groups"] += 1.0
            totals["stable"] += 1.0 if stable else 0.0
            totals["stable_and_correct"] += 1.0 if stable_and_correct else 0.0
        group_results[group_name] = {
            "case_ids": [case["id"] for case in group_cases],
            "modes": mode_details,
        }

    mode_summary = {
        mode: {
            "group_count": int(values["groups"]),
            "stable_group_rate": round(values["stable"] / values["groups"], 6) if values["groups"] else 0.0,
            "stable_and_correct_group_rate": round(values["stable_and_correct"] / values["groups"], 6)
            if values["groups"]
            else 0.0,
        }
        for mode, values in sorted(mode_totals.items(), key=lambda item: _mode_sort_key(item[0]))
    }
    return {"groups": group_results, "modes": mode_summary}


def _export_success_rate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = {target: {"exact": 0, "partial": 0, "lossy": 0, "unsupported": 0} for target in EXPORT_TARGETS}
    match_counts = {target: {"matched": 0, "expected": 0} for target in EXPORT_TARGETS}
    for case in cases:
        horn_reasoner = _condition_map(case).get("horn_reasoner")
        if horn_reasoner is None:
            continue
        statuses = horn_reasoner.get("compiled", {}).get("statuses", {})
        expected = case.get("expectations", {}).get("expected_exportability", {})
        for target in EXPORT_TARGETS:
            status = str(statuses.get(target, "unsupported"))
            status_counts[target][status] = status_counts[target].get(status, 0) + 1
            if target in expected:
                match_counts[target]["expected"] += 1
                if status == expected[target]:
                    match_counts[target]["matched"] += 1
    return {
        "by_target": {
            target: {
                "exact_rate": _rate(counts["exact"], sum(counts.values())),
                "partial_rate": _rate(counts["partial"], sum(counts.values())),
                "lossy_rate": _rate(counts["lossy"], sum(counts.values())),
                "unsupported_rate": _rate(counts["unsupported"], sum(counts.values())),
                "expectation_match_rate": _rate(match_counts[target]["matched"], match_counts[target]["expected"]),
            }
            for target, counts in status_counts.items()
        }
    }


def _explanation_faithfulness_proxy(cases: list[dict[str, Any]]) -> dict[str, Any]:
    passes = []
    check_totals: dict[str, list[float]] = {}
    for case in cases:
        horn_reasoner = _condition_map(case).get("horn_reasoner")
        if horn_reasoner is None:
            continue
        proxy = horn_reasoner.get("explanation_proxy", {})
        passes.append(1.0 if proxy.get("passed") else 0.0)
        for check in proxy.get("checks", []):
            if not check.get("applicable"):
                continue
            check_totals.setdefault(check["name"], []).append(1.0 if check.get("passed") else 0.0)
    return {
        "horn_reasoner": {
            "pass_rate": _safe_mean(passes),
            "checks": {name: _safe_mean(values) for name, values in sorted(check_totals.items())},
        }
    }


def _partial_formalization_correctness(cases: list[dict[str, Any]]) -> dict[str, Any]:
    subset = [
        case
        for case in cases
        if case.get("expectations", {}).get("expected_exportability", {}).get("horn") in {"partial", "unsupported"}
    ]
    if not subset:
        return {"case_count": 0, "modes": {}, "horn_reasoner": {}}

    mode_scores: dict[str, list[float]] = {}
    export_matches = []
    explanation_matches = []
    for case in subset:
        condition_map = _condition_map(case)
        for mode, condition in condition_map.items():
            mode_scores.setdefault(mode, []).append(1.0 if condition.get("correct") else 0.0)
        horn_reasoner = condition_map.get("horn_reasoner")
        if horn_reasoner is not None:
            expected_status = case["expectations"]["expected_exportability"].get("horn")
            actual_status = horn_reasoner.get("compiled", {}).get("statuses", {}).get("horn")
            export_matches.append(1.0 if actual_status == expected_status else 0.0)
            explanation_matches.append(1.0 if horn_reasoner.get("explanation_proxy", {}).get("passed") else 0.0)

    return {
        "case_count": len(subset),
        "modes": {
            mode: {"accuracy": _safe_mean(values)}
            for mode, values in sorted(mode_scores.items(), key=lambda item: _mode_sort_key(item[0]))
        },
        "horn_reasoner": {
            "export_expectation_match_rate": _safe_mean(export_matches),
            "explanation_proxy_rate": _safe_mean(explanation_matches),
        },
    }


def _average_reasoning_depth_handled(cases: list[dict[str, Any]], aggregate: dict[str, Any]) -> dict[str, Any]:
    mode_depths: dict[str, list[float]] = {mode: [] for mode in aggregate}
    for case in cases:
        expected_depth = float(case.get("expectations", {}).get("expected_reasoning_depth", 0) or 0)
        for condition in case.get("conditions", []):
            if condition.get("correct"):
                mode_depths.setdefault(condition["name"], []).append(expected_depth)
    return {
        "modes": {
            mode: {
                "average_depth": _safe_mean(depths),
                "max_depth": max(depths, default=0.0),
            }
            for mode, depths in sorted(mode_depths.items(), key=lambda item: _mode_sort_key(item[0]))
        }
    }


def _contradiction_flag_match_rate(cases: list[dict[str, Any]]) -> float:
    values = []
    for case in cases:
        horn_reasoner = _condition_map(case).get("horn_reasoner")
        if horn_reasoner is None:
            continue
        expected = bool(case.get("expectations", {}).get("expected_contradiction_flag", False))
        actual = bool(horn_reasoner.get("contradiction", {}).get("flag", False))
        values.append(1.0 if actual == expected else 0.0)
    return _safe_mean(values)


def _contradiction_false_positive_rate(cases: list[dict[str, Any]]) -> float:
    negatives = []
    for case in cases:
        if case.get("expectations", {}).get("expected_contradiction_flag"):
            continue
        horn_reasoner = _condition_map(case).get("horn_reasoner")
        if horn_reasoner is None:
            continue
        negatives.append(1.0 if horn_reasoner.get("contradiction", {}).get("flag") else 0.0)
    return _safe_mean(negatives)


def _build_comparison_table(aggregate: dict[str, Any], diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
    table = []
    paraphrase = diagnostics.get("paraphrase_stability", {}).get("modes", {})
    negation = diagnostics.get("negation_handling_score", {}).get("modes", {})
    exceptions = diagnostics.get("exception_handling_score", {}).get("modes", {})
    contradiction = diagnostics.get("contradiction_sensitivity", {}).get("modes", {})
    depths = diagnostics.get("average_reasoning_depth_handled", {}).get("modes", {})
    export_rates = diagnostics.get("export_success_rate", {}).get("by_target", {})

    for mode in _ordered_modes(aggregate):
        current = aggregate.get(mode, {})
        row = {
            "mode": mode,
            "label": DISPLAY_LABELS.get(mode, mode.replace("_", " ").title()),
            "accuracy": current.get("accuracy", 0.0),
            "average_total_tokens": current.get("average_total_tokens", 0.0),
            "average_latency_seconds": current.get("average_latency_seconds", 0.0),
            "negation_score": negation.get(mode, {}).get("accuracy"),
            "exception_score": exceptions.get(mode, {}).get("accuracy"),
            "contradiction_score": contradiction.get(mode, {}).get("accuracy"),
            "paraphrase_stability": paraphrase.get(mode, {}).get("stable_group_rate"),
            "average_reasoning_depth_solved": depths.get(mode, {}).get("average_depth"),
        }
        if mode == "horn_reasoner":
            row["horn_export_match_rate"] = export_rates.get("horn", {}).get("expectation_match_rate")
            row["explanation_proxy_rate"] = diagnostics.get("explanation_faithfulness_proxy", {}).get("horn_reasoner", {}).get(
                "pass_rate"
            )
        table.append(row)
    return table


def _build_error_report(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for case in cases:
        for condition in case.get("conditions", []):
            if condition.get("correct"):
                continue
            entry = {
                "case_id": case.get("id"),
                "mode": condition.get("name"),
                "category": case.get("category"),
                "categories": case.get("categories", []),
                "difficulty": case.get("difficulty"),
                "question": case.get("question"),
                "predicted": condition.get("predicted"),
                "gold": condition.get("gold"),
                "expected_failure_mode": case.get("expectations", {}).get("expected_failure_mode"),
                "expected_behavior": case.get("expectations", {}).get("expected_behavior"),
            }
            if condition.get("name") == "horn_reasoner":
                entry["raw_reasoning_answer"] = condition.get("raw_reasoning_answer")
                entry["horn_status"] = condition.get("compiled", {}).get("statuses", {}).get("horn")
                entry["contradiction_flag"] = condition.get("contradiction", {}).get("flag")
                entry["explanation_proxy_passed"] = condition.get("explanation_proxy", {}).get("passed")
            errors.append(entry)
    return errors


def _summarize_statement_exportability(document: HybridDocument) -> dict[str, Any]:
    summary: dict[str, dict[str, int]] = {}
    for statement in document.statements:
        for target, record in statement.exportability.items():
            target_bucket = summary.setdefault(target, {})
            target_bucket[record.status] = target_bucket.get(record.status, 0) + 1
    return summary


def _detect_contradictions(document: HybridDocument) -> dict[str, Any]:
    positive_atoms: dict[tuple[str, tuple[str, ...]], Atom] = {}
    negative_atoms: dict[tuple[str, tuple[str, ...]], Atom] = {}
    for statement in document.statements:
        if statement.kind != "fact" or statement.formal_core is None:
            continue
        if isinstance(statement.formal_core, Atom):
            positive_atoms[_atom_key(statement.formal_core)] = statement.formal_core
        elif isinstance(statement.formal_core, Negation) and isinstance(statement.formal_core.operand, Atom):
            negative_atoms[_atom_key(statement.formal_core.operand)] = statement.formal_core.operand

    conflicting = sorted(set(positive_atoms) & set(negative_atoms))
    return {
        "flag": bool(conflicting),
        "pairs": [_atom_key_to_text(key) for key in conflicting],
    }


def _score_explanation_proxy(
    *,
    compiled_document: HybridDocument,
    reasoning: ReasoningResult,
    explanation: str,
    horn_status: str,
) -> dict[str, Any]:
    lower_explanation = explanation.casefold()
    checks = []

    trace_required = bool(reasoning.trace)
    checks.append(
        {
            "name": "trace_section_present",
            "applicable": trace_required,
            "passed": (not trace_required) or ("derivation trace:" in lower_explanation),
        }
    )
    for step in reasoning.trace:
        checks.append(
            {
                "name": f"trace_mentions_{step.derived.predicate}",
                "applicable": True,
                "passed": step.derived.predicate.casefold() in lower_explanation,
            }
        )

    blocked_required = bool(reasoning.blocked)
    checks.append(
        {
            "name": "blocked_section_present",
            "applicable": blocked_required,
            "passed": (not blocked_required) or ("blocked rule applications:" in lower_explanation),
        }
    )

    residue_required = horn_status in {"partial", "unsupported"} or any(
        not statement.semantic_residue.is_empty() for statement in compiled_document.statements
    )
    checks.append(
        {
            "name": "residue_or_withholding_acknowledged",
            "applicable": residue_required,
            "passed": (not residue_required)
            or any(token in lower_explanation for token in ("residue", "withheld", "unformalized", "preserved outside")),
        }
    )

    notes_required = bool(reasoning.notes)
    checks.append(
        {
            "name": "engine_notes_acknowledged",
            "applicable": notes_required,
            "passed": (not notes_required) or ("engine notes:" in lower_explanation),
        }
    )

    applicable = [check for check in checks if check["applicable"]]
    passed = all(check["passed"] for check in applicable) if applicable else True
    return {"passed": passed, "checks": checks}


def _condition_map(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {condition["name"]: condition for condition in case.get("conditions", [])}


def _atom_key(atom: Atom) -> tuple[str, tuple[str, ...]]:
    return atom.predicate, tuple(_term_value(argument) for argument in atom.arguments)


def _term_value(term: Any) -> str:
    if hasattr(term, "name"):
        return str(term.name)
    if hasattr(term, "value"):
        return str(term.value)
    return str(term)


def _atom_key_to_text(key: tuple[str, tuple[str, ...]]) -> str:
    predicate, arguments = key
    if not arguments:
        return predicate
    return f"{predicate}({', '.join(arguments)})"


def _ordered_modes(aggregate: dict[str, Any]) -> list[str]:
    present = [mode for mode in DEFAULT_MODE_ORDER if mode in aggregate]
    present.extend(sorted(mode for mode in aggregate if mode not in present))
    return present


def _mode_sort_key(mode: str) -> tuple[int, str]:
    try:
        return DEFAULT_MODE_ORDER.index(mode), mode
    except ValueError:
        return len(DEFAULT_MODE_ORDER), mode


def _safe_mean(values: list[float] | list[int]) -> float:
    return round(mean(values), 6) if values else 0.0


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)
