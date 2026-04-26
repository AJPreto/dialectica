# Dialectica

Dialectica is a design for an agent that transforms natural language into
structured logical blocks before downstream prompting, retrieval, and
embedding.

The goal is not to force language into brittle formal logic. The goal is to
produce a stable intermediate representation that is:

- expressive enough to capture reasoning structure
- soft enough to preserve ambiguity and uncertainty
- machine-friendly enough for retrieval, planning, and synthesis

By doing so, we are leveraging a priori knowledge that can be token-independent and 
achieve the same accuracy. This has limited scope, but aims to showcase how we can 
intertwine preexisting corpus of knowledge with powerful LLMs. 

## Current status

The repo includes a runnable local toolchain with:

- a local parser CLI
- a small HTTP API
- a benchmark and evaluation harness
- an end-to-end answer evaluation harness
- a synthetic complexity-sweep benchmark generator
- schema, prompt, and sample output files

The parser is heuristic so the project can run locally
with no external model dependency. That makes it useful for fast iteration on
the intermediate representation before swapping in an LLM-backed parser later.

## Quick start

From the repo root, use `uv` as the default workflow:

```bash
uv sync
```

Then run commands with `uv run`:

```bash
uv run dialectica parse "If the battery is dead, the car will not start unless we jump it." --pretty
```

### Parse text from the CLI

```bash
uv run dialectica parse "If the battery is dead, the car will not start unless we jump it." --pretty
```

### Print the canonical serialization

```bash
uv run dialectica parse "The experiment failed because the reagent was contaminated." --canonical
```

### Build a structural fingerprint

```bash
uv run dialectica fingerprint "If the battery is dead, the car will not start unless we jump it." --summary --pretty
```

### Compare two structural fingerprints

```bash
uv run dialectica compare-fingerprints "The policy requires encryption at rest." "The policy does not require encryption at rest." --pretty
```

### Parse a multi-sentence document

```bash
uv run dialectica parse --document "Employees may access the lab only if they completed safety training. Alice completed safety training." --pretty
```

### Run the local API

```bash
uv run dialectica serve --host 127.0.0.1 --port 8000
```

Then send a request:

```bash
curl -X POST http://127.0.0.1:8000/parse ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"We should allow remote work if it improves productivity.\"}"
```

### Run the benchmark harness

```bash
uv run dialectica evaluate --dataset benchmarks/core.json --pretty
```

### Run the answer evaluation harness

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

### Generate a complexity-sweep benchmark

```bash
uv run dialectica generate-complexity-benchmark --levels 6 --scenarios-per-level 2 --followups 2 --output benchmarks/complexity_sweep.sample.json
```

### Evaluate a complexity sweep

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

### Run the neuro-symbolic reasoning pipeline

```bash
uv run dialectica reason "If Alice completed amber orientation, then Alice holds an amber badge. If Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation. May Alice enter the amber workshop?" --pretty
```

If you want a step-by-step explanation of what happens during a run, see
[run walkthrough](./docs/run-walkthrough.md).

## Repo layout

- `src/dialectica/ir.py`: hybrid reasoning AST
- `src/dialectica/translator.py`: controlled natural-language translator
- `src/dialectica/compiler.py`: export dispatcher
- `src/dialectica/engine.py`: deterministic Horn and broader FOL-style reasoning engines
- `src/dialectica/explainer.py`: natural-language explanation layer
- `src/dialectica/parser.py`: heuristic parser
- `src/dialectica/canonical.py`: canonicalization and serialization
- `src/dialectica/complexity.py`: synthetic complexity benchmark generation and summaries
- `src/dialectica/filtering.py`: question-conditioned logical-form pruning
- `src/dialectica/fingerprint.py`: Gödel-inspired structural fingerprint backend
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
- `docs/tptp-inspired-encoding.md`: notes on the richer formal encoding
- `docs/structural-fingerprint.md`: notes on the Gödel-inspired auxiliary backend
- `docs/objective-evaluation.md`: how to test whether Dialectica improves correctness
- `docs/run-walkthrough.md`: step-by-step explanation of what happens during a run
- `docs/reasoning-pipeline.md`: reasoning pipeline design and CLI usage
- `docs/encoding-backends.md`: practical comparison of export targets
- `docs/reasoning-benchmark-suite.md`: benchmark philosophy, categories, metrics, and usage

