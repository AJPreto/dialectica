"""Canonicalization helpers for Dialectica logical forms."""

from __future__ import annotations

import re
from collections import Counter
from copy import deepcopy
from typing import Any


BLOCK_TYPE_CODES = {
    "claim": "c",
    "condition": "if",
    "constraint": "k",
    "definition": "def",
    "evidence": "ev",
    "exception": "exc",
    "goal": "goal",
    "outcome": "out",
    "question": "q",
    "unknown": "u",
}

RELATION_TYPE_CODES = {
    "defines": ":=",
    "implies": "=>",
    "qualifies": "~>",
    "supports": "+>",
    "unless": "unless",
}

POLARITY_CODES = {
    "negative": "-",
    "neutral": "0",
    "positive": "+",
}

TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


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


def serialize_compact_logical_form(logical_form: dict[str, Any]) -> str:
    """Serialize a logical form into a denser text form for prompt compression tests."""
    canonical = canonicalize_logical_form(logical_form)
    token_aliases = _build_token_aliases(canonical)
    proposition_aliases = _build_proposition_aliases(canonical)
    lines: list[str] = []
    if token_aliases:
        lexicon = "|".join(f"{alias}={token}" for token, alias in token_aliases.items())
        lines.append(f"LEX|{lexicon}")
    for proposition, alias in proposition_aliases.items():
        text = _compact_text(proposition, token_aliases)
        lines.append(f"P|{alias}|{text}")

    role_counts = Counter(
        (
            BLOCK_TYPE_CODES.get(block["type"], block["type"]),
            POLARITY_CODES.get(block.get("polarity", "neutral"), "0"),
            proposition_aliases[block.get("canonical_text", block.get("text", ""))],
        )
        for block in canonical.get("blocks", [])
    )
    for (block_type, polarity, alias), count in sorted(role_counts.items()):
        suffix = f"|x{count}" if count > 1 else ""
        lines.append(f"B|{block_type}|{polarity}|{alias}{suffix}")

    block_lookup = {block["id"]: block for block in canonical.get("blocks", [])}
    relation_counts = Counter()
    for relation in canonical.get("relations", []):
        source_block = block_lookup.get(relation["source"], {})
        target_block = block_lookup.get(relation["target"], {})
        source_alias = proposition_aliases.get(source_block.get("canonical_text", source_block.get("text", "")), relation["source"])
        target_alias = proposition_aliases.get(target_block.get("canonical_text", target_block.get("text", "")), relation["target"])
        relation_type = RELATION_TYPE_CODES.get(relation["type"], relation["type"])
        relation_counts[(source_alias, relation_type, target_alias)] += 1
    for (source_alias, relation_type, target_alias), count in sorted(relation_counts.items()):
        suffix = f"|x{count}" if count > 1 else ""
        lines.append(f"R|{source_alias}{relation_type}{target_alias}{suffix}")
    for ambiguity in canonical.get("ambiguities", []):
        description = _compact_text(ambiguity.get("description", ""), token_aliases)
        lines.append(f'??|{ambiguity["id"]}|{description}')
    return "\n".join(lines)


def _build_token_aliases(logical_form: dict[str, Any]) -> dict[str, str]:
    counts: Counter[str] = Counter()
    for block in logical_form.get("blocks", []):
        counts.update(TOKEN_PATTERN.findall(block.get("canonical_text", block.get("text", "")).casefold()))
    for ambiguity in logical_form.get("ambiguities", []):
        counts.update(TOKEN_PATTERN.findall(ambiguity.get("description", "").casefold()))

    aliases: dict[str, str] = {}
    alias_counter = 1
    for token, count in counts.most_common():
        alias = f"~{alias_counter}"
        dictionary_cost = len(alias) + len(token) + 2
        gross_savings = count * max(0, len(token) - len(alias))
        if count >= 2 and len(token) >= 4 and gross_savings > dictionary_cost:
            aliases[token] = alias
            alias_counter += 1
    return aliases


def _build_proposition_aliases(logical_form: dict[str, Any]) -> dict[str, str]:
    propositions = sorted(
        {
            block.get("canonical_text", block.get("text", ""))
            for block in logical_form.get("blocks", [])
            if block.get("canonical_text", block.get("text", ""))
        }
    )
    return {proposition: f"p{index}" for index, proposition in enumerate(propositions, start=1)}


def _compact_text(text: str, token_aliases: dict[str, str]) -> str:
    tokens = TOKEN_PATTERN.findall(text.casefold())
    compact_tokens = [token_aliases.get(token, token) for token in tokens]
    return " ".join(compact_tokens).replace("|", "/")
