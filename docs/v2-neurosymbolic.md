# V2 Neuro-Symbolic Path

Dialectica V1 is a typed logical-block and retrieval-oriented system.
Dialectica V2 is an experimental parallel path that adds a stronger
neuro-symbolic stack:

```text
natural language
  -> controlled translator
  -> hybrid AST
  -> pluggable exports
  -> symbolic reasoning backend
  -> natural-language explanation
```

## Design goals

- preserve V1 intact
- keep the internal IR stable even while export targets change
- formalize as much as is safe
- keep ambiguity and other residue explicit
- prefer deterministic reasoning
- stay laptop-friendly and dependency-light

## Current V2 slice

The first vertical slice intentionally covers a small, controlled subset:

- atomic facts such as `Alice completed amber orientation`
- Horn-style rules such as `If ..., then ...`
- guarded exceptions such as `unless ...`
- universal rules such as `All certified operators may use the milling machine`
- yes/no queries
- explicit residue for uncertainty, attribution, unresolved references, and
  non-formalized fragments

It does not yet try to solve:

- unrestricted negation
- full arithmetic reasoning
- general quantifier scope recovery from free-form prose
- theorem-prover integration

## Hybrid AST

Each statement contains:

- `formal_core`
- `semantic_residue`
- `provenance`
- `exportability`

That means a sentence can be partially formalized without pretending the whole
sentence compiled exactly.

## Export targets

Current exporters:

- `horn`
  Default end-to-end backend. Used for deterministic forward chaining and
  explanation traces.
- `fol`
  Comparison path. Exports the same AST into a FOL/TPTP-style annotated
  encoding.
- `smt`
  Experimental partial path. Present mainly to make exportability explicit for
  future arithmetic and constraint work.

## CLI

Run the experimental path:

```bash
uv run dialectica v2-run "If Alice completed amber orientation, then Alice holds an amber badge. If Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation. May Alice enter the amber workshop?" --pretty
```

You can also pass the query separately:

```bash
uv run dialectica v2-run "All certified operators may use the milling machine. Bruno is a certified operator." --query "May Bruno use the milling machine?" --pretty
```

## Output shape

The command returns:

- the translated hybrid document
- per-target compiled artifacts
- Horn reasoning result
- a natural-language explanation

## Why Horn first

Horn rules are the best first end-to-end backend because they are:

- deterministic
- explainable
- cheap to run locally
- well-matched to the repo's current chain/condition/exception tasks

FOL and SMT are still important, but they are better as comparison or future
paths until the translator is stronger.

