"""Gödel-inspired structural fingerprints for Dialectica logical forms."""

from __future__ import annotations

import math
import re
from typing import Any

from .canonical import canonicalize_logical_form


MODULI = (1_000_003, 1_000_033, 1_000_037)
DEFAULT_SKETCH_SIZE = 24
DEFAULT_EXACT_LIMIT = 18
_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


def fingerprint_logical_form(
    logical_form: dict[str, Any],
    *,
    sketch_size: int = DEFAULT_SKETCH_SIZE,
    exact_limit: int = DEFAULT_EXACT_LIMIT,
) -> dict[str, Any]:
    """Build a Gödel-inspired structural fingerprint for a logical form.

    This is intentionally not a raw Gödel number used directly as an embedding.
    Instead, it uses Gödel-style symbol numbering and prime-based sequence coding
    to derive stable structural signatures and a fixed-width sketch suitable for
    approximate similarity comparisons.
    """
    canonical = canonicalize_logical_form(logical_form)
    block_lookup = {block["id"]: block for block in canonical.get("blocks", [])}

    block_entries = [
        _encode_entry(
            block["id"],
            block["type"],
            _block_symbols(block),
            item_kind="block",
            exact_limit=exact_limit,
        )
        for block in canonical.get("blocks", [])
    ]
    relation_entries = [
        _encode_entry(
            f'{relation["source"]}->{relation["target"]}',
            relation["type"],
            _relation_symbols(relation, block_lookup),
            item_kind="relation",
            exact_limit=exact_limit,
        )
        for relation in canonical.get("relations", [])
    ]
    ambiguity_entries = [
        _encode_entry(
            ambiguity["id"],
            "ambiguity",
            _ambiguity_symbols(ambiguity),
            item_kind="ambiguity",
            exact_limit=exact_limit,
        )
        for ambiguity in canonical.get("ambiguities", [])
    ]
    all_symbols = sorted(
        {
            symbol
            for entry in [*block_entries, *relation_entries, *ambiguity_entries]
            for symbol in entry["symbol_sequence"]
        }
    )
    symbol_table = {symbol: index + 1 for index, symbol in enumerate(all_symbols)}

    for entry in [*block_entries, *relation_entries, *ambiguity_entries]:
        _finalize_entry(entry, symbol_table, exact_limit=exact_limit)

    graph_entry = _encode_entry(
        "graph",
        "graph",
        _graph_symbols(canonical, block_entries, relation_entries, ambiguity_entries),
        item_kind="graph",
        exact_limit=exact_limit,
    )
    for symbol in graph_entry["symbol_sequence"]:
        if symbol not in symbol_table:
            symbol_table[symbol] = len(symbol_table) + 1
    _finalize_entry(graph_entry, symbol_table, exact_limit=exact_limit)

    sketch = _build_sketch([*block_entries, *relation_entries, *ambiguity_entries, graph_entry], sketch_size=sketch_size)

    return {
        "scheme": "godel-inspired",
        "symbol_table": symbol_table,
        "graph": _export_entry(graph_entry),
        "blocks": [_export_entry(entry) for entry in block_entries],
        "relations": [_export_entry(entry) for entry in relation_entries],
        "ambiguities": [_export_entry(entry) for entry in ambiguity_entries],
        "sketch": sketch,
        "metadata": {
            "sketch_size": sketch_size,
            "exact_limit": exact_limit,
            "symbol_count": len(symbol_table),
            "block_count": len(block_entries),
            "relation_count": len(relation_entries),
            "ambiguity_count": len(ambiguity_entries),
        },
    }


def summarize_fingerprint(fingerprint: dict[str, Any]) -> dict[str, Any]:
    """Return a concise summary suitable for prompts and reports."""
    return {
        "scheme": fingerprint["scheme"],
        "graph_signature": fingerprint["graph"]["signature"],
        "graph_residues": fingerprint["graph"]["residues"],
        "sketch": fingerprint["sketch"],
        "block_signatures": [
            {
                "id": block["id"],
                "type": block["label"],
                "signature": block["signature"],
            }
            for block in fingerprint.get("blocks", [])
        ],
        "relation_signatures": [
            {
                "id": relation["id"],
                "type": relation["label"],
                "signature": relation["signature"],
            }
            for relation in fingerprint.get("relations", [])
        ],
        "metadata": fingerprint.get("metadata", {}),
    }


