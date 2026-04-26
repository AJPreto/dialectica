# Gold Answer Keys

This file is a human-readable view of the current gold labels in the benchmark JSON files.

The benchmark JSON files remain the source of truth:

- `benchmarks/v2_reasoning.sample.json`
- `benchmarks/v2_reasoning.expanded.json`
- `benchmarks/v2_reasoning.messy.json`
- `benchmarks/v2_chatgpt_manual.exercise.json`
- `benchmarks/v2_chatgpt_manual.pack.json`

## Sample

Source: `v2_reasoning.sample.json`

| ID | Gold | Question |
| --- | --- | --- |
| v2-case-001 | yes | May Alice enter the amber workshop? |
| v2-case-002 | yes | May Bruno use the milling machine? |
| v2-case-003 | unknown | May Alice enter the amber workshop? |
| v2-case-004 | unknown | Does Alice hold an amber badge? |
| v2-case-005 | yes | May Greta enter the amber workshop? |
| v2-case-006 | no | May Carla use the milling machine? |

## Expanded

Source: `v2_reasoning.expanded.json`

| ID | Gold | Question |
| --- | --- | --- |
| v2x-imp-001 | yes | Does Alice hold an amber badge? |
| v2x-imp-002 | yes | Does Alice hold the amber badge? |
| v2x-imp-003 | unknown | Does Alice hold an amber badge? |
| v2x-conj-001 | yes | May Alice enter the amber workshop? |
| v2x-conj-002 | unknown | May Alice enter the amber workshop? |
| v2x-disj-001 | yes | May Alice enter the amber workshop? |
| v2x-neg-001 | no | Does Alice hold an amber badge? |
| v2x-neg-002 | unknown | May Alice enter the amber workshop? |
| v2x-ctr-001 | unknown | Does Alice hold an amber badge? |
| v2x-exc-001 | no | May Alice enter the amber workshop? |
| v2x-exc-002 | unknown | May Alice enter the amber workshop? |
| v2x-exc-003 | unknown | May Alice enter the amber workshop? |
| v2x-chain-001 | yes | May Alice enter the amber workshop? |
| v2x-chain-002 | yes | May Greta enter the amber workshop? |
| v2x-var-001 | yes | May Bruno use the milling machine? |
| v2x-var-002 | yes | Can Bruno use the milling machine? |
| v2x-var-003 | unknown | May Carla use the milling machine? |
| v2x-att-001 | unknown | Does Alice hold an amber badge? |
| v2x-att-002 | unknown | May Bruno use the milling machine? |
| v2x-amb-001 | unknown | Does Alice hold an amber badge? |
| v2x-amb-002 | unknown | Does Alice hold an amber badge? |
| v2x-amb-003 | unknown | Does Alice hold the amber badge? |
| v2x-num-001 | yes | Is inventory count >= 3? |
| v2x-num-002 | yes | Is batch size = 4? |

## Messy

Source: `v2_reasoning.messy.json`

| ID | Gold | Question |
| --- | --- | --- |
| v2m-chain-001 | yes | May Mira supervise pallet transfers? |
| v2m-chain-002 | yes | May Mira supervise pallet transfers? |
| v2m-chain-003 | unknown | May Mira supervise pallet transfers? |
| v2m-exc-001 | no | May Lena enter the restricted stacks? |
| v2m-exc-002 | unknown | May Lena enter the restricted stacks? |
| v2m-exc-003 | unknown | May Lena enter the restricted stacks? |
| v2m-ctr-001 | unknown | May Nora use the solvent cabinet? |
| v2m-neg-001 | no | May Ravi activate the test rig? |
| v2m-att-001 | unknown | May Marta access the heat bay? |
| v2m-amb-001 | unknown | Does Alice hold an amber badge? |
| v2m-unc-001 | unknown | May Farah inspect the crane? |
| v2m-disj-001 | yes | May Imani enter the diagnostics room? |
| v2m-var-001 | yes | May Dina use the milling machine? |
| v2m-num-001 | yes | Is batch size = 4? |
| v2m-num-002 | yes | Is inventory count >= 3? |
| v2m-mixed-001 | no | May Greta enter lab 4? |
| v2m-imp-001 | yes | Does Paolo receive an orange permit? |
| v2m-conj-001 | yes | May Nina enter the clean room? |
| v2m-disj-002 | yes | May Omar enter server room B? |
| v2m-var-003 | yes | May Theo calibrate the optic bench? |
| v2m-neg-002 | no | Does Elias hold a silver badge? |
| v2m-neg-003 | no | May Priya operate the pallet lift? |
| v2m-exc-004 | no | May Jonah enter the map vault? |
| v2m-mixed-002 | no | May Rosa enter lab 7? |
| v2m-var-004 | no | May Carla use the milling machine? |
| v2m-imp-002 | no | May Aria open the solvent locker? |
| v2m-att-002 | no | May Marta access the heat bay? |
| v2m-chain-004 | unknown | May Talia inspect the hoist? |
| v2m-amb-002 | unknown | Does Marcus receive a silver pass? |
| v2m-disj-003 | unknown | May Salma enter the diagnostics room? |

## Manual Exercise

Source: `v2_chatgpt_manual.exercise.json`

| ID | Gold | Question |
| --- | --- | --- |
| v2x-manual-chat-001 | unknown | May Bruno start the calibration console? |

## Manual Pack

Source: `v2_chatgpt_manual.pack.json`

| ID | Gold | Question |
| --- | --- | --- |
| v2x-manual-pack-001 | yes | Does Alice hold an amber badge? |
| v2x-manual-pack-002 | yes | May Bruno enter the calibration room? |
| v2x-manual-pack-003 | no | Does Alice hold an amber badge? |
| v2x-manual-pack-004 | unknown | May Alice enter the amber workshop? |
| v2x-manual-pack-005 | unknown | May Alice enter the amber workshop? |
| v2x-manual-pack-006 | yes | Is batch size = 4? |
