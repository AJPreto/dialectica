# Benchmark Condition Examples

This document shows what each current benchmark condition means in practice.

## First principle

`direct` is the original task in raw language.

In the benchmark, it is wrapped in a small instruction so the model returns a
consistent JSON answer format, but conceptually it is still the raw task.

The other conditions are encoded-only routes.
They do not mix the raw task text with extra logical scaffolding.

## Example case

Context:

```text
If Alice completed amber orientation, then Alice holds an amber badge.
If Alice holds an amber badge, then Alice may enter the amber workshop.
Alice completed amber orientation.
If Bruno completed cobalt orientation, then Bruno holds a cobalt badge.
Bruno completed cobalt orientation.
```

Question:

```text
May Alice enter the amber workshop?
```

Gold answer:

```text
yes
```

## What each condition sees

### `direct`

The model sees the raw context and the raw question.

```text
Context:
If Alice completed amber orientation, then Alice holds an amber badge.
If Alice holds an amber badge, then Alice may enter the amber workshop.
Alice completed amber orientation.
If Bruno completed cobalt orientation, then Bruno holds a cobalt badge.
Bruno completed cobalt orientation.

Question:
May Alice enter the amber workshop?
```

This is the baseline closest to the original prompt.

### `dialectica_compact`

The model does not get the raw context or raw question.

It gets only the compact encoding of the full parsed graph.

Sketch:

```text
P|p1|alice completed amber orientation
P|p2|alice holds amber badge
P|p3|alice may enter amber workshop
P|p4|bruno completed cobalt orientation
P|p5|bruno holds cobalt badge

B|if|+|p1
B|out|+|p2
B|if|+|p2
B|out|+|p3
B|c|+|p1
B|if|+|p4
B|out|+|p5
B|c|+|p4

R|p1=>p2
R|p2=>p3
R|p4=>p5
```

This is encoded-only, but it still includes irrelevant Bruno material.

### `dialectica_filtered`

This is the filtered-only route.

It also omits the raw text, but before building the compact encoding it prunes
the logical form to the subgraph most relevant to the question.

So Bruno disappears.

Sketch:

```text
P|p1|alice completed amber orientation
P|p2|alice holds amber badge
P|p3|alice may enter amber workshop

B|if|+|p1
B|out|+|p2
B|if|+|p2
B|out|+|p3
B|c|+|p1

R|p1=>p2
R|p2=>p3
```

This is the clearest implementation of the intended pipeline:

1. parse the original language
2. filter to the relevant logical material
3. answer from the filtered representation only

### `dialectica_structural_compact`

This is `dialectica_compact` plus the structural fingerprint.

So it includes:

- compact full-graph encoding
- structural fingerprint summary

but not the raw text.

Example structural summary:

```json
{
  "scheme": "godel-inspired-v1",
  "graph_signature": "00ep7t-00knhc-0065yl",
  "graph_residues": {
    "1000003": 685865,
    "1000033": 963552,
    "1000037": 287661
  },
  "block_signatures": [
    {"id": "b1", "type": "claim", "signature": "009mxi-00d2lv-00i4im"},
    {"id": "b2", "type": "claim", "signature": "00gp00-007hjd-002j21"},
    {"id": "b3", "type": "condition", "signature": "007h6n-00hs6w-00bia8"},
    {"id": "b4", "type": "condition", "signature": "00g5gh-000ov7-006wcx"},
    {"id": "b5", "type": "condition", "signature": "0077sa-0010ze-007l63"},
    {"id": "b6", "type": "outcome", "signature": "00cw32-00aqnq-00az93"},
    {"id": "b7", "type": "outcome", "signature": "00awmg-003u5a-00dfe7"},
    {"id": "b8", "type": "outcome", "signature": "0002m4-009b7q-003ooi"}
  ],
  "relation_signatures": [
    {"id": "b3->b6", "type": "implies", "signature": "00fcql-00g0z4-00bsoj"},
    {"id": "b4->b7", "type": "implies", "signature": "00fcql-00g0z4-00bsoj"},
    {"id": "b5->b8", "type": "implies", "signature": "00fcql-00g0z4-00bsoj"}
  ],
  "metadata": {
    "symbol_count": 49,
    "block_count": 8,
    "relation_count": 3
  }
}
```

The important thing is not the exact numbers. The important thing is that this
adds a compact summary of graph shape:

- how many blocks and relations exist
- which blocks have matching or different structural signatures
- one graph-level signature for the whole logical object

### `dialectica_filtered_structural`

This is `dialectica_filtered` plus the structural fingerprint.

So it includes:

- compact filtered encoding
- structural fingerprint summary

but not the raw text.

For the filtered Alice-only subgraph, the structural summary becomes smaller:

```json
{
  "scheme": "godel-inspired-v1",
  "graph_signature": "003ot4-000hgs-0059x9",
  "graph_residues": {
    "1000003": 172120,
    "1000033": 22636,
    "1000037": 246141
  },
  "block_signatures": [
    {"id": "b1", "type": "claim", "signature": "00dw2v-006edr-009jfs"},
    {"id": "b2", "type": "condition", "signature": "00k8mq-00j759-0076oj"},
    {"id": "b3", "type": "condition", "signature": "00315t-00d4z1-00jox6"},
    {"id": "b4", "type": "outcome", "signature": "00gnjn-000ge0-009v4m"},
    {"id": "b5", "type": "outcome", "signature": "0024jk-00cw72-00d61i"}
  ],
  "relation_signatures": [
    {"id": "b2->b4", "type": "implies", "signature": "00jmcf-00ggy4-00ar98"},
    {"id": "b3->b5", "type": "implies", "signature": "00jmcf-00ggy4-00ar98"}
  ],
  "metadata": {
    "symbol_count": 43,
    "block_count": 5,
    "relation_count": 2
  }
}
```

Compared with the unfiltered structural route:

- Bruno is gone
- the graph signature changes
- the block count drops from `8` to `5`
- the relation count drops from `3` to `2`

That is the clearest structural example of what filtering is doing before the
model answers.

## Short intuition

- `direct`: original prompt
- `dialectica_compact`: encoded-only full scaffold
- `dialectica_filtered`: encoded-only relevant scaffold
- `dialectica_structural_compact`: encoded-only full scaffold plus structural cue
- `dialectica_filtered_structural`: encoded-only relevant scaffold plus structural cue

## Gold variants

If a dataset includes hand-authored gold logical forms, the benchmark can also
run:

- `dialectica_gold_compact`
- `dialectica_gold_filtered`
- `dialectica_gold_structural_compact`
- `dialectica_gold_filtered_structural`

These use the gold intermediate structure instead of the parser output.

That helps separate two different questions:

1. Is the representation idea good?
2. Is the parser recovering that representation reliably?
