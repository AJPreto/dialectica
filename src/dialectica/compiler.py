"""Compiler entry points for the experimental Dialectica V2 path."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .encodings import FOLExporter, HornExporter, SMTExporter
from .ir import HybridDocument, ir_to_dict


EXPORTERS = {
    "horn": HornExporter(),
    "fol": FOLExporter(),
    "smt": SMTExporter(),
}
SUPPORTED_EXPORT_TARGETS = tuple(EXPORTERS)


def compile_hybrid_document(document: HybridDocument, targets: tuple[str, ...] = ("horn", "fol", "smt")) -> tuple[HybridDocument, dict[str, Any]]:
    compiled_document = deepcopy(document)
    compiled_outputs: dict[str, Any] = {}

    for target in targets:
        exporter = EXPORTERS.get(target)
        if exporter is None:
            supported = ", ".join(SUPPORTED_EXPORT_TARGETS)
            raise ValueError(f"Unsupported export target '{target}'. Supported targets: {supported}.")
        result = exporter.compile(compiled_document)
        compiled_outputs[target] = {
            "status": result.status,
            "artifact": result.artifact,
            "notes": result.notes,
        }
        for statement in compiled_document.statements:
            record = result.statement_records.get(statement.id)
            if record is not None:
                statement.exportability[target] = record

    return compiled_document, compiled_outputs


def compiled_document_to_dict(document: HybridDocument) -> dict[str, Any]:
    return ir_to_dict(document)