## Core idea

Instead of embedding only raw user text, Dialectica creates a two-layer
representation:

1. Natural language input
2. Logical block graph

The logical block graph is then used in two ways:

- as a prompt intermediate layer for downstream agents
- as a canonical representation to embed and index

## Why this helps

Raw text embeddings often blur distinctions that matter for reasoning:

- goals vs constraints
- claims vs evidence
- conditions vs outcomes
- negation
- exceptions
- uncertainty

Dialectica makes those distinctions explicit.

## Design principles

### 1. Typed semantics over rigid formalism

Dialectica should start as a typed semantic graph, not pure symbolic logic.
Natural language is too ambiguous for a strict first-order pipeline to work
reliably in most real settings.

### 2. Faithfulness over precision

If the source text is vague, the representation should stay vague. The parser
must be able to emit uncertainty and ambiguity instead of inventing a clean but
incorrect structure.

### 3. Hybrid retrieval

Store and compare:

- the original text
- the canonicalized logical representation
- optional block-level embeddings

This lets the system benefit from both semantic similarity and explicit
reasoning structure.

### 4. Decomposability

The smallest useful unit is a block. A single utterance may yield many blocks
and many relations.

## System components

### Parser

Transforms natural language into structured blocks and relations.

Input:

- raw utterance or document span

Output:

- `LogicalForm` JSON object

### Canonicalizer

Normalizes parser output into a stable ordering and serialization so semantically
equivalent outputs are more likely to compare well.

Examples:

- normalize block ordering
- deduplicate repeated entities
- standardize relation direction
- preserve unresolved ambiguity explicitly

### Embedder

Creates embeddings from one or more of:

- source text
- canonical logical serialization
- per-block text

### Retriever

Supports queries over:

- text similarity
- logic similarity
- relation-aware subgraph matches

### Downstream agent

Consumes both the original user text and the parsed logical structure for:

- planning
- constrained answering
- contradiction checking
- memory retrieval
- prompt construction

## Minimal schema

The first version of Dialectica should support:

- `claim`
- `goal`
- `constraint`
- `condition`
- `outcome`
- `evidence`
- `definition`
- `question`
- `exception`
- `unknown`
- `ambiguity`

And relations such as:

- `supports`
- `contradicts`
- `implies`
- `depends_on`
- `defines`
- `qualifies`
- `unless`
- `answers`

See [logical-blocks.schema.json](./schema/logical-blocks.schema.json).

## Rich encoding layer

Dialectica now also has an optional TPTP-inspired encoding layer that adds:

- annotated formulae
- formula roles
- typed signatures
- quantifiers and connectives
- provenance and useful metadata

Start here:

- [encoding schema](./schema/logical-encoding.schema.json)
- [encoding notes](./docs/tptp-inspired-encoding.md)
- [sample encoding](./examples/sample-encoding.json)

## Testing whether Dialectica helps

The parser benchmark is not the main proof of value. The main test is whether
the same model answers objective tasks more accurately when using Dialectica.

The new answer evaluation harness compares:

- `direct`
- `dialectica_compact`
- `dialectica_filtered`
- `dialectica_structural_compact`
- `dialectica_filtered_structural`
- optionally `dialectica_gold_compact` when gold logical forms are present
- optionally `dialectica_gold_filtered` when gold logical forms are present
- optionally `dialectica_gold_structural_compact` when gold logical forms are present
- optionally `dialectica_gold_filtered_structural` when gold logical forms are present

See:

