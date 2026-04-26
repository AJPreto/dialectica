# Reasoning Benchmark Suite

Dialectica uses a single canonical reasoning benchmark:

- `benchmarks/reasoning.messy.json`

The file contains 30 longer, noisier reasoning problems with distractors,
memo-like framing, and a tri-valued answer policy: `yes`, `no`, or `unknown`.
`unknown` is used when the context leaves the answer unsupported, conflicted,
ambiguous, or otherwise underdetermined.

## Philosophy

The reasoning suite is meant to characterize the system, not flatter it.

The benchmark includes:

- cases the Horn path should solve cleanly
- cases that require multi-step chaining
- cases where the reasoner should stay partial or conservative
- cases where translation or export limits should be visible

The goal is to answer:

`Does the reasoning path still hold up when the problem is not a neat textbook snippet?`

## Category Taxonomy

Cases are annotated with one or more categories:

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

## Per-Case Expectations

Each benchmark item can specify:

- `expected_answer`
- `expected_horn_answer`
- `expected_inference_success`
- `expected_contradiction_flag`
- `expected_exportability`
- `expected_reasoning_depth`
- `expected_failure_mode`
- `expected_behavior`

These fields make the benchmark inspectable and make failure analysis clearer
than a single raw accuracy number.

## Manual Checking

For a human-readable answer key with full context, use:

- `docs/gold-answer-keys.md`

For a one-case-at-a-time ChatGPT prompt pack, use:

- `prompts/external-chat-benchmark.messy.md`

For recording manual ChatGPT answers, use:

- `examples/reasoning/external-chat-messy-response.template.json`

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

## Running It

```bash
uv run dialectica evaluate-reasoning --dataset benchmarks/reasoning.messy.json --provider ollama --model qwen2.5:3b --output reports/reasoning.messy.qwen2.5.json --markdown-output reports/reasoning.messy.qwen2.5.report.md --charts-dir reports/reasoning.messy.qwen2.5.charts --pretty
```

Render charts from an existing JSON report without recomputing:

```bash
uv run dialectica render-reasoning-report --report reports/reasoning.messy.qwen2.5.json --markdown-output reports/reasoning.messy.qwen2.5.report.md --charts-dir reports/reasoning.messy.qwen2.5.charts --pretty
```

## Interpreting Results

Do not overclaim from aggregate accuracy alone.

Look at:

- where the Horn reasoner wins
- where it loses
- whether those wins cluster in the categories it is designed for
- whether its failures are due to translation limits, export limits, or reasoning limits

The right conclusion is not "Horn is better" or "Horn is worse". The right
conclusion is a map of where the current reasoning slice is trustworthy.
