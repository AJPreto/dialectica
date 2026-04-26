# Gold Answer Keys

This file is a human-readable view of the current gold labels in the benchmark JSON files.

The benchmark JSON files remain the source of truth:

- `benchmarks/reasoning.sample.json`
- `benchmarks/reasoning.expanded.json`
- `benchmarks/reasoning.messy.json`
- `benchmarks/reasoning_manual.exercise.json`
- `benchmarks/reasoning_manual.pack.json`

## Sample

Source: `reasoning.sample.json`

| ID | Gold | Question |
| --- | --- | --- |
| reasoning-case-001 | yes | May Alice enter the amber workshop? |
| reasoning-case-002 | yes | May Bruno use the milling machine? |
| reasoning-case-003 | unknown | May Alice enter the amber workshop? |
| reasoning-case-004 | unknown | Does Alice hold an amber badge? |
| reasoning-case-005 | yes | May Greta enter the amber workshop? |
| reasoning-case-006 | no | May Carla use the milling machine? |

## Expanded

Source: `reasoning.expanded.json`

| ID | Gold | Question |
| --- | --- | --- |
| reasoning-expanded-imp-001 | yes | Does Alice hold an amber badge? |
| reasoning-expanded-imp-002 | yes | Does Alice hold the amber badge? |
| reasoning-expanded-imp-003 | unknown | Does Alice hold an amber badge? |
| reasoning-expanded-conj-001 | yes | May Alice enter the amber workshop? |
| reasoning-expanded-conj-002 | unknown | May Alice enter the amber workshop? |
| reasoning-expanded-disj-001 | yes | May Alice enter the amber workshop? |
| reasoning-expanded-neg-001 | no | Does Alice hold an amber badge? |
| reasoning-expanded-neg-002 | unknown | May Alice enter the amber workshop? |
| reasoning-expanded-ctr-001 | unknown | Does Alice hold an amber badge? |
| reasoning-expanded-exc-001 | no | May Alice enter the amber workshop? |
| reasoning-expanded-exc-002 | unknown | May Alice enter the amber workshop? |
| reasoning-expanded-exc-003 | unknown | May Alice enter the amber workshop? |
| reasoning-expanded-chain-001 | yes | May Alice enter the amber workshop? |
| reasoning-expanded-chain-002 | yes | May Greta enter the amber workshop? |
| reasoning-expanded-var-001 | yes | May Bruno use the milling machine? |
| reasoning-expanded-var-002 | yes | Can Bruno use the milling machine? |
| reasoning-expanded-var-003 | unknown | May Carla use the milling machine? |
| reasoning-expanded-att-001 | unknown | Does Alice hold an amber badge? |
| reasoning-expanded-att-002 | unknown | May Bruno use the milling machine? |
| reasoning-expanded-amb-001 | unknown | Does Alice hold an amber badge? |
| reasoning-expanded-amb-002 | unknown | Does Alice hold an amber badge? |
| reasoning-expanded-amb-003 | unknown | Does Alice hold the amber badge? |
| reasoning-expanded-num-001 | yes | Is inventory count >= 3? |
| reasoning-expanded-num-002 | yes | Is batch size = 4? |

## Messy

Source: `reasoning.messy.json`

| ID | Gold | Question |
| --- | --- | --- |
| reasoning-messy-chain-001 | yes | May Mira supervise pallet transfers? |
| reasoning-messy-chain-002 | yes | May Mira supervise pallet transfers? |
| reasoning-messy-chain-003 | unknown | May Mira supervise pallet transfers? |
| reasoning-messy-exc-001 | no | May Lena enter the restricted stacks? |
| reasoning-messy-exc-002 | unknown | May Lena enter the restricted stacks? |
| reasoning-messy-exc-003 | unknown | May Lena enter the restricted stacks? |
| reasoning-messy-ctr-001 | unknown | May Nora use the solvent cabinet? |
| reasoning-messy-neg-001 | no | May Ravi activate the test rig? |
| reasoning-messy-att-001 | unknown | May Marta access the heat bay? |
| reasoning-messy-amb-001 | unknown | Does Alice hold an amber badge? |
| reasoning-messy-unc-001 | unknown | May Farah inspect the crane? |
| reasoning-messy-disj-001 | yes | May Imani enter the diagnostics room? |
| reasoning-messy-var-001 | yes | May Dina use the milling machine? |
| reasoning-messy-num-001 | yes | Is batch size = 4? |
| reasoning-messy-num-002 | yes | Is inventory count >= 3? |
| reasoning-messy-mixed-001 | no | May Greta enter lab 4? |
| reasoning-messy-imp-001 | yes | Does Paolo receive an orange permit? |
| reasoning-messy-conj-001 | yes | May Nina enter the clean room? |
| reasoning-messy-disj-002 | yes | May Omar enter server room B? |
| reasoning-messy-var-003 | yes | May Theo calibrate the optic bench? |
| reasoning-messy-neg-002 | no | Does Elias hold a silver badge? |
| reasoning-messy-neg-003 | no | May Priya operate the pallet lift? |
| reasoning-messy-exc-004 | no | May Jonah enter the map vault? |
| reasoning-messy-mixed-002 | no | May Rosa enter lab 7? |
| reasoning-messy-var-004 | no | May Carla use the milling machine? |
| reasoning-messy-imp-002 | no | May Aria open the solvent locker? |
| reasoning-messy-att-002 | no | May Marta access the heat bay? |
| reasoning-messy-chain-004 | unknown | May Talia inspect the hoist? |
| reasoning-messy-amb-002 | unknown | Does Marcus receive a silver pass? |
| reasoning-messy-disj-003 | unknown | May Salma enter the diagnostics room? |

## Manual Exercise

Source: `reasoning_manual.exercise.json`

| ID | Gold | Question |
| --- | --- | --- |
| reasoning-manual-chat-001 | unknown | May Bruno start the calibration console? |

## Manual Pack

Source: `reasoning_manual.pack.json`

| ID | Gold | Question |
| --- | --- | --- |
| reasoning-manual-pack-001 | yes | Does Alice hold an amber badge? |
| reasoning-manual-pack-002 | yes | May Bruno enter the calibration room? |
| reasoning-manual-pack-003 | no | Does Alice hold an amber badge? |
| reasoning-manual-pack-004 | unknown | May Alice enter the amber workshop? |
| reasoning-manual-pack-005 | unknown | May Alice enter the amber workshop? |
| reasoning-manual-pack-006 | yes | Is batch size = 4? |
