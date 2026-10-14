"""Question-conditioned logical-form filtering for compact Dialectica prompts."""

from __future__ import annotations

import re
from typing import Any

from .canonical import canonicalize_logical_form


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "is",
    "it",
    "may",
    "might",
    "must",
    "not",
    "of",
    "on",
    "or",
    "should",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "they",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "would",
}

RELATION_EXPANSION_TYPES = {"implies", "unless", "qualifies", "supports"}


def filter_logical_form(
    context_form: dict[str, Any],
    question_form: dict[str, Any],
    *,
    max_hops: int = 4,
) -> dict[str, Any]:
    """Return a question-conditioned subgraph of a logical form.

    The goal is to approximate a "logical filter" stage: keep the blocks most
    relevant to the question, then expand through supporting relations so the
    compact prompt can omit unrelated context.
    """
    canonical_context = canonicalize_logical_form(context_form)
    canonical_question = canonicalize_logical_form(question_form)
    blocks = canonical_context.get("blocks", [])
    relations = canonical_context.get("relations", [])
    ambiguities = canonical_context.get("ambiguities", [])
    if not blocks:
        return canonical_context

    question_tokens = _question_tokens(canonical_question)
    if not question_tokens:
        return _fallback_filtered_form(canonical_context, reason="no_question_tokens")

    token_map = {block["id"]: _informative_tokens(block.get("canonical_text", block.get("text", ""))) for block in blocks}
    score_map = {block["id"]: _block_score(block, token_map[block["id"]], question_tokens) for block in blocks}
    best_score = max(score_map.values(), default=0.0)
    if best_score <= 0.0:
        return _fallback_filtered_form(canonical_context, reason="no_overlap")

    selected_ids = {
        block_id
        for block_id, score in score_map.items()
        if score >= max(1.0, best_score - 0.75)
    }

    for _ in range(max_hops):
        changed = False
        for relation in relations:
            source = relation["source"]
            target = relation["target"]
            relation_type = relation.get("type", "")
            if target in selected_ids and source not in selected_ids:
                selected_ids.add(source)
                changed = True
            if source in selected_ids and relation_type in RELATION_EXPANSION_TYPES and target not in selected_ids:
                selected_ids.add(target)
                changed = True
        if not changed:
            break

    selected_tokens = set().union(*(token_map.get(block_id, set()) for block_id in selected_ids))
    for block in blocks:
        if block["id"] in selected_ids:
            continue
        block_tokens = token_map.get(block["id"], set())
        overlap_with_question = len(block_tokens & question_tokens)
        overlap_with_selected = len(block_tokens & selected_tokens)
        if block.get("type") == "claim" and overlap_with_question and overlap_with_selected:
            selected_ids.add(block["id"])
            continue
        if _jaccard(block_tokens, selected_tokens) >= 0.6:
            selected_ids.add(block["id"])

    filtered_blocks = [block for block in blocks if block["id"] in selected_ids]
    filtered_relations = [
        relation
        for relation in relations
        if relation["source"] in selected_ids and relation["target"] in selected_ids
    ]
    filtered_ambiguities = [
        ambiguity
        for ambiguity in ambiguities
        if any(block_id in selected_ids for block_id in ambiguity.get("affected_blocks", []))
    ]

    filtered_form = {
        "source_text": canonical_context.get("source_text", ""),
        "language": canonical_context.get("language", "en"),
        "parse_status": canonical_context.get("parse_status", "ok"),
        "blocks": filtered_blocks,
        "relations": filtered_relations,
        "ambiguities": filtered_ambiguities,
        "metadata": {
            **canonical_context.get("metadata", {}),
            "filter": {
                "strategy": "question-conditioned",
                "source_block_count": len(blocks),
                "filtered_block_count": len(filtered_blocks),
                "source_relation_count": len(relations),
                "filtered_relation_count": len(filtered_relations),
                "question_tokens": sorted(question_tokens),
            },
        },
    }
    return canonicalize_logical_form(filtered_form)


def _fallback_filtered_form(canonical: dict[str, Any], *, reason: str) -> dict[str, Any]:
    fallback = dict(canonical)
    metadata = dict(fallback.get("metadata", {}))
    metadata["filter"] = {
        "strategy": "question-conditioned",
        "fallback": reason,
        "source_block_count": len(fallback.get("blocks", [])),
        "filtered_block_count": len(fallback.get("blocks", [])),
        "source_relation_count": len(fallback.get("relations", [])),
        "filtered_relation_count": len(fallback.get("relations", [])),
    }
    fallback["metadata"] = metadata
    return fallback


def _question_tokens(question_form: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for block in question_form.get("blocks", []):
        tokens.update(_informative_tokens(block.get("canonical_text", block.get("text", ""))))
    return tokens


def _block_score(block: dict[str, Any], block_tokens: set[str], question_tokens: set[str]) -> float:
    overlap = len(block_tokens & question_tokens)
    if overlap == 0:
        return 0.0
    type_bonus = {
        "outcome": 1.0,
        "constraint": 1.0,
        "claim": 0.8,
        "condition": 0.6,
        "exception": 0.6,
        "goal": 0.4,
    }.get(block.get("type", ""), 0.0)
    polarity_bonus = 0.25 if block.get("polarity") == "negative" else 0.0
    return overlap + type_bonus + polarity_bonus + _jaccard(block_tokens, question_tokens)


def _informative_tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(text.casefold())
        if token not in STOPWORDS and len(token) >= 3
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
