# Dialectica

Dialectica is a design for an agent that transforms natural language into
structured logical blocks before downstream prompting, retrieval, and
embedding.

The goal is not to force language into brittle formal logic. The goal is to
produce a stable intermediate representation that is:

- expressive enough to capture reasoning structure
- soft enough to preserve ambiguity and uncertainty
- machine-friendly enough for retrieval, planning, and synthesis

## Prototype status

The repo now includes a runnable V1 prototype with:

- a local parser CLI
- a small HTTP API
- a benchmark and evaluation harness
- schema, prompt, and sample output files

The parser is heuristic in this first version so the project can run locally
with no external model dependency. That makes it useful for fast iteration on
the intermediate representation before swapping in an LLM-backed parser later.

## Quick start

From the repo root, use one of these setup paths:

```bash
$env:PYTHONPATH="src"
```

Or install the package in editable mode:

```bash
python -m pip install -e .
```

### Parse text from the CLI

```bash
python -m dialectica parse "If the battery is dead, the car will not start unless we jump it." --pretty
```

### Print the canonical serialization

```bash
python -m dialectica parse "The experiment failed because the reagent was contaminated." --canonical
```

### Run the local API

```bash
python -m dialectica serve --host 127.0.0.1 --port 8000
```

Then send a request:

```bash
curl -X POST http://127.0.0.1:8000/parse ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"We should allow remote work if it improves productivity.\"}"
```

### Run the benchmark harness

```bash
python -m dialectica evaluate --dataset benchmarks/core.json --pretty
```

## Repo layout

- `src/dialectica/parser.py`: heuristic parser
- `src/dialectica/canonical.py`: canonicalization and serialization
- `src/dialectica/validation.py`: lightweight validation
- `src/dialectica/api.py`: stdlib HTTP API
- `src/dialectica/cli.py`: command-line entry points
- `benchmarks/core.json`: initial benchmark set
- `schema/logical-blocks.schema.json`: JSON schema for the target structure
- `schema/logical-encoding.schema.json`: TPTP-inspired encoding layer
- `prompts/parser.md`: parser prompt for an eventual LLM-backed version
- `docs/tptp-inspired-encoding.md`: notes on the richer formal encoding

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

The fastest path to a working prototype is:

1. Define the schema
2. Create a parser prompt that emits strict JSON
3. Canonicalize the JSON
4. Serialize the canonical form into text
5. Embed both raw text and canonical serialization
6. Compare hybrid retrieval quality on a small benchmark set

The prototype now covers steps 1 through 4 directly, and lays the groundwork
for steps 5 and 6.

## V1 architecture

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

## Practical V1 constraints

Dialectica should not try to solve full formal reasoning in version one.
Instead, version one should aim to be useful for:

- decomposing prompts
- retrieving relevant prior reasoning
- surfacing contradictions
- carrying forward explicit constraints

## Next implementation steps

- Replace or augment the heuristic parser with an LLM-backed parser
- Expand the benchmark set to 25 to 50 varied utterances
- Add embedding generation for raw text and canonical graph serializations
- Add hybrid retrieval experiments and scoring
- Measure whether logical retrieval beats text-only retrieval for selected tasks

