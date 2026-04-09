"""Dialectica prototype package."""

from .canonical import canonicalize_logical_form, serialize_logical_form
from .fingerprint import compare_fingerprints, fingerprint_logical_form, summarize_fingerprint
from .parser import parse_document, parse_text
from .validation import validate_logical_form

__all__ = [
    "canonicalize_logical_form",
    "compare_fingerprints",
    "fingerprint_logical_form",
    "parse_document",
    "parse_text",
    "serialize_logical_form",
    "summarize_fingerprint",
    "validate_logical_form",
]
