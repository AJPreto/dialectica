# Objective Evaluation

The current benchmark in [evaluate.py](/c:/Users/marti/Documents/GitHub/dialectica/src/dialectica/evaluate.py)
tests whether the parser produces plausible block and relation types. That is a
useful diagnostic, but it does not answer the real question:

`Does using Dialectica produce more objectively correct answers than prompting directly?`

This document defines how to test that.

## Success criterion

Dialectica is successful if, on a fixed dataset with objectively scored answers,
the Dialectica pipeline achieves higher answer accuracy than a direct-prompt
baseline using the same underlying model.

Primary metric:

- exact-match or validator-based correctness

Secondary metrics:

- retrieval quality
- parser fidelity
- latency
- token cost

## Important principle

Do not compare only against a weak baseline like "just answer this".

Use at least these three conditions:

1. `Direct`
   The model receives the user prompt and answers directly.
2. `Structured baseline`
   The model is told to extract constraints or reason step by step, but without
   Dialectica's explicit schema.
3. `Dialectica`
   The pipeline parses the input into blocks and optional formal encoding, then
   asks the model to answer using that representation.
4. `Dialectica + structural fingerprint`
   The pipeline uses the logical form plus the Gödel-inspired structural
   fingerprint as auxiliary context.

If Dialectica beats only the weak baseline, that is not strong evidence.
If it beats the structured baseline too, the result is much more meaningful.

## What to measure

### 1. End-to-end answer accuracy

This is the main metric.

Examples:

- boolean answers: exact `true` or `false`
- multiple choice: exact option
- math: exact final number or normalized expression
- plans: pass a rule-based validator
- contradiction detection: exact label

Avoid model-graded scoring whenever possible.

### 2. Retrieval quality

If embeddings are part of the system, evaluate retrieval separately before
generation.

Useful metrics:

- Recall@k
- MRR
- nDCG

Then evaluate downstream answer accuracy with retrieved context included.

### 3. Parser fidelity

Keep the current structural benchmark because it helps diagnose failure modes.
But treat it as a diagnostic metric, not the main outcome metric.

## Best benchmark design

The strongest benchmark for this project is a synthetic or semi-synthetic task
set generated from hidden logical ground truth.

### Why synthetic data is valuable

If the task is generated from a known formal structure, then:

- the correct answer is known exactly
- the logical relations are known exactly
- the dataset can target specific phenomena like negation or exceptions
- the benchmark does not depend on subjective grading

This is especially well aligned with Dialectica because the system is trying to
recover structure from language.

## Recommended task families

Build tasks that stress the kinds of phenomena Dialectica is supposed to help
with:

- negation
- conditionals
- exceptions such as `unless`
- quantified statements
- goal versus constraint separation
- contradiction detection
- multi-step rule application
- retrieval with near-miss distractors

## Dataset format

Create a second benchmark family for objective QA tasks. A good per-example
format is:

```json
{
  "id": "task-001",
  "context": "Employees may access the lab only if they completed safety training. Alice completed safety training.",
  "question": "Can Alice access the lab?",
  "gold_answer": "yes",
  "answer_type": "boolean",
  "phenomena": ["constraint", "condition"],
  "gold_blocks": ["constraint", "condition", "claim"],
  "gold_relations": ["implies"],
  "gold_encoding": {
    "dialect": "tff"
  }
}
```

The important field is `gold_answer`. That is what the main experiment should
optimize for.

Optional fields for deeper analysis:

- `gold_logical_form`
- `gold_question_logical_form`
- `gold_encoding`

Those let the harness compare:

- `dialectica_parsed`: use the current parser output
- `dialectica_structural`: use parser output plus the structural fingerprint
- `dialectica_gold`: use gold intermediate structure when available
- `dialectica_gold_structural`: use gold intermediate structure plus the
  structural fingerprint

That separation is valuable because it tells you whether failures come from the
representation idea itself or from the parser recovering it imperfectly.

## Experimental protocol

For each task:

1. Run the `Direct` prompt.
2. Run the `Structured baseline`.
3. Run the `Dialectica` pipeline.
4. Score all outputs with the same deterministic checker.
5. Save the prompt, parsed representation, final answer, score, latency, and tokens.

Keep these fixed:

- model version
- temperature
- max tokens
- system prompt style
- answer format

If one condition gets more context or more compute, record that explicitly.

## Current CLI support

The repo now includes a runner for this workflow:

```bash
uv run dialectica evaluate-answers --dataset benchmarks/objective_qa.sample.json --provider oracle --pretty
```

For a real model-backed run:

```bash
$env:OPENAI_API_KEY="your_key_here"
uv run dialectica evaluate-answers --dataset benchmarks/objective_qa.sample.json --provider openai --model gpt-5.4-mini --pretty
```

The `oracle` provider is just a smoke test for the harness. It is not a valid
benchmark condition.

## Retrieval experiment design

If the end goal includes embeddings, use a separate corpus-query benchmark.

For each query:

1. Retrieve with text-only embeddings.
2. Retrieve with canonical Dialectica serialization.
3. Retrieve with a hybrid score.
4. Measure recall of the gold-supporting item.
5. Measure answer accuracy after retrieval.

The best retrieval benchmark includes distractors that differ only by:

- negation
- exception
- quantifier scope
- similar wording with different logical meaning

## Statistical testing

Use paired comparisons, because each method answers the same tasks.

Recommended:

- exact-match accuracy
- bootstrap confidence interval for accuracy difference
- McNemar's test for paired wins and losses

## Failure analysis

Separate failures into buckets:

- parser error
- retrieval error
- solver reasoning error
- answer formatting error
- benchmark ambiguity

Without this, it will be hard to tell whether Dialectica itself is helping.

## Practical milestone order

1. Keep the current parser-structure benchmark
2. Add objective QA benchmark files
3. Add direct and structured baselines
4. Add deterministic scoring
5. Add retrieval benchmark
6. Compare accuracy, not just elegance of representation

## Strongest possible version

Because the project now has a TPTP-inspired encoding layer, the long-term best
benchmark is:

1. generate hidden formal theories and queries
2. verbalize them into natural language
3. solve them symbolically to get the gold answer
4. compare direct prompting against Dialectica-assisted prompting

That would let us test whether the intermediate representation actually recovers
enough structure to improve objective correctness.
