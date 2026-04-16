"""Deterministic reasoning engines for the experimental V2 path."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ir import Atom, Comparison, Constant, NumberLiteral, Variable, ir_to_dict


@dataclass
class TraceStep:
    statement_id: str
    derived: Atom
    premises: list[Atom]
    blocked_by: list[Atom] = field(default_factory=list)


@dataclass
class ReasoningResult:
    answer: str
    query: Atom | None
    derived_facts: list[Atom]
    trace: list[TraceStep]
    blocked: list[TraceStep]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "query": ir_to_dict(self.query) if self.query else None,
            "derived_facts": [ir_to_dict(atom) for atom in self.derived_facts],
            "trace": [ir_to_dict(step) for step in self.trace],
            "blocked": [ir_to_dict(step) for step in self.blocked],
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SignedLiteral:
    sign: str
    atom: Atom | Comparison

    def text(self) -> str:
        prefix = "" if self.sign == "positive" else "not "
        if isinstance(self.atom, Atom):
            if self.atom.arguments:
                arguments = ", ".join(_term_value(argument) for argument in self.atom.arguments)
                return f"{prefix}{self.atom.predicate}({arguments})"
            return f"{prefix}{self.atom.predicate}"
        left = _value_text(self.atom.left)
        right = _value_text(self.atom.right)
        return f"{prefix}{left} {self.atom.operator} {right}"


@dataclass
class ProofStep:
    statement_id: str
    derived: SignedLiteral
    premises: list[SignedLiteral]
    blocked_by: list[SignedLiteral] = field(default_factory=list)
    conflict_with: list[SignedLiteral] = field(default_factory=list)


@dataclass
class FOLReasoningResult:
    answer: str
    query: SignedLiteral | None
    derived_literals: list[SignedLiteral]
    trace: list[ProofStep]
    blocked: list[ProofStep]
    conflicts: list[SignedLiteral]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "query": ir_to_dict(self.query) if self.query else None,
            "derived_literals": [ir_to_dict(item) for item in self.derived_literals],
            "trace": [ir_to_dict(step) for step in self.trace],
            "blocked": [ir_to_dict(step) for step in self.blocked],
            "conflicts": [ir_to_dict(item) for item in self.conflicts],
            "notes": self.notes,
        }


def reason_over_horn_program(program: dict[str, Any]) -> ReasoningResult:
    """Forward-chain over a Horn-like program exported from the V2 AST."""
    facts = [_atom_from_dict(entry["atom"]) for entry in program.get("facts", [])]
    rules = [
        {
            "statement_id": entry["statement_id"],
            "head": _atom_from_dict(entry["head"]),
            "body": [_atom_from_dict(item) for item in entry.get("body", [])],
            "exceptions": [_atom_from_dict(item) for item in entry.get("exceptions", [])],
        }
        for entry in program.get("rules", [])
    ]
    query_entry = program.get("query")
    query = _atom_from_dict(query_entry["atom"]) if isinstance(query_entry, dict) and query_entry.get("atom") else None

    known: dict[tuple[str, tuple[str, ...]], Atom] = {_atom_key(fact): fact for fact in facts}
    trace: list[TraceStep] = []
    blocked: list[TraceStep] = []
    changed = True

    while changed:
        changed = False
        known_facts = list(known.values())
        for rule in rules:
            for substitution, premises in _satisfy_body(rule["body"], known_facts, {}):
                head = _apply_substitution(rule["head"], substitution)
                exceptions = [_apply_substitution(item, substitution) for item in rule["exceptions"]]
                triggered = [item for item in exceptions if _atom_key(item) in known]
                if triggered:
                    blocked.append(
                        TraceStep(
                            statement_id=rule["statement_id"],
                            derived=head,
                            premises=premises,
                            blocked_by=triggered,
                        )
                    )
                    continue
                key = _atom_key(head)
                if key in known:
                    continue
                known[key] = head
                trace.append(TraceStep(statement_id=rule["statement_id"], derived=head, premises=premises))
                changed = True

    answer = "not_entailed"
    notes: list[str] = []
    if query is None:
        notes.append("No Horn-compilable query was available.")
    elif _atom_key(query) in known:
        answer = "entailed"
    elif any(_atom_key(step.derived) == _atom_key(query) for step in blocked):
        answer = "blocked"

    if program.get("skipped"):
        notes.append(
            "Some AST statements were intentionally withheld from Horn reasoning because their export was partial or unsupported."
        )

    return ReasoningResult(
        answer=answer,
        query=query,
        derived_facts=list(known.values()),
        trace=trace,
        blocked=blocked,
        notes=notes,
    )


def reason_over_fol_program(program: dict[str, Any]) -> FOLReasoningResult:
    """Run a deterministic skeptical proof search over the exported safe FOL fragment."""
    fact_entries = [
        {
            "statement_id": entry["statement_id"],
            "literal": _literal_from_dict(entry["literal"]),
        }
        for entry in program.get("facts", [])
    ]
    rule_entries = [
        {
            "statement_id": entry["statement_id"],
            "head": _literal_from_dict(entry["head"]),
            "branches": [
                [_literal_from_dict(item) for item in branch]
                for branch in entry.get("branches", [])
            ],
            "exceptions": [_literal_from_dict(item) for item in entry.get("exceptions", [])],
        }
        for entry in program.get("rules", [])
    ]
    query_entry = program.get("query")
    query = _literal_from_dict(query_entry["literal"]) if isinstance(query_entry, dict) and query_entry.get("literal") else None

    known: dict[tuple[str, tuple[Any, ...]], SignedLiteral] = {}
    trace: list[ProofStep] = []
    blocked: list[ProofStep] = []
    notes: list[str] = []

    for entry in fact_entries:
        literal = entry["literal"]
        known[_literal_key(literal)] = literal

    changed = True
    while changed:
        changed = False
        known_literals = list(known.values())
        for rule in rule_entries:
            for branch in rule["branches"]:
                for substitution, premises in _satisfy_literal_branch(branch, known_literals, {}):
                    grounded_premises = [_apply_substitution_literal(item, substitution) for item in premises]
                    if any(_literal_is_conflicted(item, known) for item in grounded_premises):
                        blocked.append(
                            ProofStep(
                                statement_id=rule["statement_id"],
                                derived=_apply_substitution_literal(rule["head"], substitution),
                                premises=grounded_premises,
                                blocked_by=[],
                                conflict_with=[item for item in grounded_premises if _literal_is_conflicted(item, known)],
                            )
                        )
                        continue
                    grounded_exceptions = [_apply_substitution_literal(item, substitution) for item in rule["exceptions"]]
                    triggered = [item for item in grounded_exceptions if _literal_key(item) in known]
                    if triggered:
                        blocked.append(
                            ProofStep(
                                statement_id=rule["statement_id"],
                                derived=_apply_substitution_literal(rule["head"], substitution),
                                premises=grounded_premises,
                                blocked_by=triggered,
                            )
                        )
                        continue
                    head = _apply_substitution_literal(rule["head"], substitution)
                    key = _literal_key(head)
                    if key in known:
                        continue
                    known[key] = head
                    trace.append(ProofStep(statement_id=rule["statement_id"], derived=head, premises=grounded_premises))
                    changed = True

    conflicts = _collect_conflicts(known)
    if program.get("skipped"):
        notes.append(
            "Some AST statements were intentionally withheld from the FOL reasoning core because their export was partial or unsupported."
        )
    if conflicts:
        notes.append("Conflicting positive and negative literals were detected, so skeptical proof blocked unsafe conclusions.")

    answer = "not_entailed"
    if query is None:
        notes.append("No FOL-compilable query was available.")
    else:
        query_key = _literal_key(query)
        complement_key = _literal_key(_complement_literal(query))
        query_known = query_key in known
        complement_known = complement_key in known
        if query_known and complement_known:
            answer = "conflicted"
        elif query_known:
            answer = "entailed"
        elif complement_known:
            answer = "refuted"

    return FOLReasoningResult(
        answer=answer,
        query=query,
        derived_literals=list(known.values()),
        trace=trace,
        blocked=blocked,
        conflicts=conflicts,
        notes=notes,
    )


def _satisfy_body(body: list[Atom], facts: list[Atom], substitution: dict[str, str]):
    if not body:
        yield substitution, []
        return
    first, *rest = body
    for fact in facts:
        next_substitution = _match_atom(first, fact, substitution)
        if next_substitution is None:
            continue
        grounded_first = _apply_substitution(first, next_substitution)
        for final_substitution, premises in _satisfy_body(rest, facts, next_substitution):
            yield final_substitution, [grounded_first, *premises]


def _match_atom(pattern: Atom, fact: Atom, substitution: dict[str, str]) -> dict[str, str] | None:
    if pattern.predicate != fact.predicate or len(pattern.arguments) != len(fact.arguments):
        return None
    current = dict(substitution)
    for pattern_arg, fact_arg in zip(pattern.arguments, fact.arguments, strict=False):
        if isinstance(pattern_arg, Variable):
            bound = current.get(pattern_arg.name)
            fact_value = _term_value(fact_arg)
            if bound is None:
                current[pattern_arg.name] = fact_value
            elif bound != fact_value:
                return None
            continue
        if _term_value(pattern_arg) != _term_value(fact_arg):
            return None
    return current


def _apply_substitution(atom: Atom, substitution: dict[str, str]) -> Atom:
    grounded_arguments = []
    for argument in atom.arguments:
        if isinstance(argument, Variable) and argument.name in substitution:
            grounded_arguments.append(Constant(substitution[argument.name], sort=argument.sort))
        else:
            grounded_arguments.append(argument)
    return Atom(predicate=atom.predicate, arguments=tuple(grounded_arguments))


def _satisfy_literal_branch(
    branch: list[SignedLiteral],
    facts: list[SignedLiteral],
    substitution: dict[str, str],
):
    if not branch:
        yield substitution, []
        return
    first, *rest = branch
    for fact in facts:
        next_substitution = _match_literal(first, fact, substitution)
        if next_substitution is None:
            continue
        grounded_first = _apply_substitution_literal(first, next_substitution)
        for final_substitution, premises in _satisfy_literal_branch(rest, facts, next_substitution):
            yield final_substitution, [grounded_first, *premises]


def _match_literal(
    pattern: SignedLiteral,
    fact: SignedLiteral,
    substitution: dict[str, str],
) -> dict[str, str] | None:
    if pattern.sign != fact.sign:
        return None
    if isinstance(pattern.atom, Atom) and isinstance(fact.atom, Atom):
        return _match_atom(pattern.atom, fact.atom, substitution)
    if isinstance(pattern.atom, Comparison) and isinstance(fact.atom, Comparison):
        return _match_comparison(pattern.atom, fact.atom, substitution)
    return None


def _match_comparison(
    pattern: Comparison,
    fact: Comparison,
    substitution: dict[str, str],
) -> dict[str, str] | None:
    if pattern.operator != fact.operator:
        return None
    current = dict(substitution)
    for left, right in ((pattern.left, fact.left), (pattern.right, fact.right)):
        if isinstance(left, Variable):
            bound = current.get(left.name)
            right_value = _value_text(right)
            if bound is None:
                current[left.name] = right_value
            elif bound != right_value:
                return None
            continue
        if _value_text(left) != _value_text(right):
            return None
    return current


def _apply_substitution_literal(literal: SignedLiteral, substitution: dict[str, str]) -> SignedLiteral:
    if isinstance(literal.atom, Atom):
        grounded_arguments = []
        for argument in literal.atom.arguments:
            if isinstance(argument, Variable) and argument.name in substitution:
                grounded_arguments.append(Constant(substitution[argument.name], sort=argument.sort))
            else:
                grounded_arguments.append(argument)
        return SignedLiteral(sign=literal.sign, atom=Atom(predicate=literal.atom.predicate, arguments=tuple(grounded_arguments)))
    comparison = literal.atom
    return SignedLiteral(
        sign=literal.sign,
        atom=Comparison(
            operator=comparison.operator,
            left=_apply_substitution_value(comparison.left, substitution),
            right=_apply_substitution_value(comparison.right, substitution),
        ),
    )


def _apply_substitution_value(value, substitution: dict[str, str]):
    if isinstance(value, Variable) and value.name in substitution:
        replacement = substitution[value.name]
        if replacement.replace(".", "", 1).isdigit():
            return NumberLiteral(float(replacement) if "." in replacement else int(replacement))
        return Constant(replacement, sort=value.sort)
    return value


def _literal_key(literal: SignedLiteral) -> tuple[str, tuple[Any, ...]]:
    return literal.sign, _formula_key(literal.atom)


def _formula_key(formula: Atom | Comparison) -> tuple[Any, ...]:
    if isinstance(formula, Atom):
        return ("atom", formula.predicate, tuple(_term_value(argument) for argument in formula.arguments))
    return ("comparison", formula.operator, _value_text(formula.left), _value_text(formula.right))


def _literal_is_conflicted(literal: SignedLiteral, known: dict[tuple[str, tuple[Any, ...]], SignedLiteral]) -> bool:
    return _literal_key(_complement_literal(literal)) in known


def _complement_literal(literal: SignedLiteral) -> SignedLiteral:
    return SignedLiteral(
        sign="negative" if literal.sign == "positive" else "positive",
        atom=literal.atom,
    )


def _collect_conflicts(known: dict[tuple[str, tuple[Any, ...]], SignedLiteral]) -> list[SignedLiteral]:
    conflicts: list[SignedLiteral] = []
    seen: set[tuple[str, tuple[Any, ...]]] = set()
    for literal in known.values():
        complement_key = _literal_key(_complement_literal(literal))
        literal_key = _literal_key(literal)
        if complement_key in known and literal_key not in seen and complement_key not in seen:
            conflicts.append(literal)
            seen.add(literal_key)
            seen.add(complement_key)
    return conflicts


def _atom_key(atom: Atom) -> tuple[str, tuple[str, ...]]:
    return atom.predicate, tuple(_term_value(argument) for argument in atom.arguments)


def _term_value(term) -> str:
    if hasattr(term, "name"):
        return str(term.name)
    if hasattr(term, "value"):
        return str(term.value)
    return str(term)


def _value_text(value) -> str:
    if isinstance(value, NumberLiteral):
        return str(value.value)
    return _term_value(value)


def _atom_from_dict(payload: dict[str, Any]) -> Atom:
    arguments = []
    for argument in payload.get("arguments", []):
        node_type = argument.get("node_type")
        if node_type == "Variable":
            arguments.append(Variable(argument["name"], sort=argument.get("sort")))
        else:
            arguments.append(Constant(str(argument.get("name", argument.get("value"))), sort=argument.get("sort")))
    return Atom(predicate=payload["predicate"], arguments=tuple(arguments))


def _comparison_from_dict(payload: dict[str, Any]) -> Comparison:
    return Comparison(
        operator=payload["operator"],
        left=_value_from_dict(payload["left"]),
        right=_value_from_dict(payload["right"]),
    )


def _value_from_dict(payload: dict[str, Any]):
    node_type = payload.get("node_type")
    if node_type == "Variable":
        return Variable(payload["name"], sort=payload.get("sort"))
    if node_type == "NumberLiteral":
        return NumberLiteral(payload["value"])
    return Constant(str(payload.get("name", payload.get("value"))), sort=payload.get("sort"))


def _literal_from_dict(payload: dict[str, Any]) -> SignedLiteral:
    atom_payload = payload["atom"]
    node_type = atom_payload.get("node_type")
    atom = _comparison_from_dict(atom_payload) if node_type == "Comparison" else _atom_from_dict(atom_payload)
    return SignedLiteral(sign=payload.get("sign", "positive"), atom=atom)
