"""Heuristic natural-language to logical-form parser."""

from __future__ import annotations

import re
from typing import Any

from .canonical import canonicalize_logical_form


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


def parse(text: str, *, language: str = "en", document: bool = False) -> dict[str, Any]:
    """Parse text into a canonical logical form.

    This is the recommended entry point: it picks the sentence or document
    parser and returns the canonicalized result.
    """
    parse_fn = parse_document if document else parse_text
    return canonicalize_logical_form(parse_fn(text, language=language))


def parse_text(text: str, language: str = "en") -> dict[str, Any]:
    """Parse natural language into a Dialectica logical form.

    The local parser uses lightweight heuristics so it can run locally
    without a model dependency.
    """
    cleaned = _normalize_text(text)
    logical_form: dict[str, Any] = {
        "source_text": text,
        "language": language,
        "parse_status": "ok" if cleaned else "failed",
        "blocks": [],
        "relations": [],
        "ambiguities": [],
        "metadata": {"parser": "heuristic"},
    }
    if not cleaned:
        return logical_form

    block_counter = 0

    def add_block(block_type: str, block_text: str) -> str:
        nonlocal block_counter
        block_counter += 1
        block_id = f"b{block_counter}"
        canonical_text = _canonical_text(block_text)
        logical_form["blocks"].append(
            {
                "id": block_id,
                "type": block_type,
                "text": block_text.strip(" ,."),
                "canonical_text": canonical_text,
                "polarity": _infer_polarity(block_text),
                "certainty": _infer_certainty(block_type, block_text),
                "tags": _infer_tags(canonical_text),
            }
        )
        return block_id

    lowered = f" {cleaned.lower()} "
    parsed = False

    if cleaned.endswith("?"):
        qid = add_block("question", cleaned.rstrip("?"))
        logical_form["parse_status"] = "underspecified"
        logical_form["ambiguities"].append(
            {
                "id": "a1",
                "description": "Question intent is clear, but answer content is absent.",
                "affected_blocks": [qid],
            }
        )
        return logical_form

    conditional = _match_conditional(cleaned)
    if conditional:
        parsed = True
        condition_id = add_block("condition", conditional["condition"])
        outcome_text = _normalize_conditional_outcome(conditional["outcome"])
        outcome_type = _classify_simple_block(outcome_text)
        if outcome_type == "claim":
            outcome_type = "outcome"
        outcome_id = add_block(outcome_type, outcome_text)
        logical_form["relations"].append(
            {"type": "implies", "source": condition_id, "target": outcome_id, "certainty": 0.85}
        )
        if conditional["exception"]:
            exception_id = add_block("exception", conditional["exception"])
            logical_form["relations"].append(
                {"type": "unless", "source": exception_id, "target": outcome_id, "certainty": 0.8}
            )

    because = _match_connector(cleaned, " because ")
    if because:
        parsed = True
        left, right = because
        left_id = add_block(_classify_simple_block(left), left)
        right_id = add_block("evidence", right)
        logical_form["relations"].append(
            {"type": "supports", "source": right_id, "target": left_id, "certainty": 0.82}
        )

    definition = _match_definition(cleaned)
    if definition:
        parsed = True
        term, meaning = definition
        term_id = add_block("claim", term)
        def_id = add_block("definition", meaning)
        logical_form["relations"].append(
            {"type": "defines", "source": def_id, "target": term_id, "certainty": 0.88}
        )

    contrast = _match_connector(cleaned, " but ")
    if contrast:
        parsed = True
        left, right = contrast
        left_id = add_block(_classify_simple_block(left), left)
        right_id = add_block(_classify_simple_block(right), right)
        logical_form["relations"].append(
            {"type": "qualifies", "source": right_id, "target": left_id, "certainty": 0.7}
        )
        logical_form["parse_status"] = "ambiguous"
        logical_form["ambiguities"].append(
            {
                "id": f"a{len(logical_form['ambiguities']) + 1}",
                "description": "The connector 'but' may indicate qualification, contrast, or contradiction.",
                "affected_blocks": [left_id, right_id],
            }
        )

    if not parsed:
        block_type = _classify_simple_block(cleaned)
        add_block(block_type, cleaned)
        if block_type in {"unknown", "claim"} and _might_be_ambiguous(lowered):
            logical_form["parse_status"] = "ambiguous"
            logical_form["ambiguities"].append(
                {
                    "id": "a1",
                    "description": "The utterance may contain implicit relations not recoverable from heuristics.",
                    "affected_blocks": ["b1"],
                }
            )

    _dedupe_blocks(logical_form)
    return logical_form