- [objective evaluation guide](./docs/objective-evaluation.md)
- [sample objective QA dataset](./benchmarks/objective_qa.sample.json)
- [sample complexity sweep](./benchmarks/complexity_sweep.sample.json)
- [reasoning benchmark suite](./docs/reasoning-benchmark-suite.md)

## Structural fingerprint backend

Dialectica now includes a Gödel-inspired structural fingerprint route that
works alongside the logical route rather than replacing it.

It is intended for:

- structural retrieval experiments
- exact-shape fingerprints
- auxiliary prompt context
- future hybrid embedding strategies

Start here:

- [structural fingerprint notes](./docs/structural-fingerprint.md)

## Example

Input:

`If the battery is dead, the car will not start unless we jump it.`

Output:

```json
{
  "source_text": "If the battery is dead, the car will not start unless we jump it.",
  "blocks": [
    {
      "id": "b1",
      "type": "condition",
      "text": "the battery is dead"
    },
    {
      "id": "b2",
      "type": "outcome",
      "text": "the car will not start",
      "polarity": "negative"
    },
    {
      "id": "b3",
      "type": "exception",
      "text": "we jump it"
    }
  ],
  "relations": [
    {
      "type": "implies",
      "source": "b1",
      "target": "b2"
    },
    {
      "type": "unless",
      "source": "b3",
      "target": "b2"
    }
  ]
}
```

## Suggested first build

The fastest path to a working system is:

1. Define the schema
2. Create a parser prompt that emits strict JSON
3. Canonicalize the JSON
4. Serialize the canonical form into text
5. Embed both raw text and canonical serialization
6. Compare hybrid retrieval quality on a small benchmark set

The local toolchain covers steps 1 through 4 directly, and lays the groundwork
for steps 5 and 6.

## Retrieval Architecture

```text
User text
  -> Parser LLM
  -> LogicalForm JSON
  -> Canonicalizer
  -> Canonical serialization
  -> Embeddings
  -> Vector store

Query
  -> Parser LLM
  -> LogicalForm JSON
  -> Canonical serialization
  -> Hybrid retrieval
  -> Downstream agent
```

## Practical Constraints

The retrieval-oriented path should not try to solve full formal reasoning.
Instead, it should be useful for:

- decomposing prompts
- retrieving relevant prior reasoning
- surfacing contradictions
- carrying forward explicit constraints

## Neuro-Symbolic Reasoning

Dialectica also includes a neuro-symbolic reasoning path that works alongside
the retrieval-oriented logical-form pipeline:

- conservative redundancy removal before translation
- high-confidence decomposition into smaller articulated units
- a hybrid AST with formal core, residue, provenance, and exportability
- a pluggable encoding layer
- a deterministic Horn-style reasoning backend
- a broader skeptical FOL-style reasoning backend over the exact exported core
- a natural-language explanation layer

The default end-to-end reasoning backend is Horn-style because it is deterministic,
explainable, and cheap to run locally. The same AST also exports to a FOL-style
artifact that now has a matching proof path for the safe compiled fragment, and
to a partial SMT-oriented path for future
arithmetic work.

Start here:

- [reasoning pipeline overview](./docs/reasoning-pipeline.md)
- [encoding backend comparison](./docs/encoding-backends.md)
- [reasoning benchmark suite](./docs/reasoning-benchmark-suite.md)

Run the reasoning benchmark locally:

```bash
uv run dialectica evaluate-reasoning --dataset benchmarks/reasoning.messy.json --provider ollama --model qwen2.5:3b --output reports/reasoning.messy.qwen2.5.json --markdown-output reports/reasoning.messy.qwen2.5.report.md --charts-dir reports/reasoning.messy.qwen2.5.charts --pretty
```

## Next implementation steps

- Replace or augment the heuristic parser with an LLM-backed parser
- Broaden contradiction, negation, and arithmetic coverage in the translator
- Add embedding generation for raw text and canonical graph serializations
- Add hybrid retrieval experiments and scoring
- Measure whether logical retrieval beats text-only retrieval for selected tasks
