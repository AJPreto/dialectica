"""Controlled natural-language translator for Dialectica reasoning."""

from __future__ import annotations

import re

from .ir import (
    Atom,
    FormalCore,
    Comparison,
    Conjunction,
    Constant,
    Disjunction,
    HybridDocument,
    HybridStatement,
    Implication,
    Negation,
    NumberLiteral,
    Provenance,
    RuleCore,
    SemanticResidue,
    SourceSpan,
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
_SEMICOLON_SPLIT_PATTERN = re.compile(r";")
_CONJUNCTION_SPLIT_PATTERN = re.compile(r"\band\b", re.I)
_GENERIC_VERB_PATTERN = re.compile(r"^(?P<subject>[A-Z][A-Za-z0-9_-]*) (?P<verb>[a-z]+)(?: (?P<object>.+))?$")
_VERB_ALIASES = {
    "finishes": "completed",
    "finished": "completed",
    "finish": "completed",
    "receives": "receive",
    "received": "receive",
    "receive": "receive",
    "wears": "wear",
    "wore": "wear",
    "wear": "wear",
    "carries": "carry",
    "carried": "carry",
    "carry": "carry",
}
_GENERIC_VERB_CANONICALS = set(_VERB_ALIASES.values())


def translate_text(text: str, query: str | None = None) -> HybridDocument:
    """Translate raw text into the hybrid reasoning AST."""
    statements: list[HybridStatement] = []
    statement_counter = 0
    prepared_context = _prepare_context_units(text)
    query_text = query

    for unit in prepared_context["units"]:
        cleaned = unit["fragment"]
        if not cleaned:
            continue
        if cleaned.endswith("?") and query_text is None:
            query_text = cleaned
            continue
        statement_counter += 1
        statement = _translate_sentence(
            cleaned,
            statement_id=f"s{statement_counter}",
            sentence_id=unit["sentence_id"],
            source_text=text,
            start=unit["start"],
            end=unit["end"],
        )
        statements.append(statement)

    if query_text:
        query_text = _normalize(query_text)
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
            "path": "hybrid-reasoning",
            "translator": "controlled-heuristic",
            "statement_count": len(statements),
            "pretranslation": prepared_context["metadata"],
        },
    )


def _prepare_context_units(text: str) -> dict[str, object]:
    raw_segments = _split_sentences_with_spans(text)
    units: list[dict[str, object]] = []
    decomposition_events: list[dict[str, object]] = []
    removed_duplicates: list[dict[str, object]] = []
    seen_keys: dict[str, str] = {}
    candidate_count = 0

    for sentence_index, (fragment, start, end) in enumerate(raw_segments, start=1):
        decomposed_units, events = _decompose_context_fragment(
            fragment,
            start=start,
            end=end,
            sentence_index=sentence_index,
        )
        decomposition_events.extend(events)
        for unit in decomposed_units:
            candidate_count += 1
            cleaned = _normalize(str(unit["fragment"]))
            if not cleaned:
                continue
            unit["fragment"] = cleaned
            redundancy_key = _redundancy_key(cleaned)
            duplicate_of = seen_keys.get(redundancy_key)
            if duplicate_of is not None:
                removed_duplicates.append(
                    {
                        "fragment": cleaned,
                        "duplicate_of": duplicate_of,
                        "sentence_id": unit["sentence_id"],
                        "span": {"start": unit["start"], "end": unit["end"]},
                    }
                )
                continue
            seen_keys[redundancy_key] = str(unit["sentence_id"])
            units.append(unit)

    return {
        "units": units,
        "metadata": {
            "original_sentence_count": len(raw_segments),
            "candidate_unit_count": candidate_count,
            "kept_unit_count": len(units),
            "duplicate_unit_count": len(removed_duplicates),
            "decomposition_count": len(decomposition_events),
            "removed_duplicates": removed_duplicates,
            "decomposition_events": decomposition_events,
        },
    }


