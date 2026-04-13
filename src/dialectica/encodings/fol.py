"""FOL-style export for the experimental Dialectica V2 path."""

from __future__ import annotations

from typing import Any

from .base import BaseExporter, CompilationResult, combine_status
from ..ir import (
    ArithmeticExpression,
    Atom,
    Comparison,
    Constant,
    ExportRecord,
    HybridDocument,
    Negation,
    NumberLiteral,
    RuleCore,
    Variable,
)


class FOLExporter(BaseExporter):
    target = "fol"

    def compile(self, document: HybridDocument) -> CompilationResult:
        records: dict[str, ExportRecord] = {}
        formulas: list[dict[str, Any]] = []
        predicate_names: set[str] = set()
        constant_names: set[str] = set()
        notes: list[str] = []

        for statement in document.statements:
            record, formula = self._compile_statement(statement)
            records[statement.id] = record
            if formula is None:
                continue
            formulas.append(formula)
            _collect_signature(formula["formula"], predicate_names, constant_names)
            if record.status != "exact":
                notes.extend(record.notes)

        signature = {
            "types": [{"name": "$i", "kind": "built_in"}],
            "predicates": [
                {
                    "name": name,
                    "signature": "$i > $o",
                    "arity": 1,
                    "description": "Auto-generated from the V2 hybrid AST.",
                }
                for name in sorted(predicate_names)
            ],
            "functions": [],
            "constants": [
                {
                    "name": name,
                    "signature": "$i",
                    "arity": 0,
                    "description": "Auto-generated constant from the V2 hybrid AST.",
                }
                for name in sorted(constant_names)
            ],
        }
        artifact = {
            "dialect": "fof",
            "logic": {
                "name": "first_order",
                "typed": False,
                "higher_order": False,
                "supports_arithmetic": False,
                "supports_conditionals": True,
                "supports_lets": False,
            },
            "signature": signature,
            "annotated_formulae": formulas,
            "translation_notes": _dedupe(notes),
        }
        return CompilationResult(
            target=self.target,
            status=combine_status(list(records.values())),
            artifact=artifact,
            notes=_dedupe(notes),
            statement_records=records,
        )

    def _compile_statement(self, statement) -> tuple[ExportRecord, dict[str, Any] | None]:
        notes = _residue_notes(statement)
        core = statement.formal_core
        if core is None:
            return ExportRecord(target=self.target, status="unsupported", notes=[*notes, "No formal core to export."]), None

        status = "partial" if _requires_partial_export(statement) else "exact"
        if isinstance(core, Comparison) and core.operator not in {"=", "!="}:
            notes.append("Non-equality comparison was preserved in the AST but not emitted in the first FOL exporter.")
            return ExportRecord(target=self.target, status="unsupported", notes=notes), None

        formula = _formula_node(core)
        if formula is None:
            return ExportRecord(
                target=self.target,
                status="unsupported",
                notes=[*notes, "The FOL exporter could not compile this formal core."],
            ), None

        role = "conjecture" if statement.kind == "query" else "axiom"
        if isinstance(core, RuleCore) and core.exceptions:
            status = "partial"
            notes.append("Rule exceptions were exported as explicit negated guards, which is only a partial match for defeasible unless semantics.")
        return ExportRecord(target=self.target, status=status, notes=notes), {
            "name": statement.id,
            "language": "fof",
            "role": role,
            "linked_blocks": [],
            "source": {
                "kind": "parser",
                "reference": "experimental-v2-translator",
                "details": {"sentence_id": statement.provenance.sentence_id},
            },
            "useful_info": [{"key": "source_fragment", "value": statement.provenance.fragment}],
            "confidence": statement.semantic_residue.confidence,
            "formula": formula,
        }


