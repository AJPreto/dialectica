"""Complexity-sweep benchmark generation and reporting."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from statistics import mean
from typing import Any

from .canonical import serialize_compact_logical_form, serialize_logical_form


PERSONS = [
    "Alice",
    "Bruno",
    "Carla",
    "Dorian",
    "Elena",
    "Farid",
    "Greta",
    "Hugo",
    "Ines",
    "Jonas",
    "Kira",
    "Levi",
    "Marta",
    "Nolan",
    "Opal",
    "Priya",
    "Quinn",
    "Rhea",
    "Soren",
    "Talia",
]

THEMES = [
    "amber",
    "cobalt",
    "delta",
    "ember",
    "frost",
    "granite",
    "helix",
    "ion",
    "jade",
    "kepler",
    "lumen",
    "meridian",
]

STEP_TEMPLATES = [
    "completed {theme} orientation",
    "holds a {theme} badge",
    "is cleared for the {theme} wing",
    "may enter the {theme} workshop",
    "may operate the {theme} console",
    "may access the {theme} vault",
    "may start the {theme} reactor",
    "may authorize the {theme} sequence",
]

NEGATIVE_CUES = (
    " not ",
    " never ",
    " no ",
    " cannot ",
    " can't ",
    " won't ",
    " without ",
    " fail",
)


def generate_complexity_dataset(
    *,
    levels: int = 6,
    scenarios_per_level: int = 3,
    followups: int = 3,
    seed: int = 7,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    cases: list[dict[str, Any]] = []
    scenario_counter = 0
    for level in range(1, levels + 1):
        for scenario_index in range(scenarios_per_level):
            scenario_counter += 1
            cases.extend(
                _generate_scenario_cases(
                    level=level,
                    scenario_index=scenario_index,
                    scenario_counter=scenario_counter,
                    followups=followups,
                    rng=rng,
                )
            )
    return cases


def write_complexity_dataset(dataset: list[dict[str, Any]], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dataset, indent=2), encoding="utf-8")


def summarize_complexity_report(report: dict[str, Any]) -> dict[str, Any]:
    levels: dict[int, dict[str, Any]] = {}

    for case in report.get("cases", []):
        complexity = case.get("complexity") or {}
        level = int(complexity.get("level", 0) or 0)
        bucket = levels.setdefault(level, _new_level_bucket())

        bucket["case_count"] += 1
        if case.get("scenario_id"):
            bucket["scenario_ids"].add(str(case["scenario_id"]))

        context_text = str(case.get("context", ""))
        bucket["context_characters"].append(len(context_text))
        bucket["context_words"].append(len(context_text.split()))
        bucket["context_sentence_count"].append(int(complexity.get("context_sentence_count", 0) or 0))
        bucket["chain_length"].append(int(complexity.get("chain_length", 0) or 0))
        bucket["distractor_count"].append(int(complexity.get("distractor_count", 0) or 0))
        bucket["target_depth"].append(int(complexity.get("target_depth", 0) or 0))
        bucket["followup_count"].append(int(complexity.get("followup_count", 0) or 0))

        parsed_context = case.get("parsed_context") or {}
        canonical_text = serialize_logical_form(parsed_context)
        compact_text = serialize_compact_logical_form(parsed_context)
        bucket["canonical_characters"].append(len(canonical_text))
        bucket["compact_characters"].append(len(compact_text))
        bucket["compact_smaller_than_raw"] += int(len(compact_text) < len(context_text))

        condition_lookup = {condition["name"]: condition for condition in case.get("conditions", [])}
        direct_condition = condition_lookup.get("direct")
        compact_condition = condition_lookup.get("dialectica_compact")
        if direct_condition and compact_condition:
            direct_prompt_size = _prompt_size(direct_condition)
            compact_prompt_size = _prompt_size(compact_condition)
            if compact_prompt_size < direct_prompt_size:
                bucket["compact_prompt_smaller_than_direct"] += 1

        for condition in case.get("conditions", []):
            condition_bucket = bucket["conditions"].setdefault(condition["name"], _new_condition_bucket())
            condition_bucket["accuracy"].append(1.0 if condition["correct"] else 0.0)
            condition_bucket["latency_seconds"].append(float(condition.get("latency_seconds", 0.0) or 0.0))
            condition_bucket["iterations"].append(int(condition.get("iterations", 0) or 0))
            condition_bucket["input_tokens"].append(int(condition.get("token_counts", {}).get("input_tokens", 0) or 0))
            condition_bucket["output_tokens"].append(int(condition.get("token_counts", {}).get("output_tokens", 0) or 0))
            condition_bucket["total_tokens"].append(int(condition.get("token_counts", {}).get("total_tokens", 0) or 0))
            condition_bucket["cached_tokens"].append(int(condition.get("token_counts", {}).get("cached_tokens", 0) or 0))
            condition_bucket["reasoning_tokens"].append(
                int(condition.get("token_counts", {}).get("reasoning_tokens", 0) or 0)
            )
            condition_bucket["prompt_characters"].append(_prompt_size(condition))
            condition_bucket["prompt_words"].append(
                int(condition.get("prompt_words", 0) or 0) + int(condition.get("instructions_words", 0) or 0)
            )

    finalized_levels: dict[str, Any] = {}
    representation_crossover_levels: list[int] = []
    compact_inflection_levels: list[int] = []
    structural_compact_inflection_levels: list[int] = []

    for level in sorted(levels):
        bucket = levels[level]
        case_count = bucket["case_count"]
        level_summary = {
            "case_count": case_count,
            "scenario_count": len(bucket["scenario_ids"]),
            "average_context_characters": _safe_mean(bucket["context_characters"]),
            "average_context_words": _safe_mean(bucket["context_words"]),
            "average_context_sentence_count": _safe_mean(bucket["context_sentence_count"]),
            "average_chain_length": _safe_mean(bucket["chain_length"]),
            "average_distractor_count": _safe_mean(bucket["distractor_count"]),
            "average_target_depth": _safe_mean(bucket["target_depth"]),
            "average_followup_count": _safe_mean(bucket["followup_count"]),
            "average_canonical_characters": _safe_mean(bucket["canonical_characters"]),
            "average_compact_characters": _safe_mean(bucket["compact_characters"]),
            "compact_context_smaller_than_raw_share": (
                bucket["compact_smaller_than_raw"] / case_count if case_count else 0.0
            ),
            "compact_prompt_smaller_than_direct_share": (
                bucket["compact_prompt_smaller_than_direct"] / case_count if case_count else 0.0
            ),
            "conditions": {
                name: _finalize_condition_bucket(condition_bucket)
                for name, condition_bucket in sorted(bucket["conditions"].items())
            },
        }

        direct_summary = level_summary["conditions"].get("direct")
        compact_summary = level_summary["conditions"].get("dialectica_compact")
        structural_compact_summary = level_summary["conditions"].get("dialectica_structural_compact")

        if direct_summary and compact_summary:
            level_summary["direct_vs_dialectica_compact"] = {
                "accuracy_delta": round(
                    compact_summary["accuracy"] - direct_summary["accuracy"],
                    6,
                ),
                "representation_character_delta": round(
                    level_summary["average_compact_characters"] - level_summary["average_context_characters"],
                    6,
                ),
                "average_total_token_delta": round(
                    compact_summary["average_total_tokens"] - direct_summary["average_total_tokens"],
                    6,
                ),
                "average_prompt_character_delta": round(
                    compact_summary["average_prompt_characters"] - direct_summary["average_prompt_characters"],
                    6,
                ),
            }
            if level_summary["average_compact_characters"] <= level_summary["average_context_characters"]:
                representation_crossover_levels.append(level)
            if (
                compact_summary["accuracy"] >= direct_summary["accuracy"]
                and compact_summary["average_prompt_characters"] <= direct_summary["average_prompt_characters"]
            ):
                compact_inflection_levels.append(level)

        if direct_summary and structural_compact_summary:
            level_summary["direct_vs_dialectica_structural_compact"] = {
                "accuracy_delta": round(
                    structural_compact_summary["accuracy"] - direct_summary["accuracy"],
                    6,
                ),
                "average_total_token_delta": round(
                    structural_compact_summary["average_total_tokens"] - direct_summary["average_total_tokens"],
                    6,
                ),
                "average_prompt_character_delta": round(
                    structural_compact_summary["average_prompt_characters"] - direct_summary["average_prompt_characters"],
                    6,
                ),
            }
            if (
                structural_compact_summary["accuracy"] >= direct_summary["accuracy"]
                and structural_compact_summary["average_prompt_characters"] <= direct_summary["average_prompt_characters"]
            ):
                structural_compact_inflection_levels.append(level)

        finalized_levels[str(level)] = level_summary

    return {
        "dataset_path": report.get("dataset_path"),
        "provider": report.get("provider"),
        "model": report.get("model"),
        "levels": finalized_levels,
        "candidate_representation_crossover_levels": representation_crossover_levels,
        "candidate_prompt_inflection_levels": {
            "dialectica_compact": compact_inflection_levels,
            "dialectica_structural_compact": structural_compact_inflection_levels,
        },
    }


def write_complexity_summary(summary: dict[str, Any], output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _generate_scenario_cases(
    *,
    level: int,
    scenario_index: int,
    scenario_counter: int,
    followups: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    chain_length = min(level + 1, len(STEP_TEMPLATES) - 1)
    distractor_count = max(0, level - 1)
    variant_pool = ["entails", "missing_base"]
    if level >= 3:
        variant_pool.extend(["blocked", "waived"])
    variant = variant_pool[(scenario_index + level + scenario_counter) % len(variant_pool)]

    name = _pick_unique(PERSONS, scenario_counter + scenario_index)
    theme = _pick_unique(THEMES, scenario_counter * 3 + level)
    predicates = _build_predicates(theme, chain_length)
    blocker = f"is under {theme} suspension"
    waiver = f"has a {theme} director waiver"

    core_items = _build_core_items(
        name=name,
        predicates=predicates,
        blocker=blocker,
        waiver=waiver,
        variant=variant,
        include_exception=level >= 3,
    )
    distractor_items = _build_distractor_items(
        count=distractor_count,
        scenario_counter=scenario_counter,
        level=level,
        rng=rng,
    )
    ordered_items = _interleave_items(core_items, distractor_items, rng)
    context = " ".join(item["sentence"] for item in ordered_items)

    target_indices = _select_target_indices(chain_length=chain_length, followups=followups)
    derived_states = _derive_states(predicates, variant=variant)
    gold_context_form = _build_context_logical_form(
        ordered_items,
        context=context,
        metadata={
            "generator": "complexity-sweep-v1",
            "family": "access_chain",
            "level": level,
            "variant": variant,
            "chain_length": chain_length,
            "distractor_count": distractor_count,
        },
    )

    cases: list[dict[str, Any]] = []
    for followup_index, target_depth in enumerate(target_indices, start=1):
        target_predicate = predicates[target_depth]
        question = _question_for_predicate(name, target_predicate)
        gold_answer = _gold_answer_for_target(
            target_depth=target_depth,
            chain_length=chain_length,
            derived_states=derived_states,
            final_predicate=predicates[-1],
            variant=variant,
        )
        gold_question_form = _build_question_logical_form(question)
        case_id = f"cx-{level:02d}-{scenario_counter:03d}-q{followup_index}"
        phenomena = ["condition", "multi_hop", "distractors"]
        if level >= 3:
            phenomena.extend(["exception", "negation"])
        if target_depth == chain_length:
            phenomena.append("final_goal")
        else:
            phenomena.append("followup")
        cases.append(
            {
                "id": case_id,
                "scenario_id": f"scenario-{level:02d}-{scenario_counter:03d}",
                "context": context,
                "question": question,
                "gold_answer": gold_answer,
                "answer_type": "boolean",
                "phenomena": phenomena,
                "complexity": {
                    "level": level,
                    "family": "access_chain",
                    "variant": variant,
                    "chain_length": chain_length,
                    "distractor_count": distractor_count,
                    "followup_index": followup_index,
                    "followup_count": len(target_indices),
                    "target_depth": target_depth,
                    "context_sentence_count": len(ordered_items),
                },
                "gold_blocks": [block["type"] for block in gold_context_form["blocks"]],
                "gold_relations": [relation["type"] for relation in gold_context_form["relations"]],
                "gold_logical_form": gold_context_form,
                "gold_question_logical_form": gold_question_form,
                "gold_encoding": {
                    "dialect": "fof",
                    "generator": "complexity-sweep-v1",
                    "family": "access_chain",
                    "variant": variant,
                    "level": level,
                },
            }
        )
    return cases


def _build_core_items(
    *,
    name: str,
    predicates: list[str],
    blocker: str,
    waiver: str,
    variant: str,
    include_exception: bool,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    base_predicate = predicates[0]
    if variant == "missing_base":
        items.append(_fact_item(name, base_predicate, negative=True))
    else:
        items.append(_fact_item(name, base_predicate))

    for index in range(len(predicates) - 1):
        items.append(_rule_item(name, predicates[index], predicates[index + 1]))

    if include_exception:
        final_predicate = predicates[-1]
        items.append(_rule_item(name, blocker, _negated_predicate(final_predicate), exception=waiver))
        if variant in {"blocked", "waived"}:
            items.append(_fact_item(name, blocker))
        else:
            items.append(_fact_item(name, blocker, negative=True))

        if variant == "waived":
            items.append(_fact_item(name, waiver))
        elif variant == "blocked":
            items.append(_fact_item(name, waiver, negative=True))
    return items


def _build_distractor_items(
    *,
    count: int,
    scenario_counter: int,
    level: int,
    rng: random.Random,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for index in range(count):
        name = _pick_unique(PERSONS, scenario_counter + level + index + 7)
        theme = _pick_unique(THEMES, scenario_counter + level + index + 13)
        distractor_predicates = _build_predicates(theme, min(2, len(STEP_TEMPLATES) - 2))
        items.append(_rule_item(name, distractor_predicates[0], distractor_predicates[1]))
        if rng.random() < 0.5:
            items.append(_fact_item(name, distractor_predicates[0]))
        else:
            items.append(_fact_item(name, distractor_predicates[0], negative=True))
    return items


def _interleave_items(
    core_items: list[dict[str, str]],
    distractor_items: list[dict[str, str]],
    rng: random.Random,
) -> list[dict[str, str]]:
    ordered = list(core_items)
    for item in distractor_items:
        insert_at = rng.randint(0, len(ordered))
        ordered.insert(insert_at, item)
    return ordered


def _derive_states(predicates: list[str], *, variant: str) -> dict[str, bool]:
    states = {predicate: False for predicate in predicates}
    if variant != "missing_base":
        states[predicates[0]] = True
        for predicate in predicates[1:]:
            states[predicate] = True
    if variant == "blocked":
        states[predicates[-1]] = False
    return states


def _gold_answer_for_target(
    *,
    target_depth: int,
    chain_length: int,
    derived_states: dict[str, bool],
    final_predicate: str,
    variant: str,
) -> str:
    target_predicate = list(derived_states)[target_depth]
    answer = derived_states[target_predicate]
    if target_depth == chain_length and target_predicate == final_predicate and variant == "blocked":
        answer = False
    return "yes" if answer else "no"


def _build_predicates(theme: str, chain_length: int) -> list[str]:
    return [template.format(theme=theme) for template in STEP_TEMPLATES[: chain_length + 1]]


def _select_target_indices(*, chain_length: int, followups: int) -> list[int]:
    start = max(1, chain_length - followups + 1)
    return list(range(start, chain_length + 1))


def _pick_unique(pool: list[str], index: int) -> str:
    return pool[index % len(pool)]


def _fact_item(name: str, predicate: str, negative: bool = False) -> dict[str, str]:
    claim_text = _negative_statement(name, predicate).rstrip(".") if negative else _positive_statement(name, predicate).rstrip(".")
    return {
        "kind": "fact",
        "sentence": _render_fact_sentence(name, predicate, negative=negative),
        "claim_text": claim_text,
    }


def _rule_item(name: str, condition: str, outcome: str, exception: str | None = None) -> dict[str, str]:
    sentence = _render_rule_sentence(name, condition, outcome, exception=exception)
    exception_text = f"{name} {exception}" if exception else ""
    if sentence.endswith("."):
        sentence = sentence
    else:
        sentence += "."
    return {
        "kind": "rule",
        "sentence": sentence,
        "condition_text": f"{name} {condition}",
        "outcome_text": f"{name} {outcome}",
        "exception_text": exception_text,
    }


def _render_fact_sentence(name: str, predicate: str, negative: bool = False) -> str:
    statement = _negative_statement(name, predicate).rstrip(".") if negative else _positive_statement(name, predicate).rstrip(".")
    return (
        f"According to the current facility record, {statement}, "
        "as noted in the active compliance log for this shift."
    )


def _render_rule_sentence(name: str, condition: str, outcome: str, exception: str | None = None) -> str:
    sentence = (
        f"If {name} {condition}, then under the standing facility policy in effect for the current shift "
        f"{name} {outcome}"
    )
    if exception:
        sentence += f" unless {name} {exception}"
    return sentence + "."


def _question_for_predicate(name: str, predicate: str) -> str:
    if predicate.startswith("completed "):
        return f"Did {name} complete {predicate.removeprefix('completed ')}?"
    if predicate.startswith("holds "):
        return f"Does {name} hold {predicate.removeprefix('holds ')}?"
    if predicate.startswith("has "):
        return f"Does {name} have {predicate.removeprefix('has ')}?"
    if predicate.startswith("is "):
        return f"Is {name} {predicate.removeprefix('is ')}?"
    if predicate.startswith("may "):
        return f"May {name} {predicate.removeprefix('may ')}?"
    return f"Is it true that {name} {predicate}?"


def _positive_statement(name: str, predicate: str) -> str:
    return f"{name} {predicate}."


def _negative_statement(name: str, predicate: str) -> str:
    if predicate.startswith("completed "):
        return f"{name} did not complete {predicate.removeprefix('completed ')}."
    if predicate.startswith("holds "):
        return f"{name} does not hold {predicate.removeprefix('holds ')}."
    if predicate.startswith("has "):
        return f"{name} does not have {predicate.removeprefix('has ')}."
    if predicate.startswith("is "):
        return f"{name} is not {predicate.removeprefix('is ')}."
    if predicate.startswith("may "):
        return f"{name} may not {predicate.removeprefix('may ')}."
    return f"It is not the case that {name} {predicate}."


def _negated_predicate(predicate: str) -> str:
    if predicate.startswith("completed "):
        return f"did not complete {predicate.removeprefix('completed ')}"
    if predicate.startswith("holds "):
        return f"does not hold {predicate.removeprefix('holds ')}"
    if predicate.startswith("has "):
        return f"does not have {predicate.removeprefix('has ')}"
    if predicate.startswith("is "):
        return f"is not {predicate.removeprefix('is ')}"
    if predicate.startswith("may "):
        return f"may not {predicate.removeprefix('may ')}"
    return f"is not in state {predicate}"


def _build_context_logical_form(
    items: list[dict[str, str]],
    *,
    context: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    logical_form: dict[str, Any] = {
        "source_text": context,
        "language": "en",
        "parse_status": "ok",
        "blocks": [],
        "relations": [],
        "ambiguities": [],
        "metadata": metadata,
    }
    block_counter = 0

    def add_block(block_type: str, text: str) -> str:
        nonlocal block_counter
        block_counter += 1
        block_id = f"b{block_counter}"
        logical_form["blocks"].append(
            {
                "id": block_id,
                "type": block_type,
                "text": text,
                "canonical_text": _canonical_text(text),
                "polarity": _infer_polarity(text),
            }
        )
        return block_id

    for item in items:
        if item["kind"] == "fact":
            add_block("claim", item["claim_text"])
            continue
        condition_id = add_block("condition", item["condition_text"])
        outcome_id = add_block("outcome", item["outcome_text"])
        logical_form["relations"].append({"type": "implies", "source": condition_id, "target": outcome_id})
        if item.get("exception_text"):
            exception_id = add_block("exception", item["exception_text"])
            logical_form["relations"].append({"type": "unless", "source": exception_id, "target": outcome_id})
    return logical_form


def _build_question_logical_form(question: str) -> dict[str, Any]:
    text = question.rstrip("?")
    return {
        "source_text": question,
        "language": "en",
        "parse_status": "ok",
        "blocks": [
            {
                "id": "b1",
                "type": "question",
                "text": text,
                "canonical_text": _canonical_text(text),
                "polarity": _infer_polarity(text),
            }
        ],
        "relations": [],
        "ambiguities": [],
        "metadata": {"generator": "complexity-sweep-v1"},
    }


def _canonical_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).strip(".,;:!?")


def _infer_polarity(text: str) -> str:
    lowered = f" {_canonical_text(text)} "
    return "negative" if any(cue in lowered for cue in NEGATIVE_CUES) else "positive"


def _new_level_bucket() -> dict[str, Any]:
    return {
        "case_count": 0,
        "scenario_ids": set(),
        "context_characters": [],
        "context_words": [],
        "context_sentence_count": [],
        "chain_length": [],
        "distractor_count": [],
        "target_depth": [],
        "followup_count": [],
        "canonical_characters": [],
        "compact_characters": [],
        "compact_smaller_than_raw": 0,
        "compact_prompt_smaller_than_direct": 0,
        "conditions": {},
    }


def _new_condition_bucket() -> dict[str, list[float] | list[int]]:
    return {
        "accuracy": [],
        "latency_seconds": [],
        "iterations": [],
        "input_tokens": [],
        "output_tokens": [],
        "total_tokens": [],
        "cached_tokens": [],
        "reasoning_tokens": [],
        "prompt_characters": [],
        "prompt_words": [],
    }


def _finalize_condition_bucket(bucket: dict[str, list[float] | list[int]]) -> dict[str, Any]:
    return {
        "accuracy": _safe_mean(bucket["accuracy"]),
        "average_latency_seconds": _safe_mean(bucket["latency_seconds"]),
        "average_iterations": _safe_mean(bucket["iterations"]),
        "average_input_tokens": _safe_mean(bucket["input_tokens"]),
        "average_output_tokens": _safe_mean(bucket["output_tokens"]),
        "average_total_tokens": _safe_mean(bucket["total_tokens"]),
        "average_cached_tokens": _safe_mean(bucket["cached_tokens"]),
        "average_reasoning_tokens": _safe_mean(bucket["reasoning_tokens"]),
        "average_prompt_characters": _safe_mean(bucket["prompt_characters"]),
        "average_prompt_words": _safe_mean(bucket["prompt_words"]),
    }


def _prompt_size(condition: dict[str, Any]) -> int:
    return int(condition.get("prompt_characters", 0) or 0) + int(condition.get("instructions_characters", 0) or 0)


def _safe_mean(values: list[float] | list[int]) -> float:
    return round(mean(values), 6) if values else 0.0
