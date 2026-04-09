# Structural Fingerprint

Dialectica now includes a Gödel-inspired structural fingerprint backend.

This backend is not meant to replace the logical representation. It is an
auxiliary route that adds:

- stable symbolic numbering
- prime-based sequence coding
- compact structural signatures
- a fixed-width sketch for approximate similarity

## Why this exists

The canonical logical serialization is readable and useful for prompting, but it
is still mostly text. The structural fingerprint makes logical shape more
explicit while staying lighter than a full theorem-prover export.

It is designed for:

- structural deduplication
- contradiction and near-contradiction fingerprints
- retrieval experiments that care about logical shape
- auxiliary prompt context alongside the main logical form

## Why it is only auxiliary

A raw Gödel number is excellent for exact coding, but poor as a similarity
embedding on its own. Small syntactic changes can create large numeric changes.

Dialectica therefore uses a hybrid approach:

1. logical form as the primary representation
2. structural fingerprint as an auxiliary representation

## What the backend emits

For a logical form, the fingerprint module produces:

- `symbol_table`: deterministic symbol-to-id mapping
- `graph`: graph-level signature and residues
- `blocks`: block-level signatures
- `relations`: relation-level signatures
- `sketch`: fixed-width structural sketch

## Encoding strategy

The current version uses:

- deterministic symbol extraction from canonical logical forms
- stable symbol numbering
- Gödel-style prime power sequence coding
- modular residues for manageable signatures
- a hashed sketch derived from block, relation, and graph signatures

That means it is:

- deterministic
- reversible only partially
- exact enough for structural identity signals
- compact enough for approximate comparison

## CLI

Generate a fingerprint:

```bash
uv run dialectica fingerprint "If the battery is dead, the car will not start unless we jump it." --summary --pretty
```

Compare two fingerprints:

```bash
uv run dialectica compare-fingerprints "If the battery is dead, the car will not start." "If the battery is dead, the car will start." --pretty
```

## In answer evaluation

The end-to-end evaluator now includes:

- `dialectica_parsed`
- `dialectica_structural`
- optionally `dialectica_gold`
- optionally `dialectica_gold_structural`

This lets you test whether the auxiliary structural route helps compared with
the current logic-only route.
