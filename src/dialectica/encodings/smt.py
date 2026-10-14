"""Partial SMT-style export for Dialectica reasoning."""

from __future__ import annotations

from .base import BaseExporter, CompilationResult, combine_status
from ..ir import Comparison, ExportRecord, HybridDocument, NumberLiteral

_SMT_OPERATORS = {"=": "=", "!=": "distinct", ">": ">", "<": "<", ">=": ">=", "<=": "<="}


class SMTExporter(BaseExporter):
    target = "smt"

    def compile(self, document: HybridDocument) -> CompilationResult:
        assertions: list[str] = []
        records: dict[str, ExportRecord] = {}
        notes: list[str] = []

        for statement in document.statements:
            core = statement.formal_core
            if isinstance(core, Comparison):
                operator = _SMT_OPERATORS.get(core.operator, "=")
                assertions.append(f"(assert ({operator} {_smt_value(core.left)} {_smt_value(core.right)}))")
                records[statement.id] = ExportRecord(target=self.target, status="exact", notes=[])
                continue
            records[statement.id] = ExportRecord(
                target=self.target,
                status="unsupported",
                notes=["The first SMT exporter only handles standalone comparison statements."],
            )
            notes.append("The SMT path is available as a partial export target for arithmetic and constraint work.")

        artifact = {
            "dialect": "smtlib2",
            "assertions": assertions,
        }
        return CompilationResult(
            target=self.target,
            status=combine_status(list(records.values())),
            artifact=artifact,
            notes=list(dict.fromkeys(notes)),
            statement_records=records,
        )


def _smt_value(value) -> str:
    if isinstance(value, NumberLiteral):
        return str(value.value)
    return str(getattr(value, "name", value))
