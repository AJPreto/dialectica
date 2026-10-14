"""Dialectica logical-form toolkit.

Typical use::

    import dialectica

    form = dialectica.parse("If the battery is dead, the car will not start.")
    run = dialectica.reason("Alice completed orientation. If Alice completed orientation, "
                            "then Alice holds a badge. Does Alice hold a badge?")
    run.answer  # "entailed"
"""

from importlib.metadata import PackageNotFoundError, version

from .canonical import canonicalize_logical_form, serialize_compact_logical_form, serialize_logical_form
from .compiler import SUPPORTED_EXPORT_TARGETS, compile_hybrid_document
from .engine import FOLReasoningResult, ReasoningResult, reason_over_fol_program, reason_over_horn_program
from .explainer import explain_fol_reasoning, explain_reasoning
from .filtering import filter_logical_form
from .fingerprint import compare_fingerprints, fingerprint_logical_form, summarize_fingerprint
from .ir import HybridDocument, HybridStatement, ir_to_dict
from .parser import parse, parse_document, parse_text
from .pipeline import ReasoningRun, reason, run_reasoner
from .translator import translate_text
from .validation import validate_logical_form

try:
    __version__ = version("dialectica")
except PackageNotFoundError:  # running from a source checkout without installation
    __version__ = "0.0.0"

__all__ = [
    "FOLReasoningResult",
    "HybridDocument",
    "HybridStatement",
    "ReasoningResult",
    "ReasoningRun",
    "SUPPORTED_EXPORT_TARGETS",
    "__version__",
    "canonicalize_logical_form",
    "compare_fingerprints",
    "compile_hybrid_document",
    "explain_fol_reasoning",
    "explain_reasoning",
    "filter_logical_form",
    "fingerprint_logical_form",
    "ir_to_dict",
    "parse",
    "parse_document",
    "parse_text",
    "reason",
    "reason_over_fol_program",
    "reason_over_horn_program",
    "run_reasoner",
    "serialize_compact_logical_form",
    "serialize_logical_form",
    "summarize_fingerprint",
    "translate_text",
    "validate_logical_form",
]