def compare_fingerprints(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Compare two fingerprints using sketch cosine similarity."""
    left_vector = left.get("sketch", [])
    right_vector = right.get("sketch", [])
    numerator = sum(a * b for a, b in zip(left_vector, right_vector, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left_vector))
    right_norm = math.sqrt(sum(b * b for b in right_vector))
    cosine = numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0
    return {
        "cosine_similarity": round(cosine, 6),
        "left_graph_signature": left.get("graph", {}).get("signature"),
        "right_graph_signature": right.get("graph", {}).get("signature"),
    }


def _encode_entry(identifier: str, label: str, symbol_sequence: list[str], *, item_kind: str, exact_limit: int) -> dict[str, Any]:
    return {
        "id": identifier,
        "label": label,
        "item_kind": item_kind,
        "symbol_sequence": symbol_sequence,
        "symbol_ids": [],
        "residues": {},
        "signature": "",
        "exact_code": None,
        "log_magnitude": 0.0,
        "exact_limit": exact_limit,
    }


def _finalize_entry(entry: dict[str, Any], symbol_table: dict[str, int], *, exact_limit: int) -> None:
    symbol_ids = [symbol_table[symbol] for symbol in entry["symbol_sequence"]]
    encoding = _encode_sequence(symbol_ids, exact_limit=exact_limit)
    entry["symbol_ids"] = symbol_ids
    entry["residues"] = encoding["residues"]
    entry["signature"] = encoding["signature"]
    entry["exact_code"] = encoding["exact_code"]
    entry["log_magnitude"] = encoding["log_magnitude"]


def _export_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry["id"],
        "label": entry["label"],
        "item_kind": entry["item_kind"],
        "signature": entry["signature"],
        "residues": entry["residues"],
        "exact_code": entry["exact_code"],
        "log_magnitude": entry["log_magnitude"],
        "symbol_sequence": entry["symbol_sequence"],
        "symbol_ids": entry["symbol_ids"],
    }


def _encode_sequence(symbol_ids: list[int], *, exact_limit: int) -> dict[str, Any]:
    if not symbol_ids:
        return {
            "exact_code": "1",
            "residues": {str(modulus): 1 for modulus in MODULI},
            "log_magnitude": 0.0,
            "signature": "000000-000000-000000",
        }

    primes = _first_primes(len(symbol_ids))
    residues = {
        str(modulus): _prime_power_code(symbol_ids, primes, modulus=modulus)
        for modulus in MODULI
    }
    exact_code = None
    if len(symbol_ids) <= exact_limit:
        exact_code = str(_prime_power_code(symbol_ids, primes, modulus=None))
    log_magnitude = round(sum(math.log(prime) * exponent for prime, exponent in zip(primes, symbol_ids)), 6)
    signature = "-".join(_base36(residues[str(modulus)])[-6:].rjust(6, "0") for modulus in MODULI)
    return {
        "exact_code": exact_code,
        "residues": residues,
        "log_magnitude": log_magnitude,
        "signature": signature,
    }


def _prime_power_code(symbol_ids: list[int], primes: list[int], *, modulus: int | None) -> int:
    value = 1
    for prime, exponent in zip(primes, symbol_ids):
        if modulus is None:
            value *= prime**exponent
        else:
            value = (value * pow(prime, exponent, modulus)) % modulus
    return value


def _build_sketch(entries: list[dict[str, Any]], *, sketch_size: int) -> list[float]:
    vector = [0.0] * sketch_size
    weights = {"graph": 2.0, "relation": 1.35, "block": 1.0, "ambiguity": 0.8}
    for entry in entries:
        weight = weights.get(entry["item_kind"], 1.0)
        residues = [entry["residues"][str(modulus)] for modulus in MODULI]
        for index, residue in enumerate(residues):
            slot = (residue + 7 * index) % sketch_size
            sign = 1.0 if ((residue // sketch_size) % 2 == 0) else -1.0
            vector[slot] += sign * weight
    return [round(value, 6) for value in vector]


def _graph_symbols(
    canonical: dict[str, Any],
    block_entries: list[dict[str, Any]],
    relation_entries: list[dict[str, Any]],
    ambiguity_entries: list[dict[str, Any]],
) -> list[str]:
    symbols = [
        "GRAPH",
        f'STATUS:{canonical.get("parse_status", "ok")}',
        f'BLOCKS:{len(block_entries)}',
        f'RELATIONS:{len(relation_entries)}',
        f'AMBIGUITIES:{len(ambiguity_entries)}',
    ]
    for entry in block_entries:
        symbols.extend(["NODE", f'NODE_LABEL:{entry["label"]}', f'NODE_SIG:{entry["signature"] or "pending"}'])
    for entry in relation_entries:
        symbols.extend(["EDGE", f'EDGE_LABEL:{entry["label"]}', f'EDGE_SIG:{entry["signature"] or "pending"}'])
    return symbols


def _block_symbols(block: dict[str, Any]) -> list[str]:
    symbols = [
        "BLOCK",
        f'TYPE:{block["type"]}',
        f'POL:{block.get("polarity", "neutral")}',
    ]
    if block.get("certainty") is not None:
        bucket = int(float(block["certainty"]) * 10)
        symbols.append(f"CERT:{bucket}")
    tokens = _text_tokens(block.get("canonical_text", block.get("text", "")))
    symbols.extend(["TEXT_START", *[f"TOK:{token}" for token in tokens], "TEXT_END"])
    return symbols


def _relation_symbols(relation: dict[str, Any], block_lookup: dict[str, dict[str, Any]]) -> list[str]:
    source_block = block_lookup.get(relation["source"], {})
    target_block = block_lookup.get(relation["target"], {})
    symbols = [
        "REL",
        f'TYPE:{relation["type"]}',
        f'SRC_TYPE:{source_block.get("type", "unknown")}',
        f'TGT_TYPE:{target_block.get("type", "unknown")}',
        f'SRC_POL:{source_block.get("polarity", "unknown")}',
        f'TGT_POL:{target_block.get("polarity", "unknown")}',
    ]
    return symbols


def _ambiguity_symbols(ambiguity: dict[str, Any]) -> list[str]:
    symbols = ["AMBIG", f'AFFECTED:{len(ambiguity.get("affected_blocks", []))}']
    symbols.extend(f"TOK:{token}" for token in _text_tokens(ambiguity.get("description", "")))
    return symbols


def _text_tokens(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.casefold())


def _first_primes(count: int) -> list[int]:
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if _is_prime(candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value == 2:
        return True
    if value % 2 == 0:
        return False
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def _base36(value: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if value == 0:
        return "0"
    result = ""
    remaining = value
    while remaining:
        remaining, digit = divmod(remaining, 36)
        result = digits[digit] + result
    return result
