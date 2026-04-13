"""Controlled natural-language translator for the experimental Dialectica V2 path."""

from __future__ import annotations

import re
from dataclasses import replace

from .ir import (
    Atom,
    Comparison,
    Constant,
    ExportRecord,
    HybridDocument,
    HybridStatement,
    Negation,
    NumberLiteral,
    Provenance,
    RuleCore,
    SemanticResidue,
    Variable,
)


_SENTENCE_PATTERN = re.compile(r"[^.!?]+[.!?]?")
_COMPARISON_PATTERN = re.compile(r"^(?P<left>[a-z0-9_ ]+)\s*(?P<op>>=|<=|!=|=|>|<)\s*(?P<right>-?\d+(?:\.\d+)?)$", re.I)
_UNIVERSAL_MODAL_PATTERN = re.compile(
    r"^all (?P<class_phrase>.+?) (?P<modal>may|can|must|should) (?P<action>.+)$",
    re.I,
)
_UNIVERSAL_IS_PATTERN = re.compile(r"^all (?P<class_phrase>.+?) are (?P<state>.+)$", re.I)
_RULE_PATTERN = re.compile(
    r"^if (?P<body>.+?), then (?P<head>.+?)(?: unless (?P<exception>.+))?$",
    re.I,
)

_UNCERTAINTY_MARKERS = ("maybe", "perhaps", "probably", "possibly")
_MODALITY_MARKERS = ("may", "can", "must", "should")
_TEMPORAL_MARKERS = ("currently", "for now", "this shift", "today", "later")
_UNRESOLVED_REFERENCES = {"he", "she", "they", "them", "it", "this", "that", "these", "those"}


def translate_text(text: str, query: str | None = None) -> HybridDocument:
    """Translate raw text into the experimental hybrid AST."""
    statements: list[HybridStatement] = []
    statement_counter = 0
    segments = _split_sentences_with_spans(text)
    query_text = query

    for sentence_index, (fragment, start, end) in enumerate(segments, start=1):
        cleaned = _normalize(fragment)
        if not cleaned:
            continue
        if cleaned.endswith("?") and query_text is None:
            query_text = cleaned
            continue
        statement_counter += 1
        statement = _translate_sentence(
            cleaned,
            statement_id=f"s{statement_counter}",
            sentence_id=f"ctx-{sentence_index}",
            source_text=text,
            start=start,
            end=end,
        )
        statements.append(statement)

    if query_text:
        statement_counter += 1
        statements.append(
            _translate_sentence(
                query_text,
                statement_id=f"s{statement_counter}",
                sentence_id="query-1",
                source_text=query_text,
                start=0,
                end=len(query_text),
                force_query=True,
            )
        )

    return HybridDocument(
        source_text=text if query is None else f"{text.strip()} {query.strip()}".strip(),
        statements=statements,
        metadata={
            "path": "experimental-v2",
            "translator": "controlled-heuristic-v2",
            "statement_count": len(statements),
        },
    )


def _translate_sentence(
    sentence: str,
    *,
    statement_id: str,
    sentence_id: str,
    source_text: str,
    start: int,
    end: int,
    force_query: bool = False,
) -> HybridStatement:
    residue, stripped = _collect_residue(sentence)
    provenance = Provenance(
        sentence_id=sentence_id,
        source_text=source_text,
        fragment=sentence,
        span=None if force_query else None if start < 0 else _span(start, end),
    )
    working = stripped.rstrip(".?!")

    if force_query or sentence.rstrip().endswith("?"):
        formal_core = _parse_query(working)
        if formal_core is None:
            residue.non_formalized_fragments.append(sentence)
        return HybridStatement(
            id=statement_id,
            kind="query",
            formal_core=formal_core,
            semantic_residue=residue,
            provenance=provenance,
            exportability={},
        )

    rule = _parse_rule(working)
    if rule is not None:
        return HybridStatement(
            id=statement_id,
            kind="rule",
            formal_core=rule,
            semantic_residue=residue,
            provenance=provenance,
            exportability={},
        )

    universal = _parse_universal_rule(working)
    if universal is not None:
        return HybridStatement(
            id=statement_id,
            kind="rule",
            formal_core=universal,
            semantic_residue=residue,
            provenance=provenance,
            exportability={},
        )

    comparison = _parse_comparison(working)
    if comparison is not None:
        return HybridStatement(
            id=statement_id,
            kind="fact",
            formal_core=comparison,
            semantic_residue=residue,
            provenance=provenance,
            exportability={},
        )

    atom_like = _parse_clause(working)
    if atom_like is not None:
        return HybridStatement(
            id=statement_id,
            kind="fact",
            formal_core=atom_like,
            semantic_residue=residue,
            provenance=provenance,
            exportability={},
        )

    residue.non_formalized_fragments.append(sentence)
    return HybridStatement(
        id=statement_id,
        kind="residue",
        formal_core=None,
        semantic_residue=residue,
        provenance=provenance,
        exportability={},
    )


