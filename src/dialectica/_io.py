"""JSON file helpers shared by the benchmark harnesses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load a benchmark dataset: a JSON array of case objects that each carry an ``id``."""
    dataset_path = Path(path)
    try:
        # utf-8-sig tolerates the BOM that some Windows editors add.
        payload = json.loads(dataset_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in benchmark dataset {dataset_path}: {exc.msg}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"Benchmark dataset {dataset_path} must be a JSON array of case objects.")
    for index, case in enumerate(payload, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Benchmark dataset {dataset_path} case {index} must be an object.")
        if "id" not in case:
            raise ValueError(f"Benchmark dataset {dataset_path} case {index} is missing required field 'id'.")
    return payload


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(payload: Any, output_path: str | Path) -> None:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
