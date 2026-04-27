# Foundations

Dialectica sits between raw language and downstream reasoning or retrieval.
Its job is to turn prose into a structured intermediate representation that is
stable enough for machines to work with while still staying faithful to the
source.

## Core Idea

Instead of embedding or prompting over only raw text, Dialectica creates a
two-layer representation:

1. natural language input
2. a logical block graph

That graph can then be used in two complementary ways:

- as a prompt intermediate for downstream agents
- as a canonical representation to embed, compare, and index

## Why This Helps

Raw text often blurs distinctions that matter for reasoning:

- goals vs constraints
- claims vs evidence
- conditions vs outcomes
- negation
- exceptions
- uncertainty

Dialectica makes those distinctions explicit without pretending the source was
cleaner than it really was.

## Design Principles

### 1. Typed semantics over rigid formalism

The first useful target is a typed semantic graph, not a full symbolic logic
pipeline. Natural language is too ambiguous for strict formalization to be the
only operating mode.

### 2. Faithfulness over precision

If the source text is vague, the representation should stay vague. The system
should be able to emit uncertainty and ambiguity instead of inventing a neat
but false structure.

### 3. Hybrid retrieval

Store and compare multiple views of the same material:

- the original text
- the canonicalized logical representation
- optional block-level text or embeddings

This keeps semantic similarity and explicit structure working together.

### 4. Decomposability

The smallest useful unit is a block. A single utterance may yield multiple
blocks and multiple relations between them.

## System Components

### Parser

Transforms natural language into structured blocks and relations.

Input:

- raw utterance or document span

Output:

- `LogicalForm` JSON object

### Canonicalizer

Normalizes parser output into a stable ordering and serialization so
semantically equivalent outputs are more likely to compare well.

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

### Downstream Agent

Consumes both the original user text and the parsed logical structure for:

- planning
- constrained answering
- contradiction checking
- memory retrieval
- prompt construction

## Minimal Schema

The base schema supports block types such as:

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

See [logical-blocks.schema.json](../../schema/logical-blocks.schema.json).

## Rich Encoding Layer

Dialectica also has an optional TPTP-inspired encoding layer that adds:

- annotated formulae
- formula roles
- typed signatures
- quantifiers and connectives
- provenance and useful metadata

Start here:

- [Encoding Schema](../../schema/logical-encoding.schema.json)
- [Encoding Notes](../tptp-inspired-encoding.md)
- [Sample Encoding](../../examples/sample-encoding.json)

## Worked Example

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
