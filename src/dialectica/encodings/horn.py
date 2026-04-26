"""Horn-style export for Dialectica reasoning."""

from __future__ import annotations

from typing import Any

from .base import BaseExporter, CompilationResult, combine_status
from ..ir import (
    Atom,
    Comparison,
    ExportRecord,
    HybridDocument,
    HybridStatement,
    Negation,
    RuleCore,
    ir_to_dict,
)


class HornExporter(BaseExporter):
    target = "horn"

    def compile(self, document: HybridDocument) -> CompilationResult:
        facts: list[dict[str, Any]] = []
        rules: list[dict[str, Any]] = []
        query: dict[str, Any] | None = None
        skipped: list[dict[str, Any]] = []
        statement_records: dict[str, ExportRecord] = {}

        for statement in document.statements:
            record, exported = self._compile_statement(statement)
            statement_records[statement.id] = record
            if statement.kind == "query" and exported is not None:
                query = exported
                continue
            if exported is None:
                skipped.append(
                    {
                        "statement_id": statement.id,
                        "status": record.status,
                        "notes": record.notes,
                    }
                )
                continue
            if statement.kind == "fact":
                facts.append(exported)
            elif statement.kind == "rule":
                rules.append(exported)

        records = list(statement_records.values())
        artifact = {
            "dialect": "horn",
            "facts": facts,
            "rules": rules,
            "query": query,
            "skipped": skipped,
        }
        notes: list[str] = []
        if skipped:
            notes.append("Some statements were withheld from Horn reasoning because the export would have been unsafe or unsupported.")
        return CompilationResult(
            target=self.target,
            status=combine_status(records),
            artifact=artifact,
            notes=notes,
            statement_records=statement_records,
        )

    def _compile_statement(self, statement: HybridStatement) -> tuple[ExportRecord, dict[str, Any] | None]:
        notes = _residue_notes(statement)
        core = statement.formal_core
        if core is None:
            return ExportRecord(target=self.target, status="unsupported", notes=[*notes, "No formal core to export."]), None

        if statement.kind == "query":
            if isinstance(core, Atom):
                status = "partial" if notes else "exact"
                return (
                    ExportRecord(target=self.target, status=status, notes=notes),
                    {"statement_id": statement.id, "atom": ir_to_dict(core)},
                )
            return ExportRecord(target=self.target, status="unsupported", notes=[*notes, "Horn queries currently require a single atom."]), None

        if isinstance(core, Negation):
            return ExportRecord(
                target=self.target,
                status="unsupported",
                notes=[*notes, "Explicit negation is not part of the first Horn backend slice."],
            ), None

        if isinstance(core, Comparison):
            return ExportRecord(
                target=self.target,
                status="unsupported",
                notes=[*notes, "Arithmetic and inequality reasoning are reserved for a future SMT path."],
            ), None

        if statement.kind == "fact" and isinstance(core, Atom):
            if notes:
                return ExportRecord(
                    target=self.target,
                    status="partial",
                    notes=[*notes, "The fact was preserved in the AST but withheld from Horn reasoning."],
                ), None
            return ExportRecord(target=self.target, status="exact", notes=[]), {
                "statement_id": statement.id,
                "atom": ir_to_dict(core),
            }

        if statement.kind == "rule" and isinstance(core, RuleCore):
            if not isinstance(core.head, Atom):
                return ExportRecord(
                    target=self.target,
                    status="unsupported",
                    notes=[*notes, "Horn rules currently require an atomic head."],
                ), None
            if any(not isinstance(item, Atom) for item in (*core.body, *core.exceptions)):
                return ExportRecord(
                    target=self.target,
                    status="unsupported",
                    notes=[*notes, "Horn rules currently require atomic body literals and guarded atomic exceptions."],
                ), None
            if notes:
                return ExportRecord(
                    target=self.target,
                    status="partial",
                    notes=[*notes, "The rule was preserved in the AST but withheld from Horn reasoning."],
                ), None
            return ExportRecord(target=self.target, status="exact", notes=[]), {
                "statement_id": statement.id,
                "head": ir_to_dict(core.head),
                "body": [ir_to_dict(item) for item in core.body],
                "exceptions": [ir_to_dict(item) for item in core.exceptions],
                "variables": [ir_to_dict(variable) for variable in core.variables],
            }

        return ExportRecord(
            target=self.target,
            status="unsupported",
            notes=[*notes, "The Horn exporter could not map this statement kind."],
        ), None


def _residue_notes(statement: HybridStatement) -> list[str]:
    residue = statement.semantic_residue
    notes: list[str] = []
    if residue.uncertainty:
        notes.append(f"Uncertainty markers present: {', '.join(residue.uncertainty)}.")
    if residue.attribution:
        notes.append(f"Attribution markers present: {', '.join(residue.attribution)}.")
    if residue.ambiguity:
        notes.append(f"Ambiguity notes present: {', '.join(residue.ambiguity)}.")
    if residue.temporal_vagueness:
        notes.append(f"Temporal vagueness present: {', '.join(residue.temporal_vagueness)}.")
    if residue.unresolved_references:
        notes.append(f"Unresolved references present: {', '.join(residue.unresolved_references)}.")
    if residue.non_formalized_fragments:
        notes.append("Some source fragments could not be formalized safely.")
    return notes
