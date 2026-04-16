# V2 Neuro-Symbolic Path

Dialectica V1 is a typed logical-block and retrieval-oriented system.
Dialectica V2 is an experimental parallel path that adds a stronger
neuro-symbolic stack:

```text
natural language
  -> redundancy check and removal
  -> conservative decomposition into smaller articulated units
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
- deduplicate only when the source content is truly redundant
- decompose only when clause boundaries are high-confidence
- prefer deterministic reasoning
- stay laptop-friendly and dependency-light

## Current V2 slice

The first vertical slice intentionally covers a small, controlled subset:

- conservative pre-translation cleanup
- atomic facts such as `Alice completed amber orientation`
- Horn-style rules such as `If ..., then ...`
- guarded exceptions such as `unless ...`
- universal rules such as `All certified operators may use the milling machine`
- yes/no queries
- explicit residue for uncertainty, attribution, unresolved references, and
  non-formalized fragments

It does not yet try to solve:

- semantic deduplication of merely similar statements
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
  Broader comparison and proof path. Exports the same AST into a FOL/TPTP-style
  annotated encoding and a safe machine-readable fragment for deterministic
  skeptical proof.
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
- the selected reasoning result
- a natural-language explanation

You can choose the reasoning backend explicitly:

```bash
uv run dialectica v2-run "If Alice completed amber orientation or Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation. May Alice enter the amber workshop?" --reasoner fol --pretty
```

## Benchmarking V2

The repo now includes a richer dedicated V2 benchmark suite:

- `benchmarks/v2_reasoning.sample.json`
- `benchmarks/v2_reasoning.expanded.json`

Use the expanded suite when you want a more credible comparison across:

- `Direct`
- `dialectica_compact`
- `dialectica_filtered`
- `dialectica_filtered_structural`
- `v2_horn`
- `v2_fol`

Example:

```bash
uv run dialectica evaluate-v2 --dataset benchmarks/v2_reasoning.expanded.json --provider ollama --model qwen2.5:3b --output reports/v2_comparison.expanded.qwen2.5.json --markdown-output reports/v2_comparison.expanded.qwen2.5.report.md --charts-dir reports/v2_comparison.expanded.qwen2.5.charts --pretty
```

For the benchmark philosophy, category taxonomy, and interpretation guidance,
see [v2-benchmark-suite.md](./v2-benchmark-suite.md).

## Why Horn first

Horn rules are the best first end-to-end backend because they are:

- deterministic
- explainable
- cheap to run locally
- well-matched to the repo's current chain/condition/exception tasks

FOL and SMT are still important, but they are better as comparison or future
paths until the translator is stronger.
