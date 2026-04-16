# Full Manual ChatGPT Pack

This pack mirrors the full expanded V2 benchmark in [v2_reasoning.expanded.json](C:/Users/marti/Documents/GitHub/dialectica/benchmarks/v2_reasoning.expanded.json).

Instructions:
- Copy one full case block at a time into ChatGPT.
- Start a fresh chat if the current one becomes flaky.
- Each case is standalone.
- Reply should be one word only: `yes` or `no`.
- When you have all answers, put them into `examples/v2/external-chat-expanded-response.template.json`.

## case-001 | v2x-imp-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation, then Alice holds an amber badge. Alice completed amber orientation.

Question: Does Alice hold an amber badge?

## case-002 | v2x-imp-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed the amber orientation, then Alice holds the amber badge. Alice completed the amber orientation.

Question: Does Alice hold the amber badge?

## case-003 | v2x-imp-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation, then Alice holds an amber badge. Bruno completed amber orientation.

Question: Does Alice hold an amber badge?

## case-004 | v2x-conj-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation and Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation. Alice holds an amber badge.

Question: May Alice enter the amber workshop?

## case-005 | v2x-conj-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation and Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-006 | v2x-disj-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation or Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-007 | v2x-neg-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: Alice does not hold an amber badge.

Question: Does Alice hold an amber badge?

## case-008 | v2x-neg-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation, then Alice may enter the amber workshop. Alice completed amber orientation. Alice may not enter the amber workshop.

Question: May Alice enter the amber workshop?

## case-009 | v2x-ctr-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: Alice completed amber orientation. Alice did not complete amber orientation. If Alice completed amber orientation, then Alice holds an amber badge.

Question: Does Alice hold an amber badge?

## case-010 | v2x-exc-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation, then Alice may enter the amber workshop unless Alice is suspended. Alice completed amber orientation. Alice is suspended.

Question: May Alice enter the amber workshop?

## case-011 | v2x-exc-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation, then Alice may enter the amber workshop unless Alice is suspended. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-012 | v2x-exc-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed the amber orientation, then Alice may enter the amber workshop unless Alice is suspended. Alice completed the amber orientation.

Question: May Alice enter the amber workshop?

## case-013 | v2x-chain-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Alice completed amber orientation, then Alice holds an amber badge. If Alice holds an amber badge, then Alice is cleared for the amber zone. If Alice is cleared for the amber zone, then Alice may enter the amber workshop. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-014 | v2x-chain-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: If Greta completed amber orientation, then Greta holds an amber badge. If Greta holds an amber badge, then Greta is cleared for the amber zone. If Greta is cleared for the amber zone, then Greta has a workstation key. If Greta has a workstation key, then Greta may enter the amber workshop. Bruno completed cobalt orientation. If Bruno completed cobalt orientation, then Bruno holds a cobalt badge. Greta completed amber orientation.

Question: May Greta enter the amber workshop?

## case-015 | v2x-var-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: All certified operators may use the milling machine. Bruno is a certified operator.

Question: May Bruno use the milling machine?

## case-016 | v2x-var-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: All certified operators can use the milling machine. Bruno is a certified operator.

Question: Can Bruno use the milling machine?

## case-017 | v2x-var-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: All certified operators may use the milling machine. Bruno is a certified operator. Carla is a guest visitor.

Question: May Carla use the milling machine?

## case-018 | v2x-att-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: According to the intern, Alice completed amber orientation. If Alice completed amber orientation, then Alice holds an amber badge.

Question: Does Alice hold an amber badge?

## case-019 | v2x-att-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: According to the inspector, Bruno is a certified operator. All certified operators may use the milling machine.

Question: May Bruno use the milling machine?

## case-020 | v2x-amb-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: Alice completed amber orientation. She holds an amber badge.

Question: Does Alice hold an amber badge?

## case-021 | v2x-amb-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: Maybe Alice completed amber orientation. If Alice completed amber orientation, then Alice holds an amber badge.

Question: Does Alice hold an amber badge?

## case-022 | v2x-amb-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: Alice completed the amber orientation. She holds the amber badge.

Question: Does Alice hold the amber badge?

## case-023 | v2x-num-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: inventory count >= 3.

Question: Is inventory count >= 3?

## case-024 | v2x-num-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no

Context: batch size = 4.

Question: Is batch size = 4?