def _parse_rule(sentence: str) -> RuleCore | None:
    match = _RULE_PATTERN.match(sentence)
    if not match:
        return None
    body = tuple(filter(None, (_parse_clause(part) for part in _split_conjuncts(match.group("body")))))
    head = _parse_clause(match.group("head"))
    exception_text = match.group("exception")
    exceptions = tuple(filter(None, (_parse_clause(part) for part in _split_conjuncts(exception_text or ""))))
    if not body or head is None:
        return None
    return RuleCore(head=head, body=body, exceptions=exceptions)


def _parse_universal_rule(sentence: str) -> RuleCore | None:
    modal_match = _UNIVERSAL_MODAL_PATTERN.match(sentence)
    if modal_match:
        variable = Variable("X", sort="entity")
        body = _class_membership_atom(modal_match.group("class_phrase"), variable)
        head = _action_atom(variable, modal_match.group("modal").lower(), modal_match.group("action"))
        return RuleCore(head=head, body=(body,), variables=(variable,))

    state_match = _UNIVERSAL_IS_PATTERN.match(sentence)
    if state_match:
        variable = Variable("X", sort="entity")
        body = _class_membership_atom(state_match.group("class_phrase"), variable)
        head = _state_atom(variable, state_match.group("state"))
        return RuleCore(head=head, body=(body,), variables=(variable,))

    return None


def _parse_query(sentence: str):
    normalized = _normalize(sentence.rstrip("?"))
    query_matchers = (
        (re.compile(r"^(?:may|can) (?P<subject>.+?) (?P<action>\w+)(?: (?P<object>.+))?$", re.I), _query_modal_atom),
        (re.compile(r"^does (?P<subject>.+?) (?P<lemma>\w+)(?: (?P<object>.+))?$", re.I), _query_verb_atom),
        (re.compile(r"^is (?P<subject>.+?) (?P<state>.+)$", re.I), _query_state_atom),
        (re.compile(r"^has (?P<subject>.+?) (?P<object>.+)$", re.I), _query_has_atom),
    )
    for pattern, builder in query_matchers:
        match = pattern.match(normalized)
        if match:
            return builder(match)
    return _parse_clause(normalized)


def _parse_clause(text: str):
    normalized = _normalize(text)
    if not normalized:
        return None

    for pattern, builder in (
        (re.compile(r"^(?P<subject>.+?) did not complete (?P<object>.+)$", re.I), _negative_completed_atom),
        (re.compile(r"^(?P<subject>.+?) completed (?P<object>.+)$", re.I), _completed_atom),
        (re.compile(r"^(?P<subject>.+?) does not hold (?P<object>.+)$", re.I), _negative_holds_atom),
        (re.compile(r"^(?P<subject>.+?) holds (?P<object>.+)$", re.I), _holds_atom),
        (re.compile(r"^(?P<subject>.+?) does not have (?P<object>.+)$", re.I), _negative_has_atom),
        (re.compile(r"^(?P<subject>.+?) has (?P<object>.+)$", re.I), _has_atom),
        (re.compile(r"^(?P<subject>.+?) may not (?P<action>\w+)(?: (?P<object>.+))?$", re.I), _negative_modal_atom),
        (re.compile(r"^(?P<subject>.+?) may (?P<action>\w+)(?: (?P<object>.+))?$", re.I), _modal_atom),
        (re.compile(r"^(?P<subject>.+?) can (?P<action>\w+)(?: (?P<object>.+))?$", re.I), _can_atom),
        (re.compile(r"^(?P<subject>.+?) is not (?P<object>.+)$", re.I), _negative_state_atom),
        (re.compile(r"^(?P<subject>.+?) is (?P<object>.+)$", re.I), _state_from_match),
    ):
        match = pattern.match(normalized)
        if match:
            return builder(match)
    return None


