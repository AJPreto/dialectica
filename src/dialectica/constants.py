"""Shared enums and defaults for Dialectica."""

BLOCK_TYPES = (
    "claim",
    "goal",
    "constraint",
    "condition",
    "outcome",
    "evidence",
    "definition",
    "question",
    "exception",
    "unknown",
    "ambiguity",
)

RELATION_TYPES = (
    "supports",
    "contradicts",
    "implies",
    "depends_on",
    "defines",
    "qualifies",
    "unless",
    "answers",
)

PARSE_STATUSES = (
    "ok",
    "ambiguous",
    "underspecified",
    "failed",
)

POLARITIES = (
    "positive",
    "negative",
    "neutral",
    "unknown",
)

