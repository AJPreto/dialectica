# Manual ChatGPT Pack

These prompts are intentionally minimal for ChatGPT web reliability.

Instructions:
- Start a fresh chat if the current one has been flaky.
- Copy one case at a time.
- Ask for a one-word answer only: `yes`, `no`, or `unknown`.
- When you have the results, paste them back into the response template in `examples/reasoning/external-chat-pack-response.template.json`.

## case-001

Use only the context below.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice holds an amber badge. Alice completed amber orientation.

Question: Does Alice hold an amber badge?

## case-002

Use only the context below.

Reply with only one word:
yes
or
no
or
unknown

Context: If Bruno holds a cobalt badge or Bruno has temporary clearance, then Bruno may enter the calibration room. Bruno holds a cobalt badge.

Question: May Bruno enter the calibration room?

## case-003

Use only the context below.

Reply with only one word:
yes
or
no
or
unknown

Context: Alice does not hold an amber badge.

Question: Does Alice hold an amber badge?

## case-004

Use only the context below.

If the context contains a contradiction that affects the conclusion, answer conservatively.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice may enter the amber workshop. Alice completed amber orientation. Alice may not enter the amber workshop.

Question: May Alice enter the amber workshop?

## case-005

Use only the context below.

If an exception blocks a conclusion, answer conservatively.

Reply with only one word:
yes
or
no
or
unknown

Context: If Alice completed amber orientation, then Alice may enter the amber workshop unless Alice is suspended. Alice completed amber orientation. Alice is suspended.

Question: May Alice enter the amber workshop?

## case-006

Use only the context below.

Reply with only one word:
yes
or
no
or
unknown

Context: batch size = 4.

Question: Is batch size = 4?