def _parse_comparison(text: str) -> Comparison | None:
    match = _COMPARISON_PATTERN.match(_normalize(text))
    if not match:
        return None
    return Comparison(
        operator=match.group("op"),
        left=Constant(_slug(match.group("left")), sort="number_symbol"),
        right=NumberLiteral(_to_number(match.group("right"))),
    )


def _class_membership_atom(class_phrase: str, variable: Variable) -> Atom:
    return Atom(predicate=_class_predicate(class_phrase), arguments=(variable,))


def _completed_atom(match: re.Match[str]) -> Atom:
    return _unary_atom(match.group("subject"), f"completed {match.group('object')}")


def _negative_completed_atom(match: re.Match[str]) -> Negation:
    return Negation(_unary_atom(match.group("subject"), f"completed {match.group('object')}"))


def _holds_atom(match: re.Match[str]) -> Atom:
    return _unary_atom(match.group("subject"), f"holds {match.group('object')}")


def _negative_holds_atom(match: re.Match[str]) -> Negation:
    return Negation(_unary_atom(match.group("subject"), f"holds {match.group('object')}"))


def _has_atom(match: re.Match[str]) -> Atom:
    return _unary_atom(match.group("subject"), f"has {match.group('object')}")


def _negative_has_atom(match: re.Match[str]) -> Negation:
    return Negation(_unary_atom(match.group("subject"), f"has {match.group('object')}"))


def _modal_atom(match: re.Match[str]) -> Atom:
    return _action_atom(_subject_term(match.group("subject")), "may", _action_phrase(match))


def _negative_modal_atom(match: re.Match[str]) -> Negation:
    return Negation(_action_atom(_subject_term(match.group("subject")), "may", _action_phrase(match)))


def _can_atom(match: re.Match[str]) -> Atom:
    return _action_atom(_subject_term(match.group("subject")), "can", _action_phrase(match))


def _state_from_match(match: re.Match[str]) -> Atom:
    return _state_atom(_subject_term(match.group("subject")), match.group("object"))


def _negative_state_atom(match: re.Match[str]) -> Negation:
    return Negation(_state_atom(_subject_term(match.group("subject")), match.group("object")))


def _query_modal_atom(match: re.Match[str]) -> Atom:
    return _action_atom(_subject_term(match.group("subject")), "may", _action_phrase(match))


def _query_verb_atom(match: re.Match[str]) -> Atom:
    lemma = match.group("lemma")
    normalized_lemma = {
        "complete": "completed",
        "hold": "holds",
        "have": "has",
    }.get(lemma.casefold(), lemma.casefold())
    remainder = " ".join(part for part in (normalized_lemma, match.group("object")) if part)
    return _unary_atom(match.group("subject"), remainder)


def _query_state_atom(match: re.Match[str]) -> Atom:
    return _state_atom(_subject_term(match.group("subject")), match.group("state"))


def _query_has_atom(match: re.Match[str]) -> Atom:
    return _unary_atom(match.group("subject"), f"has {match.group('object')}")


def _action_atom(subject_term, modal: str, action_text: str) -> Atom:
    return Atom(predicate=_predicate_slug(f"{modal} {action_text}"), arguments=(subject_term,))


def _state_atom(subject_term, state_text: str) -> Atom:
    cleaned = _strip_leading_articles(state_text)
    return Atom(predicate=_predicate_slug(cleaned), arguments=(subject_term,))


def _unary_atom(subject: str, predicate_text: str) -> Atom:
    return Atom(predicate=_predicate_slug(predicate_text), arguments=(_subject_term(subject),))


