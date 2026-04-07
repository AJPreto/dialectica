"""Dialectica prototype package."""

from .canonical import canonicalize_logical_form, serialize_logical_form
from .parser import parse_text
from .validation import validate_logical_form

__all__ = [
    "canonicalize_logical_form",
    "parse_text",
    "serialize_logical_form",
    "validate_logical_form",
]