def _decompose_context_fragment(
    fragment: str,
    *,
    start: int,
    end: int,
    sentence_index: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    base_units = [{"fragment": fragment, "start": start, "end": end}]
    events: list[dict[str, object]] = []

    semicolon_units = _split_units_on_pattern(
        base_units,
        pattern=_SEMICOLON_SPLIT_PATTERN,
        strategy="semicolon",
    )
    if semicolon_units != base_units:
        events.append(
            {
                "strategy": "semicolon",
                "source_fragment": _normalize(fragment),
                "emitted_fragments": [_normalize(str(unit["fragment"])) for unit in semicolon_units],
            }
        )
    working_units = semicolon_units

    if not _is_query_fragment(fragment) and not _looks_like_rule_fragment(fragment):
        conjunction_units = _split_units_on_pattern(
            working_units,
            pattern=_CONJUNCTION_SPLIT_PATTERN,
            strategy="explicit_conjunction",
        )
        if conjunction_units != working_units:
            events.append(
                {
                    "strategy": "explicit_conjunction",
                    "source_fragment": _normalize(fragment),
                    "emitted_fragments": [_normalize(str(unit["fragment"])) for unit in conjunction_units],
                }
            )
        working_units = conjunction_units

    numbered_units: list[dict[str, object]] = []
    for clause_index, unit in enumerate(working_units, start=1):
        sentence_id = f"ctx-{sentence_index}" if len(working_units) == 1 else f"ctx-{sentence_index}.{clause_index}"
        numbered_units.append(
            {
                **unit,
                "sentence_id": sentence_id,
            }
        )
    return numbered_units, events


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
        span=None if force_query or start < 0 else SourceSpan(start=start, end=end),
    )
    working = stripped.rstrip(".?!")
    kind, formal_core = _classify_sentence(working, is_query=force_query or sentence.rstrip().endswith("?"))
    if formal_core is None:
        residue.non_formalized_fragments.append(sentence)
    return HybridStatement(
        id=statement_id,
        kind=kind,
        formal_core=formal_core,
        semantic_residue=residue,
        provenance=provenance,
    )


def _classify_sentence(working: str, *, is_query: bool) -> tuple[str, FormalCore | None]:
    if is_query:
        return "query", _parse_query(working)
    rule = _parse_rule(working)
    if rule is not None:
        return "rule", rule
    if _looks_like_conditional_syntax(working):
        # A conditional we could not formalize must not degrade into a fake fact.
        return "residue", None
    universal = _parse_universal_rule(working)
    if universal is not None:
        return "rule", universal
    fact = _parse_comparison(working) or _parse_clause(working)
    if fact is not None:
        return "fact", fact
    return "residue", None


def _parse_rule(sentence: str) -> RuleCore | None:
    match = _RULE_PATTERN.match(sentence)
    if not match:
        return None
    head = _parse_clause(match.group("head"))
    exception_text = match.group("exception")
    exceptions = tuple(filter(None, (_parse_clause(part) for part in _split_on_keyword(_normalize(exception_text or ""), "and"))))
    if head is None:
        return None
    antecedent = _parse_rule_antecedent(match.group("body"))
    if antecedent is None:
        return None
    if isinstance(antecedent, Conjunction) and all(isinstance(item, (Atom, Comparison)) for item in antecedent.conjuncts):
        body = tuple(antecedent.conjuncts)
        return RuleCore(head=head, body=body, exceptions=exceptions)
    if isinstance(antecedent, (Atom, Comparison)):
        return RuleCore(head=head, body=(antecedent,), exceptions=exceptions)
    if exceptions:
        return None
    return Implication(antecedent=antecedent, consequent=head)


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
    if normalized.casefold().startswith("is "):
        comparison = _parse_comparison(normalized[3:])
        if comparison is not None:
            return comparison
    for pattern, builder in _QUERY_MATCHERS:
        match = pattern.match(normalized)
        if match:
            return builder(match)
    return _parse_clause(normalized)


def _parse_clause(text: str):
    normalized = _normalize(text)
    if not normalized:
        return None

    for pattern, builder in _CLAUSE_MATCHERS:
        match = pattern.match(normalized)
        if match:
            parsed = builder(match)
            if parsed is not None:
                return parsed
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


