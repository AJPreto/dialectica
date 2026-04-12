# Run Walkthrough

This is a plain-English walkthrough of what happens when you trigger a
Dialectica run.

The easiest run to understand is the local complexity sweep:

```bash
uv run dialectica evaluate-complexity-sweep --dataset benchmarks/complexity_sweep.sample.json --provider ollama --model qwen2.5:3b --output reports/ollama_complexity.json --performance-output reports/ollama_complexity.performance.json --summary-output reports/ollama_complexity.sweep.json --markdown-output reports/ollama_complexity.report.md --charts-dir reports/ollama_complexity.charts --pretty
```

## Big picture

Dialectica has two main phases:

1. create or choose a benchmark dataset
2. run several prompt conditions on that dataset and compare the results

If you use the complexity sweep, there is usually a generation step first:

```bash
uv run dialectica generate-complexity-benchmark --levels 6 --scenarios-per-level 2 --followups 2 --output benchmarks/complexity_sweep.sample.json
```

That command only creates the dataset. It does not call a model.

## What happens when you trigger the run

### 1. `uv` starts the project environment

`uv run dialectica ...` means:

- use this repo's Python environment
- use this repo's dependencies
- run the `dialectica` CLI entry point from `pyproject.toml`

`uv` is just the launcher. It is not the benchmark logic itself.

### 2. The CLI reads your subcommand

The CLI lives in `src/dialectica/cli.py`.

If you chose `evaluate-complexity-sweep`, the CLI does two high-level things:

1. run the answer-evaluation pipeline
2. summarize the results by complexity level

### 3. Dialectica loads the dataset

The dataset is the JSON file passed with `--dataset`.

Each case contains:

- a context
- a question
- a gold answer
- difficulty metadata
- optional gold logical forms

At this point Dialectica is not reasoning yet. It is just loading the test
cases it will evaluate.

### 4. Dialectica parses the text into structure

For every case, Dialectica takes:

- the context text
- the question text

and runs them through the local parser.

This produces a logical form with:

- blocks
- relations
- ambiguities

Then it canonicalizes the result so the ordering is stable.

### 5. Dialectica creates the encoded views

Once the logical form exists, Dialectica builds:

- the compact serialization
- the filtered compact serialization
- the structural fingerprint

The important distinction is:

- `compact` keeps the whole parsed graph
- `filtered` keeps only the question-relevant subgraph

### 6. Dialectica builds the prompt conditions

For each case, Dialectica creates:

- `direct`
- `dialectica_compact`
- `dialectica_filtered`
- `dialectica_structural_compact`
- `dialectica_filtered_structural`

If gold logical forms exist and you enable them, it can also run:

- `dialectica_gold_compact`
- `dialectica_gold_filtered`
- `dialectica_gold_structural_compact`
- `dialectica_gold_filtered_structural`

This is the heart of the benchmark.
We are comparing different ways of presenting the same task to the same model.

### 7. The provider is called

Now Dialectica finally sends prompts to the selected provider.

If you run with Ollama:

- the request goes to your local Ollama server
- the model runs on your machine
- the repo content is not sent to a hosted API by default

Each condition becomes one model call.

So one case may produce several model calls.

### 8. Every answer is scored deterministically

After each model response comes back, Dialectica extracts:

- the final answer
- the justification

Then it compares the answer to the gold answer using deterministic scoring.

For boolean tasks, values like `true`, `yes`, and `1` get normalized first so
the benchmark measures correctness rather than wording.

### 9. Metrics are collected during the run

For each condition, Dialectica records:

- correctness
- latency
- token counts
- iterations
- the exact prompt that was used

So the run collects both:

- quality metrics
- cost metrics

### 10. The complexity summary is built

After all cases finish, Dialectica groups the results by complexity level.

That summary asks questions like:

- at what level does the compact encoding become smaller than the raw context?
- how do direct and filtered token curves compare?
- does filtering help accuracy at larger sizes?

### 11. The output files are written

If you pass output paths, Dialectica can write:

- a full JSON report
- a compact performance summary
- a level-by-level sweep summary
- a markdown report
- SVG charts

The chart bundle includes:

- bar charts for accuracy, token cost, latency, and iterations
- a line plot of raw context size versus average total tokens

## What usually confuses people

### "Generate" versus "evaluate"

`generate-complexity-benchmark` only creates the dataset.

`evaluate-complexity-sweep` is the real run.

### "Compact" versus "filtered"

These are different.

`compact` asks:

- what if we send the full encoded graph and no raw text?

`filtered` asks:

- what if we first prune the graph to the relevant logical subgraph?

### "Representation crossover" versus "prompt crossover"

These are also different.

Representation crossover asks:

- is the encoded representation itself smaller than the raw context?

Prompt crossover asks:

- after adding instructions and framing, is the full encoded prompt smaller than
  the direct prompt?

The first crossover usually happens earlier than the second.

## Minimal workflows

### Fast smoke test with no real model call

```bash
uv run dialectica evaluate-complexity-sweep --dataset benchmarks/complexity_sweep.sample.json --provider oracle --pretty
```

### Real local run

```bash
uv run dialectica evaluate-complexity-sweep --dataset benchmarks/complexity_sweep.sample.json --provider ollama --model qwen2.5:3b --output reports/ollama_complexity.json --performance-output reports/ollama_complexity.performance.json --summary-output reports/ollama_complexity.sweep.json --markdown-output reports/ollama_complexity.report.md --charts-dir reports/ollama_complexity.charts --pretty
```

## If you want to inspect the code path

These are the main files involved in a run:

- `src/dialectica/cli.py`: command routing
- `src/dialectica/complexity.py`: dataset generation and level summaries
- `src/dialectica/answer_eval.py`: per-case evaluation loop
- `src/dialectica/prompting.py`: prompt construction
- `src/dialectica/filtering.py`: question-conditioned subgraph pruning
- `src/dialectica/canonical.py`: compact serialization
- `src/dialectica/fingerprint.py`: structural fingerprint generation
- `src/dialectica/providers.py`: local Ollama or other provider calls
- `src/dialectica/scoring.py`: deterministic answer scoring
- `src/dialectica/reporting.py`: markdown and SVG report generation

## Short version

When you trigger a run, Dialectica:

1. loads a dataset
2. parses each case into logical structure
3. builds encoded-only prompt variants
4. sends each variant to the selected model
5. scores the answers against gold truth
6. aggregates the results by condition and complexity level
7. writes reports and charts

That is the full loop.