def _subject_term(subject: str):
    normalized = _normalize(subject)
    if normalized.upper() == "X":
        return Variable("X", sort="entity")
    return Constant(_slug(normalized), sort="entity")


def _collect_residue(sentence: str) -> tuple[SemanticResidue, str]:
    working = _normalize(sentence)
    residue = SemanticResidue()

    attribution_match = re.match(r"^according to ([^,]+),\s*(.+)$", working, re.I)
    if attribution_match:
        residue.attribution.append(attribution_match.group(1).strip())
        working = attribution_match.group(2).strip()

    note_match = re.match(r"^(.+?),\s*as noted in ([^,]+)(?:,\s*(.+))?$", working, re.I)
    if note_match:
        residue.attribution.append(note_match.group(2).strip())
        working = " ".join(part.strip() for part in (note_match.group(1), note_match.group(3) or "") if part and part.strip())

    lowered = f" {working.casefold()} "
    for marker in _UNCERTAINTY_MARKERS:
        token = f" {marker} "
        if token in lowered:
            residue.uncertainty.append(marker)
            working = re.sub(rf"\b{re.escape(marker)}\b", "", working, flags=re.I)
    for marker in _MODALITY_MARKERS:
        if re.search(rf"\b{re.escape(marker)}\b", lowered):
            residue.modality.append(marker)
    for marker in _TEMPORAL_MARKERS:
        if marker in lowered:
            residue.temporal_vagueness.append(marker)

    unresolved = {
        token for token in re.findall(r"[a-z]+", lowered) if token in _UNRESOLVED_REFERENCES
    }
    if unresolved:
        residue.unresolved_references.extend(sorted(unresolved))

    confidence = 1.0
    if residue.uncertainty:
        confidence -= 0.35
    if residue.attribution:
        confidence -= 0.1
    if residue.temporal_vagueness:
        confidence -= 0.05
    if residue.unresolved_references:
        confidence -= 0.25
    residue.confidence = max(0.2, round(confidence, 3))
    return residue, _normalize(working)


def _split_sentences_with_spans(text: str) -> list[tuple[str, int, int]]:
    segments: list[tuple[str, int, int]] = []
    for match in _SENTENCE_PATTERN.finditer(text):
        fragment = match.group(0).strip()
        if fragment:
            segments.append((fragment, match.start(), match.end()))
    return segments


def _split_conjuncts(text: str) -> list[str]:
    normalized = _normalize(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"\band\b", normalized, flags=re.I) if part.strip()]


def _predicate_slug(text: str) -> str:
    normalized = _strip_leading_articles(text)
    normalized = re.sub(r"\s+", " ", normalized.strip().casefold())
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("/", " ")
    normalized = re.sub(r"[^a-z0-9 ]+", "", normalized)
    parts = [part for part in normalized.split() if part]
    if parts and parts[-1].endswith("s") and len(parts[-1]) > 3 and parts[-1] not in {"is", "was", "has"}:
        parts[-1] = parts[-1][:-1]
    return "_".join(parts) or "unknown_predicate"


def _class_predicate(class_phrase: str) -> str:
    predicate = _predicate_slug(class_phrase)
    if not predicate.endswith("_member") and "_" not in predicate:
        return f"{predicate}_member"
    return predicate


def _action_phrase(match: re.Match[str]) -> str:
    return " ".join(part for part in (match.group("action"), match.groupdict().get("object")) if part)


def _strip_leading_articles(text: str) -> str:
    return re.sub(r"^(?:the|a|an)\s+", "", text.strip(), flags=re.I)


def _slug(text: str) -> str:
    normalized = _strip_leading_articles(text)
    normalized = normalized.casefold().replace("-", " ")
    normalized = re.sub(r"[^a-z0-9 ]+", "", normalized)
    parts = [part for part in normalized.split() if part]
    if parts and parts[-1].endswith("s") and len(parts[-1]) > 3:
        parts[-1] = parts[-1][:-1]
    return "_".join(parts) or "unknown"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _to_number(text: str) -> int | float:
    return float(text) if "." in text else int(text)


def _span(start: int, end: int):
    from .ir import SourceSpan

    return SourceSpan(start=start, end=end)
