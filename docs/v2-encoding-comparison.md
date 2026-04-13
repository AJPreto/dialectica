# V2 Encoding Comparison

This document records the practical V2 encoding decision.

## Summary table

| Encoding | Expressivity | Determinism | Implementation complexity | Laptop-friendliness | Explanation quality | Robustness to partial language | Compile from same AST |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Horn / Datalog / Prolog-like | Good for facts, rules, chains, and guarded exceptions | High | Low | High | High | Good if unsupported residue is withheld explicitly | High |
| Typed FOL | Higher, especially for quantification and nested logic | Medium without a prover | Medium | Medium | Medium | Moderate, but easier to over-formalize | High |
| SMT-style constraints | Best for arithmetic/equalities/inequalities | High with a solver | Medium to high | Medium | Lower | Lower unless numeric intent is explicit | Medium |

## Chosen default

Dialectica V2 uses:

- `horn` as the default end-to-end backend
- `fol` as the main comparison/export path
- `smt` as an experimental partial export target for future arithmetic work

## Why Horn wins first

Horn is the best first end-to-end choice because it gives us all of this at
once:

- deterministic reasoning
- cheap local execution
- direct proof traces
- clear explanation paths
- graceful behavior when the translator only partially formalizes a sentence

## What FOL adds

FOL is still valuable because it is a better target for:

- quantification
- eventual theorem-prover integration
- comparing the same AST against a richer formalization
- checking whether a sentence is only partially Horn-compilable

## What SMT adds later

SMT becomes attractive when the translator reliably emits:

- arithmetic expressions
- equality and inequality constraints
- numeric threshold rules

It should arrive after the hybrid AST and Horn path are stable, not before.

## Evaluation plan

Compare V1 versus V2, and compare Horn versus FOL export quality, on:

- contradiction sensitivity
- negation handling
- conditions and exceptions
- rule-chain query answering
- arithmetic or equation handling when present
- compactness and inspectability
- explanation faithfulness

The practical milestone order is:

1. stabilize the shared AST
2. benchmark Horn end-to-end on controlled tasks
3. compare Horn and FOL exports on the same AST
4. add SMT-oriented cases once arithmetic translation is reliable

