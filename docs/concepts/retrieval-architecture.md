# Retrieval Architecture

Dialectica has a retrieval-oriented lane that focuses on turning messy text
into a structured representation that can be stored, compared, and reused.

This lane is not trying to solve all formal reasoning by itself. Its job is to
make downstream retrieval and prompting more disciplined.

## Suggested First Build

The fastest path to a working system is:

1. define the schema
2. create a parser prompt that emits strict JSON
3. canonicalize the JSON
4. serialize the canonical form into text
5. embed both raw text and canonical serialization
6. compare hybrid retrieval quality on a small benchmark set

The current local toolchain covers the first four steps directly and gives you
the scaffolding for the retrieval experiments after that.

## Processing Flow

```text
User text
  -> Parser
  -> LogicalForm JSON
  -> Canonicalizer
  -> Canonical serialization
  -> Embeddings
  -> Vector store

Query
  -> Parser
  -> LogicalForm JSON
  -> Canonical serialization
  -> Hybrid retrieval
  -> Downstream agent
```

## Why Hybrid Retrieval

The retrieval lane works best when it keeps multiple views of the same source:

- the original text for semantic breadth
- the canonical logical serialization for structural stability
- optional block-level views for fine-grained matching

That combination helps the system retrieve not just similar wording, but also
similar roles, dependencies, and constraints.

## Practical Constraints

The retrieval-oriented path should not pretend to be a full theorem prover.
Its value is in making downstream work easier and safer:

- decomposing prompts into clearer units
- retrieving relevant prior reasoning
- surfacing contradictions
- carrying forward explicit constraints

When a task needs deterministic inference over a safe fragment, the symbolic
reasoning backends are the better fit.

## Related Docs

- [Foundations](./foundations.md)
- [Reasoning Methods](./reasoning-methods.md)
- [Objective Evaluation](../objective-evaluation.md)
