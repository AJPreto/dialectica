"""Lightweight logical-form validation."""

from __future__ import annotations

from typing import Any

from .constants import BLOCK_TYPES, PARSE_STATUSES, POLARITIES, RELATION_TYPES


def validate_logical_form(logical_form: dict[str, Any]) -> list[str]:
    """Return a list of validation errors. Empty means valid enough for V1."""
    errors: list[str] = []
    required_top_level = ("source_text", "blocks", "relations")
    for field in required_top_level:
        if field not in logical_form:
            errors.append(f"Missing top-level field: {field}")

    if logical_form.get("parse_status", "ok") not in PARSE_STATUSES:
        errors.append(f"Invalid parse_status: {logical_form.get('parse_status')}")

    block_ids: set[str] = set()
    for index, block in enumerate(logical_form.get("blocks", []), start=1):
        block_id = block.get("id")
        if not block_id:
            errors.append(f"Block {index} is missing id")
            continue
        block_ids.add(block_id)
        if block.get("type") not in BLOCK_TYPES:
            errors.append(f"Block {block_id} has invalid type: {block.get('type')}")
        if not isinstance(block.get("text"), str) or not block["text"].strip():
            errors.append(f"Block {block_id} has empty text")
        if block.get("polarity", "neutral") not in POLARITIES:
            errors.append(f"Block {block_id} has invalid polarity: {block.get('polarity')}")

    for index, relation in enumerate(logical_form.get("relations", []), start=1):
        relation_type = relation.get("type")
        source = relation.get("source")
        target = relation.get("target")
        if relation_type not in RELATION_TYPES:
            errors.append(f"Relation {index} has invalid type: {relation_type}")
        if source not in block_ids:
            errors.append(f"Relation {index} references unknown source block: {source}")
        if target not in block_ids:
            errors.append(f"Relation {index} references unknown target block: {target}")

    return errors

