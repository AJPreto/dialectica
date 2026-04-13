"""Deterministic Horn-style reasoning engine for the experimental V2 path."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ir import Atom, Constant, Variable, ir_to_dict


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
        notes.append("Some AST statements were intentionally withheld from Horn reasoning because their export was partial or unsupported.")

    return ReasoningResult(
        answer=answer,
        query=query,
        derived_facts=list(known.values()),
        trace=trace,
        blocked=blocked,
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


def _atom_key(atom: Atom) -> tuple[str, tuple[str, ...]]:
    return atom.predicate, tuple(_term_value(argument) for argument in atom.arguments)


def _term_value(term) -> str:
    if hasattr(term, "name"):
        return str(term.name)
    if hasattr(term, "value"):
        return str(term.value)
    return str(term)


def _atom_from_dict(payload: dict[str, Any]) -> Atom:
    arguments = []
    for argument in payload.get("arguments", []):
        node_type = argument.get("node_type")
        if node_type == "Variable":
            arguments.append(Variable(argument["name"], sort=argument.get("sort")))
        else:
            arguments.append(Constant(str(argument.get("name", argument.get("value"))), sort=argument.get("sort")))
    return Atom(predicate=payload["predicate"], arguments=tuple(arguments))

