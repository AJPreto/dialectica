# Reasoning Methods

Dialectica supports several ways to answer a context-plus-question task. They
fall into three broad families:

- raw prompting over prose
- prompting over a structured encoding
- deterministic symbolic execution over a compiled representation

This guide describes what happens inside each method in broad terms.

## Shared Setup

Most reasoning runs start with the same ingredients:

- a raw context
- a raw question
- a target answer space such as `yes`, `no`, or `unknown`

From there, the methods differ in what representation they use and how much of
the reasoning is delegated to a model versus executed by the local engine.

## Direct

`Direct` is the plain prompting baseline.

What happens:

1. the raw context stays as prose
2. the raw question stays as prose
3. the provider receives both directly
4. the model answers from natural language alone

What this method is asking the model to do:

- parse the text
- track the relevant facts
- resolve contradictions or gaps
- perform the reasoning
- produce the final answer

Where it helps:

- simple implications
- obvious explicit facts
- quick baseline comparisons

Where it tends to struggle:

- ambiguity
- exception logic
- contradiction handling
- underdetermined cases where the right answer is conservative

## Compact

`Compact` replaces raw prose with Dialectica's parsed compact serialization.

What happens:

1. the context is parsed into a logical-form style block graph
2. the question is parsed the same way
3. both parsed forms are serialized into a compact structural format
4. the provider answers from the encoded representation

What this is trying to buy:

- less dependence on surface wording
- more explicit logical structure
- a prompt that exposes roles and relations directly

The tradeoff is that parser mistakes now propagate forward, and the model still
has to interpret the encoding rather than execute it mechanically.

## Filtered

`Filtered` uses the same compact encoding after pruning the context to a
question-conditioned subgraph.

What happens:

1. the context is parsed into the same logical-form blocks and relations
2. the question is parsed too
3. the filter scores context blocks by question overlap and block type
4. it keeps the best-matching blocks and expands through supporting relations
5. the reduced logical form is serialized compactly
6. the provider answers from that filtered encoding

What this is trying to buy:

- fewer distractors
- smaller prompts
- sharper attention on the likely reasoning chain

The main risk is that the filter can remove a necessary bridge fact or a useful
ambiguity signal.

## Filtered Structural

`Filtered Structural` adds a second description of the filtered graph in the
form of a structural fingerprint summary.

What happens:

1. the context is parsed
2. the context is filtered to the question-conditioned subgraph
3. the filtered form is serialized compactly
4. a structural fingerprint summary is generated for context and question
5. the provider gets both the compact encoding and the fingerprint summaries

What this is trying to buy:

- a more shape-oriented cue for the logical structure
- some robustness to wording changes
- a stable summary of relation layout

The cost is prompt size and complexity. The fingerprint is still descriptive,
not executable, so the model has to interpret it well for it to help.

## Horn Reasoner

`Horn Reasoner` is the first fully symbolic path.

What happens:

1. the raw context and question go through the controlled translator
2. the translator emits a hybrid document of facts, rules, queries, residue,
   and semantic annotations
3. the compiler exports the Horn-safe fragment into a machine-readable program
4. unsupported or unsafe statements are withheld instead of guessed through
5. the Horn engine forward-chains over exported facts and rules
6. explicit exceptions can block a derivation
7. the engine returns a symbolic result that is normalized into the task's
   answer space

What makes it useful:

- deterministic execution
- cheap local runs
- explicit reasoning traces
- reliable handling of Horn-style implications and chains

What limits it:

- no broad support for negation as a first-class signed literal
- no disjunction
- no arithmetic reasoning
- conservative refusal when the input falls outside the safe fragment

## FOL Reasoner

`FOL Reasoner` is the broader symbolic path.

What happens:

1. the raw context and question go through the same controlled translator
2. the compiler exports the safe fragment into a FOL-style artifact and proof
   program
3. facts become signed literals
4. rules become heads plus one or more antecedent branches
5. disjunction in antecedents is expanded into alternative branches
6. exceptions are kept as guarded blockers
7. the deterministic engine performs skeptical proof search over the compiled
   program
8. conflicts, blockers, and missing support are preserved through to the final
   answer instead of being smoothed away

Why it is stronger than Horn on many tasks:

- it can represent positive and negative literals
- it can cover more of the safe fragment
- it handles contradictions more skeptically
- it treats exception logic more carefully

Conceptually, this path turns prose into formal statements, compiles those
statements into a safe proof program, and then searches for an answer while
actively checking for blockers and conflicts.

## External Manual Baselines

Dialectica can also compare against external manual runs, such as copying cases
into ChatGPT and recording the answers.

That lane is useful for evaluation, but it is not a native backend. The repo
stores the observed answers, not the model's internal representation or proof
process.

## Reading The Tradeoffs

At a high level:

- prompt-first methods are flexible but can over-read the text
- encoding-based prompting methods expose more structure but still rely on a
  model to interpret that structure
- symbolic methods are narrower but clearer about why an answer is or is not
  licensed

That is the main design split in Dialectica: use structure either as better
prompt material or as something the local engine can execute directly.
