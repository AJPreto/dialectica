# Reasoning Benchmark Suite

Dialectica has two complementary evaluation stories:

- prompt-and-encoding benchmarks
- neuro-symbolic benchmarks centered on the Horn path

This document is about the neuro-symbolic benchmark.

## Philosophy

The reasoning suite is meant to characterize the system, not flatter it.

That means the benchmark includes:

- cases Horn should solve cleanly
- cases Horn should solve but only with multi-step chaining
- cases where Horn should stay partial or conservative
- cases where Horn is expected to lose information

The goal is to answer:

`Is the Horn reasoning pipeline genuinely more accurate and more faithful, or was the early result a small-benchmark artifact?`

## Files

- `benchmarks/reasoning.sample.json`
  A small smoke-test set.
- `benchmarks/reasoning.expanded.json`
  The richer curated suite for serious comparison runs.
- `benchmarks/reasoning.messy.json`
  A Tier 2 suite with longer, noisier, more distractor-heavy prompts.

## Tiers

The benchmark now has two curated tiers:

- `expanded`
  Clean diagnostic logic cases. These are still synthetic, but they isolate
  specific behaviors clearly.
- `messy`
  Longer and noisier reasoning problems. These keep the same controlled
  logic targets while adding distractors, memo-like framing, and more context
  clutter around the critical facts and rules.
  The messy tier now uses a tri-valued answer policy: `yes`, `no`, or `unknown`.
  `unknown` is used when the context leaves the answer unsupported, conflicted,
  ambiguous, or otherwise underdetermined.
  Under the current entailment-based evaluation, `A unless B` does not license `A`
  unless the blocker is ruled out explicitly; absence of evidence for `B` is not
  evidence that `B` is false.

The purpose of the messy tier is to probe the next question:

`Does the reasoning path still hold up when the problem is not a neat textbook snippet?`

## Category taxonomy

The expanded suite includes explicit categories:

- `simple_implication`
- `conjunction_disjunction`
- `negation`
- `contradiction_detection`
- `conditions_exceptions`
- `chained_inference`
- `entity_binding`
- `attribution_speaker_tracking`
- `ambiguity_partial_formalization`
- `arithmetic_equality_inequality`
- `non_exportable_or_partial`
- `messy_long_context`

Each case can belong to more than one category.

## Difficulty levels

Cases are annotated as:

- `easy`
- `medium`
- `adversarial`

The adversarial tier is important. It contains cases where the current Horn
slice is expected to fail, over-derive, or stay partial.

## Per-case expectations

Each benchmark item can specify:

- `expected_answer`
- `expected_horn_answer`
- `expected_inference_success`
- `expected_contradiction_flag`
- `expected_exportability`
- `expected_reasoning_depth`
- `expected_failure_mode`
- `expected_behavior`

This keeps the benchmark inspectable and makes failure analysis easier than a
single raw accuracy number.

## Paraphrase robustness

Some items are grouped under `paraphrase_group`.

Those groups preserve the intended meaning while varying wording or surface
form. The reasoning report measures whether each mode stays stable across the group.

This is deliberately modest. The current translator is still controlled and
domain-limited, so the paraphrases are curated rather than fully open-ended.

## Metrics

The reasoning report includes:

- overall accuracy
- average token cost
- average latency
- category-wise accuracy
- difficulty-wise accuracy
- contradiction sensitivity
- negation handling score
- exception handling score
- paraphrase stability
- export expectation match rate
- explanation faithfulness proxy
- partial-formalization correctness
- average reasoning depth handled
- a per-mode error report

The explanation metric is a proxy, not a semantic judge. It checks whether the
generated explanation matches the actual symbolic trace, blockers, and residue
signals closely enough to be useful.

## Honesty constraints

The suite intentionally includes cases where Horn is expected to struggle:

- explicit negation conflicts
- contradictions without a resolution policy
- attribution that should not be promoted to plain fact
- unresolved references
- disjunction
- arithmetic or comparison queries that point toward SMT rather than Horn

If the Horn reasoner performs poorly there, that is a benchmark success, not a benchmark
failure. The suite is doing its job by showing the boundary of the current
slice.

## Running it

Smoke test:

```bash
uv run dialectica evaluate-reasoning --dataset benchmarks/reasoning.sample.json --provider oracle --pretty
```

Expanded local run:

```bash
uv run dialectica evaluate-reasoning --dataset benchmarks/reasoning.expanded.json --provider ollama --model qwen2.5:3b --output reports/reasoning.expanded.qwen2.5.json --markdown-output reports/reasoning.expanded.qwen2.5.report.md --charts-dir reports/reasoning.expanded.qwen2.5.charts --pretty
```

Messy Tier 2 local run:

```bash
uv run dialectica evaluate-reasoning --dataset benchmarks/reasoning.messy.json --provider ollama --model qwen2.5:3b --output reports/reasoning.messy.qwen2.5.json --markdown-output reports/reasoning.messy.qwen2.5.report.md --charts-dir reports/reasoning.messy.qwen2.5.charts --pretty
```

Render charts from an existing JSON report without recomputing:

```bash
uv run dialectica render-reasoning-report --report reports/reasoning.expanded.qwen2.5.json --markdown-output reports/reasoning.expanded.qwen2.5.report.md --charts-dir reports/reasoning.expanded.qwen2.5.charts --pretty
```

## How to add new cases

Prefer explicit JSON fixtures over generated benchmark inflation.

When adding a case:

1. pick one primary category
2. add any secondary categories that matter
3. annotate the expected Horn behavior honestly
4. mark exportability explicitly
5. add a paraphrase partner only if the wording change is intentional and inspectable

## How to interpret results

Do not overclaim from aggregate accuracy alone.

Look at:

- where the Horn reasoner wins
- where it loses
- whether those wins cluster in the categories it is actually designed for
- whether its failures are because of translation limits, export limits, or reasoning limits

The right conclusion is not “Horn is better” or “Horn is worse.”
The right conclusion is a map of where the current reasoning slice is trustworthy.

On the messy tier, the extra question is whether correctness degrades
gracefully as distractors and context clutter increase, or whether the
translation layer starts dropping or misbinding the crucial pieces.
