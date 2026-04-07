"""Canonicalization helpers for Dialectica logical forms."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def canonicalize_logical_form(logical_form: dict[str, Any]) -> dict[str, Any]:
    """Return a stable copy of a logical form.

    The canonicalizer sorts blocks and relations, normalizes missing defaults,
    and makes serialized embeddings more stable.
    """
    canonical = deepcopy(logical_form)
    blocks = canonical.get("blocks", [])
    blocks.sort(key=lambda block: (block.get("type", ""), block.get("canonical_text", block.get("text", ""))))
    old_to_new: dict[str, str] = {}
    for index, block in enumerate(blocks, start=1):
        old_to_new[block["id"]] = f"b{index}"
        block["id"] = f"b{index}"
        block.setdefault("canonical_text", block.get("text", "").strip().lower())
        block.setdefault("polarity", "neutral")
        block.setdefault("tags", [])

    relations = canonical.get("relations", [])
    for relation in relations:
        relation["source"] = old_to_new.get(relation["source"], relation["source"])
        relation["target"] = old_to_new.get(relation["target"], relation["target"])
    relations.sort(key=lambda relation: (relation.get("type", ""), relation.get("source", ""), relation.get("target", "")))
    canonical["blocks"] = blocks
    canonical["relations"] = relations
    canonical.setdefault("ambiguities", [])
    canonical.setdefault("metadata", {})
    return canonical


def serialize_logical_form(logical_form: dict[str, Any]) -> str:
    """Serialize a logical form into a stable text representation."""
    canonical = canonicalize_logical_form(logical_form)
    lines: list[str] = []
    for block in canonical.get("blocks", []):
        lines.append(
            f'BLOCK {block["id"]} {block["type"]} {block.get("polarity", "neutral")} "{block.get("canonical_text", block.get("text", ""))}"'
        )
    for relation in canonical.get("relations", []):
        lines.append(f'REL {relation["source"]} {relation["type"]} {relation["target"]}')
    for ambiguity in canonical.get("ambiguities", []):
        lines.append(f'AMBIG {ambiguity["id"]} "{ambiguity["description"]}"')
    return "\n".join(lines)

