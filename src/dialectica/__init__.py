"""Dialectica logical-form toolkit."""

from .canonical import canonicalize_logical_form, serialize_logical_form
from .compiler import compile_hybrid_document
from .engine import reason_over_horn_program
from .explainer import explain_reasoning
from .fingerprint import compare_fingerprints, fingerprint_logical_form, summarize_fingerprint
from .translator import translate_text
from .parser import parse_document, parse_text
from .validation import validate_logical_form

__all__ = [
    "canonicalize_logical_form",
    "compile_hybrid_document",
    "compare_fingerprints",
    "explain_reasoning",
    "fingerprint_logical_form",
    "parse_document",
    "parse_text",
    "reason_over_horn_program",
    "serialize_logical_form",
    "summarize_fingerprint",
    "translate_text",
    "validate_logical_form",
]
