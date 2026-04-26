# Full Manual ChatGPT Pack

This pack mirrors the full expanded reasoning benchmark in [reasoning.expanded.json](../benchmarks/reasoning.expanded.json).

Instructions:
- Copy one full case block at a time into ChatGPT.
- Start a fresh chat if the current one becomes flaky.
- Each case is standalone.
- Reply should be one word only: `yes`, `no`, or `unknown`.
- When you have all answers, put them into `examples/reasoning/external-chat-expanded-response.template.json`.

## case-001 | reasoning-expanded-imp-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice holds an amber badge. Alice completed amber orientation.

Question: Does Alice hold an amber badge?

## case-002 | reasoning-expanded-imp-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed the amber orientation, then Alice holds the amber badge. Alice completed the amber orientation.

Question: Does Alice hold the amber badge?

## case-003 | reasoning-expanded-imp-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice holds an amber badge. Bruno completed amber orientation.

Question: Does Alice hold an amber badge?

## case-004 | reasoning-expanded-conj-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation and Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation. Alice holds an amber badge.

Question: May Alice enter the amber workshop?

## case-005 | reasoning-expanded-conj-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation and Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-006 | reasoning-expanded-disj-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation or Alice holds an amber badge, then Alice may enter the amber workshop. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-007 | reasoning-expanded-neg-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: Alice does not hold an amber badge.

Question: Does Alice hold an amber badge?

## case-008 | reasoning-expanded-neg-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice may enter the amber workshop. Alice completed amber orientation. Alice may not enter the amber workshop.

Question: May Alice enter the amber workshop?

## case-009 | reasoning-expanded-ctr-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: Alice completed amber orientation. Alice did not complete amber orientation. If Alice completed amber orientation, then Alice holds an amber badge.

Question: Does Alice hold an amber badge?

## case-010 | reasoning-expanded-exc-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice may enter the amber workshop unless Alice is suspended. Alice completed amber orientation. Alice is suspended. Alice may not enter the amber workshop.

Question: May Alice enter the amber workshop?

## case-011 | reasoning-expanded-exc-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice may enter the amber workshop unless Alice is suspended. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-012 | reasoning-expanded-exc-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed the amber orientation, then Alice may enter the amber workshop unless Alice is suspended. Alice completed the amber orientation.

Question: May Alice enter the amber workshop?

## case-013 | reasoning-expanded-chain-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice holds an amber badge. If Alice holds an amber badge, then Alice is cleared for the amber zone. If Alice is cleared for the amber zone, then Alice may enter the amber workshop. Alice completed amber orientation.

Question: May Alice enter the amber workshop?

## case-014 | reasoning-expanded-chain-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: If Greta completed amber orientation, then Greta holds an amber badge. If Greta holds an amber badge, then Greta is cleared for the amber zone. If Greta is cleared for the amber zone, then Greta has a workstation key. If Greta has a workstation key, then Greta may enter the amber workshop. Bruno completed cobalt orientation. If Bruno completed cobalt orientation, then Bruno holds a cobalt badge. Greta completed amber orientation.

Question: May Greta enter the amber workshop?

## case-015 | reasoning-expanded-var-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: All certified operators may use the milling machine. Bruno is a certified operator.

Question: May Bruno use the milling machine?

## case-016 | reasoning-expanded-var-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: All certified operators can use the milling machine. Bruno is a certified operator.

Question: Can Bruno use the milling machine?

## case-017 | reasoning-expanded-var-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: All certified operators may use the milling machine. Bruno is a certified operator. Carla is a guest visitor.

Question: May Carla use the milling machine?

## case-018 | reasoning-expanded-att-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: According to the intern, Alice completed amber orientation. If Alice completed amber orientation, then Alice holds an amber badge.

Question: Does Alice hold an amber badge?

## case-019 | reasoning-expanded-att-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: According to the inspector, Bruno is a certified operator. All certified operators may use the milling machine.

Question: May Bruno use the milling machine?

## case-020 | reasoning-expanded-amb-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: Alice completed amber orientation. She holds an amber badge.

Question: Does Alice hold an amber badge?

## case-021 | reasoning-expanded-amb-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: Maybe Alice completed amber orientation. If Alice completed amber orientation, then Alice holds an amber badge.

Question: Does Alice hold an amber badge?

## case-022 | reasoning-expanded-amb-003

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: Alice completed the amber orientation. She holds the amber badge.

Question: Does Alice hold the amber badge?

## case-023 | reasoning-expanded-num-001

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: inventory count >= 3.

Question: Is inventory count >= 3?

## case-024 | reasoning-expanded-num-002

Use only the context below.

Answer conservatively.

If the conclusion depends on a contradiction, uncertainty, unresolved reference, attribution, or a missing premise, do not assert it.

Reply with only one word:
yes
or
no
or
unknown

Context: batch size = 4.

Question: Is batch size = 4?
