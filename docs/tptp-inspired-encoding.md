# TPTP-Inspired Encoding

Dialectica's original schema captures logical blocks and relations well, but it
is intentionally lightweight. This encoding layer adds a more formal target that
is inspired by TPTP without forcing every natural-language utterance into strict
theorem-prover syntax.

## Why use TPTP ideas here

TPTP contributes several useful concepts:

- annotated formulae with a stable envelope
- explicit formula roles such as `axiom`, `definition`, and `conjecture`
- typed symbol declarations
- explicit quantifiers and connectives
- provenance fields like source and useful metadata

For Dialectica, those ideas are valuable because they let us move from
retrieval-oriented semantic blocks toward proof-oriented encodings when needed.

## Dialectica mapping

### Top-level encoding object

The top-level `encoding` field is optional and sits alongside:

- `source_text`
- `blocks`
- `relations`
- `ambiguities`

This lets us preserve both:

- the high-level natural-language decomposition
- the lower-level formal or semi-formal encoding

### Annotated formulae

Each encoded formula follows a TPTP-like envelope:

```json
{
  "name": "remote_work_policy",
  "language": "tff",
  "role": "conjecture",
  "formula": { "...": "..." },
  "linked_blocks": ["b1", "b2"],
  "source": {
    "kind": "parser",
    "reference": "heuristic"
  },
  "useful_info": [
    {"key": "origin", "value": "natural-language parse"}
  ],
  "confidence": 0.72
}
```

`linked_blocks` is a Dialectica addition. It keeps the formal layer connected to
the original block graph.

### Signature

The `signature` section declares:

- types
- predicates
- functions
- constants

This allows a later theorem-prover backend to reconstruct declarations while
still letting the parser work from natural language first.

### Formula AST

The `formula` field stores a JSON AST rather than raw TPTP strings. That makes
it safer for downstream code generation and easier to canonicalize.

Supported node shapes include:

- `predicate`
- `function`
- `variable`
- `constant`
- `quantified`
- `unary`
- `binary`
- `equality`
- `inequality`
- `tuple`
- `if_then_else`
- `let`

These cover the most relevant TPTP-style building blocks for a future FOF, TFF,
or TXF exporter.

## Recommended usage

Use the richer encoding when you need:

- export toward theorem-prover formats
- contradiction checks with typed symbols
- provenance-aware inference traces
- explicit variable binding and quantifier scope

Stay with the simpler block graph when you need:

- fast prompt decomposition
- retrieval and memory indexing
- ambiguity preservation without overcommitting to formalization

## Example

```json
{
  "encoding": {
    "dialect": "tff",
    "logic": {
      "name": "typed_first_order",
      "typed": true,
      "higher_order": false,
      "supports_arithmetic": false,
      "supports_conditionals": false,
      "supports_lets": false
    },
    "signature": {
      "types": [
        {"name": "$i", "kind": "built_in"}
      ],
      "predicates": [
        {
          "name": "improves_productivity",
          "signature": "$i > $o",
          "arity": 1
        },
        {
          "name": "allow_remote_work",
          "signature": "$o",
          "arity": 0
        }
      ]
    },
    "annotated_formulae": [
      {
        "name": "policy_rule",
        "language": "tff",
        "role": "conjecture",
        "linked_blocks": ["b1", "b2"],
        "source": {
          "kind": "parser",
          "reference": "heuristic"
        },
        "confidence": 0.71,
        "formula": {
          "kind": "binary",
          "operator": "=>",
          "left": {
            "kind": "predicate",
            "symbol": "improves_productivity",
            "arguments": [
              {"kind": "constant", "value": "remote_work", "type": "$i"}
            ]
          },
          "right": {
            "kind": "predicate",
            "symbol": "allow_remote_work",
            "arguments": []
          }
        }
      }
    ],
    "translation_notes": [
      "Natural language deontic force was approximated as a conjecture."
    ]
  }
}
```

## Important constraint

This is deliberately TPTP-inspired, not full TPTP compliance. Natural-language
inputs often contain ambiguity, defeasibility, or pragmatics that theorem-prover
formats do not represent directly. Dialectica keeps those signals in the block
graph and uses the richer encoding as an optional bridge layer.
