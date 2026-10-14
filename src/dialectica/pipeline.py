"""One-call reasoning pipeline: translate, compile, reason, explain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .compiler import SUPPORTED_EXPORT_TARGETS, compile_hybrid_document
from .engine import FOLReasoningResult, ReasoningResult, reason_over_fol_program, reason_over_horn_program
from .explainer import explain_fol_reasoning, explain_reasoning
from .ir import HybridDocument, ir_to_dict
from .translator import translate_text

Reasoner = Literal["horn", "fol"]


@dataclass
class ReasoningRun:
    reasoner: Reasoner
    document: HybridDocument
    compiled: dict[str, Any]
    result: ReasoningResult | FOLReasoningResult
    explanation: str

    @property
    def answer(self) -> str:
        return self.result.answer

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoner": self.reasoner,
            "hybrid_document": ir_to_dict(self.document),
            "compiled": self.compiled,
            "reasoning": self.result.to_dict(),
            "explanation": self.explanation,
        }


def reason(
    text: str,
    query: str | None = None,
    *,
    reasoner: Reasoner = "horn",
    targets: tuple[str, ...] = SUPPORTED_EXPORT_TARGETS,
) -> ReasoningRun:
    """Translate ``text`` and answer ``query`` (or the last question in ``text``).

    ``targets`` controls which export artifacts are compiled; the selected
    reasoner's target is always included.
    """
    if reasoner not in targets:
        targets = (*targets, reasoner)
    document, compiled = compile_hybrid_document(translate_text(text, query=query), targets=targets)
    return run_reasoner(document, compiled, reasoner)


def run_reasoner(document: HybridDocument, compiled: dict[str, Any], reasoner: Reasoner) -> ReasoningRun:
    """Run a reasoner over an already compiled document."""
    if reasoner == "fol":
        result = reason_over_fol_program(compiled.get("fol", {}).get("artifact", {}).get("program", {}))
        explanation = explain_fol_reasoning(document, result)
    elif reasoner == "horn":
        result = reason_over_horn_program(compiled.get("horn", {}).get("artifact", {}))
        explanation = explain_reasoning(document, result)
    else:
        raise ValueError(f"Unsupported reasoner '{reasoner}'. Supported reasoners: horn, fol.")
    return ReasoningRun(reasoner, document, compiled, result, explanation)