def _formula_node(core):
    if isinstance(core, Atom):
        return {
            "kind": "predicate",
            "symbol": core.predicate,
            "arguments": [_term_node(argument) for argument in core.arguments],
        }
    if isinstance(core, Negation):
        operand = _formula_node(core.operand)
        if operand is None:
            return None
        return {"kind": "unary", "operator": "~", "body": operand}
    if isinstance(core, Comparison):
        if core.operator == "=":
            return {"kind": "equality", "left": _term_node(core.left), "right": _term_node(core.right)}
        if core.operator == "!=":
            return {"kind": "inequality", "left": _term_node(core.left), "right": _term_node(core.right)}
        return None
    if isinstance(core, RuleCore):
        antecedent = None
        parts = [_formula_node(item) for item in core.body]
        if any(part is None for part in parts):
            return None
        antecedent_parts = [part for part in parts if part is not None]
        for exception in core.exceptions:
            exception_node = _formula_node(Negation(exception))
            if exception_node is not None:
                antecedent_parts.append(exception_node)
        if not antecedent_parts:
            antecedent = {"kind": "literal", "value": True}
        elif len(antecedent_parts) == 1:
            antecedent = antecedent_parts[0]
        else:
            antecedent = _binary_chain("&", antecedent_parts)
        head_node = _formula_node(core.head)
        if head_node is None:
            return None
        implication = {"kind": "binary", "operator": "=>", "left": antecedent, "right": head_node}
        if core.variables:
            return {
                "kind": "quantified",
                "quantifier": "!",
                "variables": [{"name": variable.name, "type": "$i"} for variable in core.variables],
                "body": implication,
            }
        return implication
    return None


def _term_node(term):
    if isinstance(term, Constant):
        return {"kind": "constant", "value": term.name, "type": _fol_sort(term.sort)}
    if isinstance(term, Variable):
        return {"kind": "variable", "symbol": term.name, "type": _fol_sort(term.sort)}
    if isinstance(term, NumberLiteral):
        return {"kind": "constant", "value": term.value, "type": "$int"}
    if isinstance(term, ArithmeticExpression):
        return {
            "kind": "function",
            "symbol": term.operator,
            "arguments": [_term_node(item) for item in term.operands],
        }
    return {"kind": "constant", "value": str(term), "type": "$i"}


def _binary_chain(operator: str, nodes: list[dict[str, Any]]) -> dict[str, Any]:
    current = nodes[0]
    for node in nodes[1:]:
        current = {"kind": "binary", "operator": operator, "left": current, "right": node}
    return current


def _fol_sort(sort_name: str | None) -> str:
    if sort_name in {None, "", "entity"}:
        return "$i"
    return sort_name


def _collect_signature(node: dict[str, Any], predicates: set[str], constants: set[str]) -> None:
    kind = node.get("kind")
    if kind == "predicate":
        predicates.add(str(node.get("symbol", "")))
        for argument in node.get("arguments", []):
            _collect_signature(argument, predicates, constants)
        return
    if kind == "constant":
        constants.add(str(node.get("value", "")))
        return
    for key in ("arguments", "body", "left", "right"):
        value = node.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _collect_signature(item, predicates, constants)
        elif isinstance(value, dict):
            _collect_signature(value, predicates, constants)
    for item in node.get("variables", []):
        _collect_signature(item, predicates, constants) if isinstance(item, dict) else None


def _residue_notes(statement) -> list[str]:
    residue = statement.semantic_residue
    notes: list[str] = []
    if residue.modality:
        notes.append(f"Modal markers preserved alongside the formula: {', '.join(residue.modality)}.")
    if residue.uncertainty:
        notes.append(f"Uncertainty markers preserved outside the formal core: {', '.join(residue.uncertainty)}.")
    if residue.attribution:
        notes.append(f"Attribution preserved outside the formal core: {', '.join(residue.attribution)}.")
    if residue.unresolved_references:
        notes.append(f"Unresolved references remain in residue: {', '.join(residue.unresolved_references)}.")
    return notes


def _requires_partial_export(statement) -> bool:
    residue = statement.semantic_residue
    return any(
        (
            residue.uncertainty,
            residue.attribution,
            residue.temporal_vagueness,
            residue.unresolved_references,
            residue.non_formalized_fragments,
            residue.ambiguity,
        )
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped
