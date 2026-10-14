"""FOL-style export for Dialectica reasoning."""

from __future__ import annotations

from typing import Any

from .base import BaseExporter, CompilationResult, combine_status
from ..ir import (
    ArithmeticExpression,
    Atom,
    Comparison,
    Conjunction,
    Constant,
    Disjunction,
    ExportRecord,
    FormalCore,
    HybridDocument,
    HybridStatement,
    Implication,
    Negation,
    NumberLiteral,
    Quantified,
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
        program = {
            "dialect": "fol-safe-fragment",
            "facts": [],
            "rules": [],
            "query": None,
            "skipped": [],
        }

        for statement in document.statements:
            record, formula, program_entry = self._compile_statement(statement)
            records[statement.id] = record
            if formula is not None:
                formulas.append(formula)
                _collect_signature(formula["formula"], predicate_names, constant_names)
            if record.notes:
                notes.extend(record.notes)

            if statement.kind == "query" and program_entry is not None:
                program["query"] = program_entry
            elif statement.kind == "fact" and program_entry is not None:
                program["facts"].append(program_entry)
            elif statement.kind == "rule" and program_entry is not None:
                program["rules"].append(program_entry)
            elif program_entry is None and record.status != "exact":
                program["skipped"].append(
                    {
                        "statement_id": statement.id,
                        "status": record.status,
                        "notes": record.notes,
                    }
                )

        signature = {
            "types": [{"name": "$i", "kind": "built_in"}],
            "predicates": [
                {
                    "name": name,
                    "signature": "$i > $o",
                    "arity": 1,
                    "description": "Auto-generated from the hybrid AST.",
                }
                for name in sorted(predicate_names)
            ],
            "functions": [],
            "constants": [
                {
                    "name": name,
                    "signature": "$i",
                    "arity": 0,
                    "description": "Auto-generated constant from the hybrid AST.",
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
            "translation_notes": list(dict.fromkeys(notes)),
            "program": program,
        }
        return CompilationResult(
            target=self.target,
            status=combine_status(list(records.values())),
            artifact=artifact,
            notes=list(dict.fromkeys(notes)),
            statement_records=records,
        )

    def _compile_statement(self, statement: HybridStatement) -> tuple[ExportRecord, dict[str, Any] | None, dict[str, Any] | None]:
        notes = _residue_notes(statement)
        core = statement.formal_core
        if core is None:
            return ExportRecord(target=self.target, status="unsupported", notes=[*notes, "No formal core to export."]), None, None

        safe_for_program = not _requires_partial_export(statement)
        status = "partial" if not safe_for_program else "exact"
        formula = _formula_node(core)
        if formula is None:
            return ExportRecord(
                target=self.target,
                status="unsupported",
                notes=[*notes, "The FOL exporter could not compile this formal core."],
            ), None, None

        program_entry = _program_entry(statement)
        if isinstance(core, RuleCore) and core.exceptions:
            status = "partial"
            notes.append(
                "Rule exceptions were exported as guarded blockers in the machine program, which is only a partial match for richer defeasible semantics."
            )
        if isinstance(core, Comparison) and core.operator not in {"=", "!=", ">=", "<=", ">", "<"}:
            status = "unsupported"
            notes.append("The comparison operator is not part of the current safe FOL fragment.")
            program_entry = None
        if not safe_for_program or status == "unsupported":
            program_entry = None

        role = "conjecture" if statement.kind == "query" else "axiom"
        return (
            ExportRecord(target=self.target, status=status, notes=notes),
            {
                "name": statement.id,
                "language": "fof",
                "role": role,
                "linked_blocks": [],
                "source": {
                    "kind": "parser",
                    "reference": "controlled-heuristic-translator",
                    "details": {"sentence_id": statement.provenance.sentence_id},
                },
                "useful_info": [{"key": "source_fragment", "value": statement.provenance.fragment}],
                "confidence": statement.semantic_residue.confidence,
                "formula": formula,
            },
            program_entry,
        )


def _program_entry(statement: HybridStatement) -> dict[str, Any] | None:
    core = statement.formal_core
    if core is None:
        return None
    if statement.kind in {"fact", "query"}:
        literal = _literal_program_node_from_formula(core)
        if literal is None:
            return None
        return {"statement_id": statement.id, "literal": literal}
    if statement.kind == "rule":
        normalized = _normalize_rule_core(core)
        if normalized is None:
            return None
        head = _literal_program_node_from_formula(normalized["head"])
        if head is None:
            return None
        branches = []
        for branch in _antecedent_branches(normalized["antecedent"]):
            branch_literals = []
            for formula in branch:
                literal = _literal_program_node_from_formula(formula)
                if literal is None:
                    return None
                branch_literals.append(literal)
            branches.append(branch_literals)
        exceptions = []
        for item in normalized["exceptions"]:
            literal = _literal_program_node_from_formula(item)
            if literal is None:
                return None
            exceptions.append(literal)
        return {
            "statement_id": statement.id,
            "head": head,
            "branches": branches or [[]],
            "exceptions": exceptions,
        }
    return None


def _normalize_rule_core(core: FormalCore) -> dict[str, Any] | None:
    if isinstance(core, RuleCore):
        antecedent = _make_conjunction(core.body)
        return {
            "head": core.head,
            "antecedent": antecedent,
            "exceptions": list(core.exceptions),
        }
    if isinstance(core, Implication):
        return {
            "head": core.consequent,
            "antecedent": core.antecedent,
            "exceptions": [],
        }
    if isinstance(core, Quantified):
        if core.quantifier != "forall":
            return None
        return _normalize_rule_core(core.body)
    return None


def _antecedent_branches(formula: FormalCore | None) -> list[list[FormalCore]]:
    if formula is None:
        return [[]]
    if isinstance(formula, Conjunction):
        branches = [[]]
        for conjunct in formula.conjuncts:
            child_branches = _antecedent_branches(conjunct)
            branches = [current + child for current in branches for child in child_branches]
        return branches
    if isinstance(formula, Disjunction):
        branches: list[list[FormalCore]] = []
        for disjunct in formula.disjuncts:
            branches.extend(_antecedent_branches(disjunct))
        return branches
    if isinstance(formula, Quantified) and formula.quantifier == "forall":
        return _antecedent_branches(formula.body)
    if _literal_program_node_from_formula(formula) is not None:
        return [[formula]]
    return []


def _literal_program_node_from_formula(core: FormalCore) -> dict[str, Any] | None:
    if isinstance(core, Atom):
        return {"sign": "positive", "atom": _atom_program_node(core)}
    if isinstance(core, Negation):
        if isinstance(core.operand, Atom):
            return {"sign": "negative", "atom": _atom_program_node(core.operand)}
        if isinstance(core.operand, Comparison):
            return {"sign": "negative", "atom": _comparison_program_node(core.operand)}
        return None
    if isinstance(core, Comparison):
        return {"sign": "positive", "atom": _comparison_program_node(core)}
    return None


def _atom_program_node(atom: Atom) -> dict[str, Any]:
    return {
        "node_type": "Atom",
        "predicate": atom.predicate,
        "arguments": [_term_program_node(argument) for argument in atom.arguments],
    }


def _comparison_program_node(comparison: Comparison) -> dict[str, Any]:
    return {
        "node_type": "Comparison",
        "operator": comparison.operator,
        "left": _term_program_node(comparison.left),
        "right": _term_program_node(comparison.right),
    }


def _term_program_node(term) -> dict[str, Any]:
    if isinstance(term, Constant):
        return {"node_type": "Constant", "name": term.name, "sort": term.sort}
    if isinstance(term, Variable):
        return {"node_type": "Variable", "name": term.name, "sort": term.sort}
    if isinstance(term, NumberLiteral):
        return {"node_type": "NumberLiteral", "value": term.value}
    return {"node_type": "Constant", "name": str(term), "sort": None}


def _formula_node(core: FormalCore):
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
        return {
            "kind": "predicate",
            "symbol": f"cmp_{_comparison_symbol(core.operator)}",
            "arguments": [_term_node(core.left), _term_node(core.right)],
        }
    if isinstance(core, Conjunction):
        parts = [_formula_node(item) for item in core.conjuncts]
        if any(part is None for part in parts):
            return None
        return _binary_chain("&", [part for part in parts if part is not None])
    if isinstance(core, Disjunction):
        parts = [_formula_node(item) for item in core.disjuncts]
        if any(part is None for part in parts):
            return None
        return _binary_chain("|", [part for part in parts if part is not None])
    if isinstance(core, Implication):
        left = _formula_node(core.antecedent)
        right = _formula_node(core.consequent)
        if left is None or right is None:
            return None
        return {"kind": "binary", "operator": "=>", "left": left, "right": right}
    if isinstance(core, Quantified):
        body = _formula_node(core.body)
        if body is None:
            return None
        quantifier = "!" if core.quantifier == "forall" else "?"
        return {
            "kind": "quantified",
            "quantifier": quantifier,
            "variables": [{"name": variable.name, "type": "$i"} for variable in core.variables],
            "body": body,
        }
    if isinstance(core, RuleCore):
        normalized = _normalize_rule_core(core)
        if normalized is None:
            return None
        head = _formula_node(normalized["head"])
        antecedent = _formula_node(normalized["antecedent"]) if normalized["antecedent"] is not None else {"kind": "literal", "value": True}
        if head is None or antecedent is None:
            return None
        if normalized["exceptions"]:
            guarded_parts = [antecedent]
            for exception in normalized["exceptions"]:
                exception_node = _formula_node(Negation(exception))
                if exception_node is not None:
                    guarded_parts.append(exception_node)
            antecedent = _binary_chain("&", guarded_parts)
        implication = {"kind": "binary", "operator": "=>", "left": antecedent, "right": head}
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
    if not nodes:
        return {"kind": "literal", "value": True}
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
        if isinstance(item, dict):
            _collect_signature(item, predicates, constants)


def _residue_notes(statement: HybridStatement) -> list[str]:
    residue = statement.semantic_residue
    notes: list[str] = []
    if residue.modality:
        notes.append(f"Modal markers preserved alongside the formula: {', '.join(residue.modality)}.")
    if residue.uncertainty:
        notes.append(f"Uncertainty markers preserved outside the formal core: {', '.join(residue.uncertainty)}.")
    if residue.attribution:
        notes.append(f"Attribution preserved outside the formal core: {', '.join(residue.attribution)}.")
    if residue.temporal_vagueness:
        notes.append(f"Temporal vagueness preserved outside the formal core: {', '.join(residue.temporal_vagueness)}.")
    if residue.unresolved_references:
        notes.append(f"Unresolved references remain in residue: {', '.join(residue.unresolved_references)}.")
    if residue.non_formalized_fragments:
        notes.append("Some source fragments were intentionally left outside the formal core.")
    if residue.ambiguity:
        notes.append(f"Ambiguity notes remain explicit: {', '.join(residue.ambiguity)}.")
    return notes


def _requires_partial_export(statement: HybridStatement) -> bool:
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


def _comparison_symbol(operator: str) -> str:
    return {
        "=": "eq",
        "!=": "neq",
        ">=": "gte",
        "<=": "lte",
        ">": "gt",
        "<": "lt",
    }.get(operator, "cmp")


def _make_conjunction(items: tuple[Any, ...]) -> FormalCore | None:
    if not items:
        return None
    if len(items) == 1:
        return items[0]
    return Conjunction(conjuncts=items)