def _unary_builder(prefix: str, *, negated: bool = False):
    def build(match: re.Match[str]) -> Atom | Negation:
        atom = _unary_atom(match.group("subject"), f"{prefix} {match.group('object')}")
        return Negation(atom) if negated else atom

    return build


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


def _query_verb_atom(match: re.Match[str]) -> Atom:
    lemma = match.group("lemma")
    normalized_lemma = {
        "complete": "completed",
        "finish": "completed",
        "finished": "completed",
        "hold": "holds",
        "have": "has",
    }.get(lemma.casefold(), _normalize_verb(lemma))
    remainder = " ".join(part for part in (normalized_lemma, match.group("object")) if part)
    return _unary_atom(match.group("subject"), remainder)


def _query_state_atom(match: re.Match[str]) -> Atom:
    return _state_atom(_subject_term(match.group("subject")), match.group("state"))


def _generic_verb_atom(match: re.Match[str]) -> Atom | None:
    subject = match.group("subject")
    if subject.casefold() in {"a", "an", "the", "if"}:
        return None
    verb = _normalize_verb(match.group("verb"))
    if verb not in _GENERIC_VERB_CANONICALS:
        return None
    predicate_text = " ".join(part for part in (verb, match.group("object")) if part)
    return _unary_atom(subject, predicate_text)


def _clause_pattern(verb: str, *, action: bool = False) -> re.Pattern[str]:
    tail = r"(?P<action>\w+)(?: (?P<object>.+))?" if action else r"(?P<object>.+)"
    return re.compile(rf"^(?P<subject>.+?) {verb} {tail}$", re.I)


# Order matters: negated forms must be tried before their positive counterparts.
_CLAUSE_MATCHERS = (
    (_clause_pattern("did not complete"), _unary_builder("completed", negated=True)),
    (_clause_pattern("completed"), _unary_builder("completed")),
    (_clause_pattern("does not hold"), _unary_builder("holds", negated=True)),
    (_clause_pattern("holds"), _unary_builder("holds")),
    (_clause_pattern("does not have"), _unary_builder("has", negated=True)),
    (_clause_pattern("has"), _unary_builder("has")),
    (_clause_pattern("may not", action=True), _negative_modal_atom),
    (_clause_pattern("may", action=True), _modal_atom),
    (_clause_pattern("can", action=True), _can_atom),
    (_clause_pattern("is not"), _negative_state_atom),
    (_clause_pattern("is"), _state_from_match),
    (_GENERIC_VERB_PATTERN, _generic_verb_atom),
)
_QUERY_MATCHERS = (
    (re.compile(r"^(?:may|can) (?P<subject>.+?) (?P<action>\w+)(?: (?P<object>.+))?$", re.I), _modal_atom),
    (re.compile(r"^does (?P<subject>.+?) (?P<lemma>\w+)(?: (?P<object>.+))?$", re.I), _query_verb_atom),
    (re.compile(r"^is (?P<subject>.+?) (?P<state>.+)$", re.I), _query_state_atom),
    (re.compile(r"^has (?P<subject>.+?) (?P<object>.+)$", re.I), _unary_builder("has")),
)


def _action_atom(subject_term, modal: str, action_text: str) -> Atom:
    canonical_modal = "may" if modal in {"may", "can"} else modal
    return Atom(predicate=_predicate_slug(f"{canonical_modal} {action_text}"), arguments=(subject_term,))


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


def _split_units_on_pattern(
    units: list[dict[str, object]],
    *,
    pattern: re.Pattern[str],
    strategy: str,
) -> list[dict[str, object]]:
    split_units: list[dict[str, object]] = []
    changed = False
    for unit in units:
        fragment = str(unit["fragment"])
        pieces = _piece_units_from_pattern(
            fragment,
            start=int(unit["start"]),
            end=int(unit["end"]),
            pattern=pattern,
            strategy=strategy,
        )
        if pieces is None:
            split_units.append(unit)
            continue
        changed = True
        split_units.extend(pieces)
    return split_units if changed else units


