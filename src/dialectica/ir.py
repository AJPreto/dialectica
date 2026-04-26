"""Hybrid intermediate representation for Dialectica reasoning."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


EXPORT_STATUSES = ("exact", "partial", "lossy", "unsupported")


@dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int


@dataclass
class Provenance:
    sentence_id: str
    source_text: str
    fragment: str
    span: SourceSpan | None = None


@dataclass
class SemanticResidue:
    ambiguity: list[str] = field(default_factory=list)
    modality: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    attribution: list[str] = field(default_factory=list)
    temporal_vagueness: list[str] = field(default_factory=list)
    unresolved_references: list[str] = field(default_factory=list)
    non_formalized_fragments: list[str] = field(default_factory=list)
    confidence: float = 1.0

    def is_empty(self) -> bool:
        return not any(
            (
                self.ambiguity,
                self.modality,
                self.uncertainty,
                self.attribution,
                self.temporal_vagueness,
                self.unresolved_references,
                self.non_formalized_fragments,
            )
        ) and self.confidence >= 0.999


@dataclass
class ExportRecord:
    target: str
    status: str
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in EXPORT_STATUSES:
            raise ValueError(f"Unsupported export status: {self.status}")


@dataclass(frozen=True)
class Variable:
    name: str
    sort: str | None = None


@dataclass(frozen=True)
class Constant:
    name: str
    sort: str | None = None


@dataclass(frozen=True)
class NumberLiteral:
    value: int | float


@dataclass(frozen=True)
class FunctionCall:
    name: str
    arguments: tuple[TermLike, ...] = ()
    sort: str | None = None


@dataclass(frozen=True)
class ArithmeticExpression:
    operator: str
    operands: tuple[ValueLike, ...]


@dataclass(frozen=True)
class Atom:
    predicate: str
    arguments: tuple[TermLike, ...] = ()


@dataclass(frozen=True)
class Comparison:
    operator: str
    left: ValueLike
    right: ValueLike


@dataclass(frozen=True)
class Conjunction:
    conjuncts: tuple[FormulaLike, ...]


@dataclass(frozen=True)
class Disjunction:
    disjuncts: tuple[FormulaLike, ...]


@dataclass(frozen=True)
class Negation:
    operand: FormulaLike


@dataclass(frozen=True)
class Implication:
    antecedent: FormulaLike
    consequent: FormulaLike


@dataclass(frozen=True)
class Quantified:
    quantifier: str
    variables: tuple[Variable, ...]
    body: FormulaLike


@dataclass(frozen=True)
class RuleCore:
    head: Atom | Comparison
    body: tuple[Atom | Comparison, ...] = ()
    exceptions: tuple[Atom | Comparison, ...] = ()
    variables: tuple[Variable, ...] = ()


ValueLike = Variable | Constant | NumberLiteral | FunctionCall | ArithmeticExpression
TermLike = Variable | Constant | NumberLiteral | FunctionCall
FormulaLike = Atom | Comparison | Conjunction | Disjunction | Negation | Implication | Quantified
FormalCore = Atom | Comparison | Conjunction | Disjunction | Negation | Implication | Quantified | RuleCore


@dataclass
class HybridStatement:
    id: str
    kind: str
    formal_core: FormalCore | None
    semantic_residue: SemanticResidue
    provenance: Provenance
    exportability: dict[str, ExportRecord] = field(default_factory=dict)


@dataclass
class HybridDocument:
    source_text: str
    statements: list[HybridStatement]
    metadata: dict[str, Any] = field(default_factory=dict)

    def query_statement(self) -> HybridStatement | None:
        for statement in self.statements:
            if statement.kind == "query":
                return statement
        return None


def ir_to_dict(value: Any) -> Any:
    """Serialize dataclass-heavy IR structures into plain JSON-safe objects."""
    if is_dataclass(value):
        payload = {}
        for field_info in fields(value):
            payload[field_info.name] = ir_to_dict(getattr(value, field_info.name))
        payload["node_type"] = type(value).__name__
        return payload
    if isinstance(value, dict):
        return {key: ir_to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [ir_to_dict(item) for item in value]
    return value
