"""Evaluation helpers for Dialectica benchmarks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._io import load_cases
from .canonical import serialize_logical_form
from .parser import parse
from .validation import validate_logical_form


def evaluate_dataset(path: str | Path) -> dict[str, Any]:
    dataset = load_cases(path)
    results: list[dict[str, Any]] = []
    valid_count = 0
    exact_block_type_match = 0
    exact_relation_type_match = 0

    for case in dataset:
        parsed = parse(case["text"], language=case.get("language", "en"))
        validation_errors = validate_logical_form(parsed)
        if not validation_errors:
            valid_count += 1

        actual_block_types = sorted(block["type"] for block in parsed.get("blocks", []))
        expected_block_types = sorted(case.get("expected_block_types", []))
        actual_relation_types = sorted(relation["type"] for relation in parsed.get("relations", []))
        expected_relation_types = sorted(case.get("expected_relation_types", []))
        if actual_block_types == expected_block_types:
            exact_block_type_match += 1
        if actual_relation_types == expected_relation_types:
            exact_relation_type_match += 1

        results.append(
            {
                "id": case["id"],
                "text": case["text"],
                "expected_block_types": expected_block_types,
                "actual_block_types": actual_block_types,
                "expected_relation_types": expected_relation_types,
                "actual_relation_types": actual_relation_types,
                "validation_errors": validation_errors,
                "canonical_text": serialize_logical_form(parsed),
            }
        )

    total = len(dataset) or 1
    return {
        "dataset_path": str(path),
        "case_count": len(dataset),
        "valid_ratio": valid_count / total,
        "exact_block_type_match_ratio": exact_block_type_match / total,
        "exact_relation_type_match_ratio": exact_relation_type_match / total,
        "results": results,
    }
