# Architecture Notes

## Recommended V1 pipeline

```text
input text
  -> parser model
  -> schema validation
  -> canonicalizer
  -> canonical text serialization
  -> embeddings
  -> vector index
  -> hybrid retrieval
  -> downstream generation
```

## Embedding strategy

Use three representational levels.

### 1. Raw text embedding

Captures broad semantic similarity and stylistic nuance.

### 2. Whole-graph canonical embedding

Serialize the parsed graph into a stable textual form, then embed it.

Example serialization:

```text
BLOCK b1 condition positive "battery is dead"
BLOCK b2 outcome negative "car does not start"
BLOCK b3 exception positive "car is jump started"
REL b1 implies b2
REL b3 unless b2
```

This tends to improve retrieval over reasoning structure.

### 3. Block-level embeddings

Embed each block independently to support:

- fine-grained retrieval
- contradiction search
- memory updates
- relation-local comparisons

## Retrieval scoring

A practical V1 score can combine:

- text cosine similarity
- canonical graph cosine similarity
- block overlap score
- relation overlap score

Example:

```text
score = 0.40 * text_similarity
      + 0.35 * graph_similarity
      + 0.15 * block_overlap
      + 0.10 * relation_overlap
```

## Good first use cases

- Prompt decomposition for agent orchestration
- Constraint-aware memory retrieval
- Contradiction detection across notes or conversations
- Policy and requirement extraction
- Research note indexing

## What not to do in V1

- Full theorem proving
- Strict symbolic execution over noisy user language
- Assuming every sentence has one clean parse
- Treating parser confidence as truth

## Evaluation ideas

Measure whether logical representations improve retrieval for:

- negation-sensitive queries
- conditional queries
- exception-heavy queries
- goal and constraint separation

## Suggested milestone order

1. Schema and prompt
2. Small gold dataset
3. Validation and canonicalization
4. Embedding experiments
5. Retrieval benchmark
6. Agent integration
