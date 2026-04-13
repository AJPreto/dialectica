"""Partial SMT-style export for the experimental Dialectica V2 path."""

from __future__ import annotations

from .base import BaseExporter, CompilationResult, combine_status
from ..ir import Comparison, ExportRecord, HybridDocument


class SMTExporter(BaseExporter):
    target = "smt"

    def compile(self, document: HybridDocument) -> CompilationResult:
        assertions: list[str] = []
        records: dict[str, ExportRecord] = {}
        notes: list[str] = []

        for statement in document.statements:
            core = statement.formal_core
            if isinstance(core, Comparison):
                assertion = f"(assert ({_smt_operator(core.operator)} {core.left.name if hasattr(core.left, 'name') else core.left.value} {core.right.value if hasattr(core.right, 'value') else core.right}))"
                assertions.append(assertion)
                records[statement.id] = ExportRecord(target=self.target, status="exact", notes=[])
                continue
            records[statement.id] = ExportRecord(
                target=self.target,
                status="unsupported",
                notes=["The first SMT exporter only handles standalone comparison statements."],
            )
            notes.append("The SMT path is present experimentally but is not yet the default end-to-end backend.")

        artifact = {
            "dialect": "smtlib2",
            "assertions": assertions,
        }
        return CompilationResult(
            target=self.target,
            status=combine_status(list(records.values())),
            artifact=artifact,
            notes=_dedupe(notes),
            statement_records=records,
        )


def _smt_operator(operator: str) -> str:
    return {"=": "=", "!=": "distinct", ">": ">", "<": "<", ">=": ">=", "<=": "<="}.get(operator, "=")


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped
