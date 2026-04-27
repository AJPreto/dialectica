# Dialectica

Dialectica is a design for an agent that transforms natural language into
structured logical blocks before downstream prompting, retrieval, and
embedding.

The goal is not to force language into brittle formal logic. The goal is to
produce a stable intermediate representation that is:

- expressive enough to capture reasoning structure
- soft enough to preserve ambiguity and uncertainty
- machine-friendly enough for retrieval, planning, and synthesis

By doing so, the project explores how token-independent structure can work
alongside strong language models without pretending that every task should be
reduced to strict symbolic logic.

## Current Status

The repo includes a runnable local toolchain with:

- a local parser CLI
- a small HTTP API
- a benchmark and evaluation harness
- an end-to-end answer evaluation harness
- a synthetic complexity-sweep benchmark generator
- schema, prompt, and sample output files

The parser is heuristic so the project can run locally with no external model
dependency. That makes it useful for fast iteration on the intermediate
representation before swapping in an LLM-backed parser later.

## Quick Start

From the repo root, use `uv` as the default workflow:

```bash
uv sync
```

Then run commands with `uv run`:

```bash
uv run dialectica parse "If the battery is dead, the car will not start unless we jump it." --pretty
```

### Parse Text From The CLI

```bash
uv run dialectica parse "If the battery is dead, the car will not start unless we jump it." --pretty
```

### Print The Canonical Serialization

```bash
uv run dialectica parse "The experiment failed because the reagent was contaminated." --canonical
```

### Build A Structural Fingerprint

```bash
uv run dialectica fingerprint "If the battery is dead, the car will not start unless we jump it." --summary --pretty
```

### Compare Two Structural Fingerprints

```bash
uv run dialectica compare-fingerprints "The policy requires encryption at rest." "The policy does not require encryption at rest." --pretty
```

### Parse A Multi-Sentence Document

```bash
uv run dialectica parse --document "Employees may access the lab only if they completed safety training. Alice completed safety training." --pretty
```

### Run The Local API

```bash
uv run dialectica serve --host 127.0.0.1 --port 8000
```

Then send a request:

```bash
curl -X POST http://127.0.0.1:8000/parse ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"We should allow remote work if it improves productivity.\"}"
```

### Run The Benchmark Harness

```bash
uv run dialectica evaluate --dataset benchmarks/core.json --pretty
```

### Run The Answer Evaluation Harness

For a smoke test that exercises the full pipeline without an API call:

```bash
uv run dialectica evaluate-answers --dataset benchmarks/objective_qa.sample.json --provider oracle --pretty
```

For a real model comparison using the OpenAI Responses API:

```bash
$env:OPENAI_API_KEY="your_key_here"
uv run dialectica evaluate-answers --dataset benchmarks/objective_qa.sample.json --provider openai --model gpt-5-mini --output reports/openai_metrics.json --performance-output reports/openai_metrics.performance.json --pretty
```

For a no-cost local run with Ollama:

```bash
ollama pull qwen2.5:3b
uv run dialectica evaluate-answers --dataset benchmarks/objective_qa.sample.json --provider ollama --model qwen2.5:3b --output reports/ollama_metrics.json --performance-output reports/ollama_metrics.performance.json --pretty
```

The Ollama provider is localhost-only by default. It refuses non-local Ollama
endpoints unless you explicitly set `DIALECTICA_ALLOW_REMOTE_OLLAMA=1`.

### Generate A Complexity-Sweep Benchmark

```bash
uv run dialectica generate-complexity-benchmark --levels 6 --scenarios-per-level 2 --followups 2 --output benchmarks/complexity_sweep.sample.json
```

### Evaluate A Complexity Sweep

```bash
uv run dialectica evaluate-complexity-sweep --dataset benchmarks/complexity_sweep.sample.json --provider ollama --model qwen2.5:3b --output reports/ollama_complexity.json --performance-output reports/ollama_complexity.performance.json --summary-output reports/ollama_complexity.sweep.json --markdown-output reports/ollama_complexity.report.md --charts-dir reports/ollama_complexity.charts --pretty
```

The complexity summary separates two crossover questions:

- when the compact Dialectica encoding becomes smaller than the raw context
- when the full compact prompt becomes smaller than the direct prompt

The report bundle can also emit:

- a markdown summary report
- SVG bar charts for accuracy, tokens, latency, and iterations
- an SVG line plot of raw context size versus average total tokens

### Run The Reasoning Pipeline

```bash
uv run dialectica reason "If Alice completed amber orientation, then Alice holds an amber badge. If Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation. May Alice enter the amber workshop?" --pretty
```

If you want a step-by-step explanation of what happens during a run, see
[run walkthrough](./docs/run-walkthrough.md).

## Repo Layout

- `src/dialectica/ir.py`: hybrid reasoning AST
- `src/dialectica/translator.py`: controlled natural-language translator
- `src/dialectica/compiler.py`: export dispatcher
- `src/dialectica/engine.py`: deterministic Horn and broader FOL-style reasoning engines
- `src/dialectica/explainer.py`: natural-language explanation layer
- `src/dialectica/parser.py`: heuristic parser
- `src/dialectica/canonical.py`: canonicalization and serialization
- `src/dialectica/complexity.py`: synthetic complexity benchmark generation and summaries
- `src/dialectica/filtering.py`: question-conditioned logical-form pruning
- `src/dialectica/fingerprint.py`: Goedel-inspired structural fingerprint backend
- `src/dialectica/validation.py`: lightweight validation
- `src/dialectica/api.py`: stdlib HTTP API
- `src/dialectica/cli.py`: command-line entry points
- `src/dialectica/reporting.py`: markdown and SVG report generation
- `benchmarks/core.json`: initial benchmark set
- `benchmarks/objective_qa.sample.json`: sample objective answer benchmark format
- `benchmarks/complexity_sweep.sample.json`: generated scaling benchmark sample
- `benchmarks/reasoning.messy.json`: canonical noisy reasoning benchmark with `yes / no / unknown` answers
- `schema/logical-blocks.schema.json`: JSON schema for the target structure
- `schema/logical-encoding.schema.json`: TPTP-inspired encoding layer
- `prompts/parser.md`: parser prompt for an eventual LLM-backed version
- `docs/concepts/README.md`: concept-level architecture and method guides
- `docs/tptp-inspired-encoding.md`: notes on the richer formal encoding
- `docs/structural-fingerprint.md`: notes on the Goedel-inspired auxiliary backend
- `docs/objective-evaluation.md`: how to test whether Dialectica improves correctness
- `docs/run-walkthrough.md`: step-by-step explanation of what happens during a run
- `docs/reasoning-pipeline.md`: reasoning pipeline design and CLI usage
- `docs/encoding-backends.md`: practical comparison of export targets
- `docs/reasoning-benchmark-suite.md`: benchmark philosophy, categories, metrics, and usage

## Concept Guides

Dialectica has two main tracks:

- a retrieval-oriented logical-form lane for prompting, indexing, and hybrid retrieval
- a deterministic reasoning lane for the safe symbolic fragment

The longer architectural notes live in `docs/` so this README can stay focused
on setup and navigation.

Start here:

- [Concept Guide Index](./docs/concepts/README.md)
- [Foundations](./docs/concepts/foundations.md)
- [Retrieval Architecture](./docs/concepts/retrieval-architecture.md)
- [Reasoning Methods](./docs/concepts/reasoning-methods.md)
- [Run Walkthrough](./docs/run-walkthrough.md)
- [Objective Evaluation](./docs/objective-evaluation.md)
- [Reasoning Benchmark Suite](./docs/reasoning-benchmark-suite.md)
- [Encoding Backends](./docs/encoding-backends.md)
- [TPTP-Inspired Encoding](./docs/tptp-inspired-encoding.md)
- [Structural Fingerprint](./docs/structural-fingerprint.md)

Shortest mental model:

1. parse prose into blocks and relations
2. canonicalize that structure into a stable form
3. use the structure either as better prompt material or compile it into a local reasoning program

## Next Implementation Steps

- Replace or augment the heuristic parser with an LLM-backed parser
- Broaden contradiction, negation, and arithmetic coverage in the translator
- Add embedding generation for raw text and canonical graph serializations
- Add hybrid retrieval experiments and scoring
- Measure whether logical retrieval beats text-only retrieval for selected tasks