def _piece_units_from_pattern(
    fragment: str,
    *,
    start: int,
    end: int,
    pattern: re.Pattern[str],
    strategy: str,
) -> list[dict[str, object]] | None:
    matches = list(pattern.finditer(fragment))
    if not matches:
        return None

    pieces: list[dict[str, object]] = []
    cursor = 0
    for match in matches:
        piece = _build_piece_unit(fragment, start, cursor, match.start())
        if piece is not None:
            pieces.append(piece)
        cursor = match.end()
    final_piece = _build_piece_unit(fragment, start, cursor, len(fragment))
    if final_piece is not None:
        pieces.append(final_piece)

    if len(pieces) <= 1:
        return None

    if strategy == "semicolon":
        if not all(_is_articulate_fragment(str(piece["fragment"])) for piece in pieces):
            return None
    elif strategy == "explicit_conjunction":
        if not all(_is_standalone_fact_fragment(str(piece["fragment"])) for piece in pieces):
            return None

    return pieces


def _build_piece_unit(fragment: str, start_offset: int, left: int, right: int) -> dict[str, object] | None:
    raw_piece = fragment[left:right]
    leading_trim = len(raw_piece) - len(raw_piece.lstrip(" \t\r\n,;"))
    trailing_trim = len(raw_piece) - len(raw_piece.rstrip(" \t\r\n,;"))
    trimmed = raw_piece.strip(" \t\r\n,;")
    if not trimmed:
        return None
    piece_start = start_offset + left + leading_trim
    piece_end = start_offset + right - trailing_trim
    return {"fragment": trimmed, "start": piece_start, "end": piece_end}


def _is_query_fragment(fragment: str) -> bool:
    return _normalize(fragment).endswith("?")


def _looks_like_rule_fragment(fragment: str) -> bool:
    normalized = _normalize(fragment).rstrip(".?!")
    return _looks_like_conditional_syntax(normalized) or _parse_universal_rule(normalized) is not None


def _looks_like_conditional_syntax(fragment: str) -> bool:
    return _RULE_PATTERN.match(_normalize(fragment).rstrip(".?!")) is not None


def _is_articulate_fragment(fragment: str) -> bool:
    normalized = _normalize(fragment)
    if not normalized:
        return False
    working = normalized.rstrip(".?!")
    if normalized.endswith("?"):
        return _parse_query(working) is not None
    return any(
        parser(working) is not None
        for parser in (_parse_rule, _parse_universal_rule, _parse_comparison, _parse_clause)
    )


def _is_standalone_fact_fragment(fragment: str) -> bool:
    normalized = _normalize(fragment)
    if not normalized or normalized.endswith("?"):
        return False
    if _looks_like_rule_fragment(normalized):
        return False
    working = normalized.rstrip(".?!")
    return _parse_clause(working) is not None or _parse_comparison(working) is not None


def _redundancy_key(fragment: str) -> str:
    normalized = _normalize(fragment)
    kind = "query" if normalized.endswith("?") else "statement"
    return f"{kind}:{normalized.casefold().rstrip('.?!')}"


def _parse_rule_antecedent(text: str):
    normalized = _normalize(text)
    if not normalized:
        return None

    disjuncts = _split_on_keyword(normalized, "or")
    if len(disjuncts) > 1:
        items = tuple(item for item in (_parse_rule_antecedent(part) for part in disjuncts) if item is not None)
        if len(items) == len(disjuncts):
            return Disjunction(disjuncts=items)
        return None

    conjuncts = _split_on_keyword(normalized, "and")
    if len(conjuncts) > 1:
        items = tuple(item for item in (_parse_rule_antecedent(part) for part in conjuncts) if item is not None)
        if len(items) == len(conjuncts):
            return Conjunction(conjuncts=items)
        return None

    return _parse_clause(normalized) or _parse_comparison(normalized)


def _split_on_keyword(text: str, keyword: str) -> list[str]:
    return [part.strip() for part in re.split(rf"\b{re.escape(keyword)}\b", text, flags=re.I) if part.strip()]


def _normalize_verb(verb: str) -> str:
    normalized = verb.casefold()
    return _VERB_ALIASES.get(normalized, normalized)


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
