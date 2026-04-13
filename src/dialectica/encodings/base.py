"""Shared encoding interfaces for Dialectica V2 exporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..ir import ExportRecord


@dataclass
class CompilationResult:
    target: str
    status: str
    artifact: dict[str, Any]
    notes: list[str] = field(default_factory=list)
    statement_records: dict[str, ExportRecord] = field(default_factory=dict)


class BaseExporter:
    target = "base"

    def compile(self, document) -> CompilationResult:
        raise NotImplementedError


def combine_status(records: list[ExportRecord]) -> str:
    """Collapse per-statement statuses into a single exporter status."""
    if not records:
        return "unsupported"
    if all(record.status == "exact" for record in records):
        return "exact"
    if any(record.status == "partial" for record in records):
        return "partial"
    if any(record.status == "lossy" for record in records):
        return "lossy"
    if any(record.status == "exact" for record in records):
        return "partial"
    return "unsupported"

