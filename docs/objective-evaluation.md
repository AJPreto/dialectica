# Objective Evaluation

The parser benchmark in [evaluate.py](/c:/Users/marti/Documents/GitHub/dialectica/src/dialectica/evaluate.py)
is useful, but it is not the main proof of value.

The real question is:

`Does Dialectica improve objective correctness compared with answering the raw task directly?`

This document defines the leaner benchmark setup now used in the repo.

For the dedicated neuro-symbolic benchmark centered on the experimental Horn
path, see [v2-benchmark-suite.md](./v2-benchmark-suite.md).

## Success criterion

Dialectica is successful if, on a fixed dataset with deterministic scoring, an
encoded-only condition beats or matches the direct baseline while improving at
least one of these:

- accuracy
- token efficiency
- scaling behavior as context size grows

Primary metric:

- exact-match or validator-based correctness

Secondary metrics:

- token cost
- latency
- iterations
- parser fidelity
- retrieval quality

## Current condition set

The repo now keeps only:

1. `Direct`
   The model receives the raw context and raw question.
2. `dialectica_compact`
   The model receives only the compact encoded logical representation.
3. `dialectica_filtered`
   The model receives only the filtered compact representation.
4. `dialectica_structural_compact`
   The model receives the compact representation plus the structural
   fingerprint.
5. `dialectica_filtered_structural`
   The model receives the filtered compact representation plus the structural
   fingerprint.

Optional gold variants:

- `dialectica_gold_compact`
- `dialectica_gold_filtered`
- `dialectica_gold_structural_compact`
- `dialectica_gold_filtered_structural`

Mixed raw-plus-augmented prompt paths were removed so the benchmark focuses on
the comparison we actually care about: raw task versus encoded-only task.

## Why this matters

If a Dialectica condition still includes the raw task plus extra structure, it
cannot really test the compression or filtering hypothesis fairly.

The current setup makes the distinction explicit:

- `direct` is the raw task
- every Dialectica condition is encoded-only
- `filtered` conditions also prune away irrelevant logical material

## What to measure

### 1. End-to-end answer accuracy

This is the main metric.

Examples:

- boolean answers: exact `yes` or `no`
- multiple choice: exact option
- math: exact normalized value
- contradiction detection: exact label

Avoid model-graded scoring whenever possible.

### 2. Token cost

Track:

- input tokens
- output tokens
- total tokens

This matters because one of the main hypotheses is that encoded-only prompting
may scale better than raw prompting as contexts get larger.

### 3. Latency and iterations

Track:

- latency per condition
- iterations per answer path

Right now most conditions are single-call, but the metric is still useful when
the pipeline gets more agentic later.

### 4. Representation crossover

Separate these two questions:

1. When does the encoded representation become smaller than the raw context?
2. When does the full encoded prompt become smaller than the direct prompt?

The first crossover usually happens earlier than the second.

## Dataset format

A good objective QA case looks like this:

```json
{
  "id": "task-001",
  "context": "Employees may access the lab only if they completed safety training. Alice completed safety training.",
  "question": "Can Alice access the lab?",
  "gold_answer": "yes",
  "answer_type": "boolean",
  "phenomena": ["constraint", "condition"],
  "gold_logical_form": {},
  "gold_question_logical_form": {},
  "gold_encoding": {
    "dialect": "tff"
  }
}
```

The most important field is `gold_answer`.

Optional gold structure lets the harness separate:

- representation quality
- parser quality

## Experimental protocol

For each case:

1. Run `direct`.
2. Run the encoded-only Dialectica variants.
3. Score every answer with the same deterministic checker.
4. Save prompts, answers, scores, token counts, and latency.

Keep these fixed:

- model version
- provider
- answer format
- scoring logic

## Current CLI support

Smoke test:

```bash
uv run dialectica evaluate-answers --dataset benchmarks/objective_qa.sample.json --provider oracle --pretty
```

Local Ollama run:

```bash
ollama pull qwen2.5:3b
uv run dialectica evaluate-answers --dataset benchmarks/objective_qa.sample.json --provider ollama --model qwen2.5:3b --pretty
```

Dialectica blocks remote Ollama endpoints by default. To preserve privacy, keep
`OLLAMA_BASE_URL` pointed at `localhost`. Only set
`DIALECTICA_ALLOW_REMOTE_OLLAMA=1` if you intentionally want to override that
safety check.

## V2-specific comparison

The repo also has a dedicated V2 comparison runner:

```bash
uv run dialectica evaluate-v2 --dataset benchmarks/v2_reasoning.expanded.json --provider ollama --model qwen2.5:3b --output reports/v2_comparison.expanded.qwen2.5.json --markdown-output reports/v2_comparison.expanded.qwen2.5.report.md --charts-dir reports/v2_comparison.expanded.qwen2.5.charts --pretty
```

That benchmark adds:

- category-wise accuracy
- difficulty-wise accuracy
- paraphrase stability
- contradiction and negation diagnostics
- exportability diagnostics for the V2 path
- explanation-faithfulness proxies

## Complexity sweep

The repo also includes a synthetic scaling benchmark:

```bash
uv run dialectica generate-complexity-benchmark --levels 6 --scenarios-per-level 2 --followups 2 --output benchmarks/complexity_sweep.sample.json
uv run dialectica evaluate-complexity-sweep --dataset benchmarks/complexity_sweep.sample.json --provider ollama --model qwen2.5:3b --output reports/ollama_complexity.json --performance-output reports/ollama_complexity.performance.json --summary-output reports/ollama_complexity.sweep.json --markdown-output reports/ollama_complexity.report.md --charts-dir reports/ollama_complexity.charts --pretty
```

That sweep reports:

- accuracy by complexity level
- token cost by complexity level
- latency and iterations by complexity level
- representation crossover levels
- prompt crossover levels
- bar charts for the main metrics
- a line plot of raw context size versus average total tokens

## Recommended task families

Build tasks that stress what Dialectica is supposed to help with:

- negation
- exceptions such as `unless`
- multi-step rule application
- distractor-heavy contexts
- repeated follow-up questions over the same scenario
- scaling context length

The most important scaling question is not just whether Dialectica is better on
average. It is whether filtered or encoded-only routes degrade more gracefully
than raw prompting as task size increases.

## Retrieval experiment design

If the end goal includes embeddings, evaluate retrieval separately.

For each query:

1. Retrieve with text-only embeddings.
2. Retrieve with Dialectica encodings.
3. Retrieve with hybrid scores.
4. Measure recall of the gold-supporting item.
5. Measure downstream answer accuracy after retrieval.

The best retrieval benchmark includes distractors that differ only by:

- negation
- exceptions
- quantifier scope
- structurally similar but logically different rules

## Failure analysis

Separate failures into buckets:

- parser error
- filtering error
- retrieval error
- solver reasoning error
- formatting error
- benchmark ambiguity

Without this, it is hard to tell whether the representation itself helped.

## Practical milestone order

1. Keep the parser-structure benchmark
2. Keep the direct baseline
3. Compare against encoded-only Dialectica variants
4. Add deterministic scoring
5. Add complexity sweeps
6. Add retrieval benchmarks
7. Compare accuracy, cost, and scaling behavior together

## Strongest possible version

Because the project now has a TPTP-inspired encoding layer, the long-term best
benchmark is:

1. generate hidden formal theories and queries
2. verbalize them into natural language
3. solve them symbolically to get the gold answer
4. compare direct prompting against encoded-only Dialectica prompting

That tests whether the intermediate representation recovers enough structure to
improve objective correctness.