def parse_document(text: str, language: str = "en") -> dict[str, Any]:
    """Parse a multi-sentence document by combining sentence-level parses."""
    segments = _split_sentences(text)
    if len(segments) <= 1:
        return parse_text(text, language=language)

    merged: dict[str, Any] = {
        "source_text": text,
        "language": language,
        "parse_status": "ok",
        "blocks": [],
        "relations": [],
        "ambiguities": [],
        "metadata": {"parser": "heuristic", "mode": "document", "segment_count": len(segments)},
    }
    block_counter = 0
    ambiguity_counter = 0
    status_priority = {"ok": 0, "underspecified": 1, "ambiguous": 2, "failed": 3}

    for sentence_index, segment in enumerate(segments, start=1):
        parsed = parse_text(segment, language=language)
        if status_priority.get(parsed["parse_status"], 0) > status_priority.get(merged["parse_status"], 0):
            merged["parse_status"] = parsed["parse_status"]

        block_mapping: dict[str, str] = {}
        for block in parsed.get("blocks", []):
            block_counter += 1
            new_id = f"b{block_counter}"
            block_mapping[block["id"]] = new_id
            copied_block = dict(block)
            copied_block["id"] = new_id
            copied_block.setdefault("tags", [])
            copied_block["tags"] = [*copied_block["tags"], f"sentence_{sentence_index}"]
            merged["blocks"].append(copied_block)

        for relation in parsed.get("relations", []):
            copied_relation = dict(relation)
            copied_relation["source"] = block_mapping.get(relation["source"], relation["source"])
            copied_relation["target"] = block_mapping.get(relation["target"], relation["target"])
            merged["relations"].append(copied_relation)

        for ambiguity in parsed.get("ambiguities", []):
            ambiguity_counter += 1
            copied_ambiguity = dict(ambiguity)
            copied_ambiguity["id"] = f"a{ambiguity_counter}"
            copied_ambiguity["affected_blocks"] = [
                block_mapping.get(block_id, block_id) for block_id in ambiguity.get("affected_blocks", [])
            ]
            merged["ambiguities"].append(copied_ambiguity)

    return merged


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _split_sentences(text: str) -> list[str]:
    cleaned = _normalize_text(text)
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part for part in parts if part]


def _canonical_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return normalized.strip(".,;:!?")


def _infer_polarity(text: str) -> str:
    lowered = f" {_canonical_text(text)} "
    return "negative" if any(cue in lowered for cue in NEGATIVE_CUES) else "positive"


def _infer_certainty(block_type: str, text: str) -> float:
    lowered = _canonical_text(text)
    if "maybe" in lowered or "might" in lowered or "possibly" in lowered:
        return 0.45
    if block_type in {"unknown", "ambiguity"}:
        return 0.3
    if block_type == "question":
        return 0.5
    return 0.85


def _infer_tags(text: str) -> list[str]:
    words = [token for token in re.findall(r"[a-z0-9_]+", text) if len(token) > 3]
    return words[:4]


def _classify_simple_block(text: str) -> str:
    lowered = _canonical_text(text)
    if not lowered:
        return "unknown"
    if any(lowered.startswith(prefix) for prefix in ("define ", "what is ", "what does ")):
        return "question"
    if _looks_like_constraint(lowered):
        return "constraint"
    if _looks_like_goal(lowered):
        return "goal"
    if lowered.startswith("if "):
        return "condition"
    if " because " in lowered or any(lowered.startswith(prefix) for prefix in ("since ", "according to ")):
        return "evidence"
    if _looks_like_definition(lowered):
        return "definition"
    return "claim"


def _looks_like_goal(text: str) -> bool:
    lowered = _canonical_text(text)
    return any(
        cue in lowered
        for cue in (
            "should ",
            "need to ",
            "want to ",
            "goal is ",
            "aim is ",
            "must ",
            "i want ",
        )
    )


def _looks_like_constraint(text: str) -> bool:
    lowered = _canonical_text(text)
    return any(
        cue in lowered
        for cue in (
            "cannot ",
            "can't ",
            "must not ",
            "should not ",
            "only if ",
            "requires ",
            "at most ",
            "no more than ",
            "required ",
            "requirement ",
            "allowed only ",
        )
    )


def _looks_like_definition(text: str) -> bool:
    lowered = _canonical_text(text)
    return " means " in lowered or " is defined as " in lowered


def _match_conditional(text: str) -> dict[str, str | None] | None:
    match = re.match(
        r"(?i)^if (?P<condition>.+?), (?P<outcome>.+?)(?: unless (?P<exception>.+))?[.?!]?$",
        text,
    )
    if match:
        return match.groupdict()
    match = re.match(
        r"(?i)^(?P<outcome>.+?) if (?P<condition>.+?)(?: unless (?P<exception>.+))?[.?!]?$",
        text,
    )
    return match.groupdict() if match else None


def _normalize_conditional_outcome(text: str) -> str:
    normalized = text.strip()
    if normalized.lower().endswith(" only"):
        return normalized[:-5].rstrip()
    return normalized


def _match_connector(text: str, connector: str) -> tuple[str, str] | None:
    lowered = text.lower()
    if connector not in lowered:
        return None
    index = lowered.index(connector)
    left = text[:index].strip(" ,.")
    right = text[index + len(connector) :].strip(" ,.")
    if not left or not right:
        return None
    return left, right


def _match_definition(text: str) -> tuple[str, str] | None:
    for connector in (" means ", " is defined as "):
        match = _match_connector(text, connector)
        if match:
            return match
    return None


def _might_be_ambiguous(lowered: str) -> bool:
    return any(cue in lowered for cue in (" maybe ", " perhaps ", " probably ", " but ", " however "))


def _dedupe_blocks(logical_form: dict[str, Any]) -> None:
    """Merge blocks with the same type and text, repointing references to the kept block."""
    kept: dict[tuple[str, str], str] = {}
    replacements: dict[str, str] = {}
    blocks: list[dict[str, Any]] = []
    for block in logical_form["blocks"]:
        key = (block["type"], block["canonical_text"])
        if key in kept:
            replacements[block["id"]] = kept[key]
            continue
        kept[key] = block["id"]
        blocks.append(block)
    if not replacements:
        return

    logical_form["blocks"] = blocks
    relations = []
    for relation in logical_form["relations"]:
        relation["source"] = replacements.get(relation["source"], relation["source"])
        relation["target"] = replacements.get(relation["target"], relation["target"])
        if relation["source"] != relation["target"]:
            relations.append(relation)
    logical_form["relations"] = relations
    for ambiguity in logical_form["ambiguities"]:
        affected = (replacements.get(block_id, block_id) for block_id in ambiguity["affected_blocks"])
        ambiguity["affected_blocks"] = list(dict.fromkeys(affected))
