# Messy Tier Manual ChatGPT Pack (Conservative)

This pack mirrors the current 30-case Tier 2 messy benchmark in [v2_reasoning.messy.json](../benchmarks/v2_reasoning.messy.json).

This variant adds a cautious policy instruction for comparison runs.

Instructions:
- Copy one full case block at a time into ChatGPT.
- Start a fresh chat if the current one becomes flaky.
- Each case is standalone.
- Use only the supplied context.
- If the conclusion is unsupported, conflicted, ambiguous, or underdetermined, answer `unknown`.
- Reply should be one word only: `yes`, `no`, or `unknown`.
- When you have all answers, put them into `examples/v2/external-chat-messy-response.v2.template.json`.

## case-001 | v2m-chain-001

Reply with only one word:
yes
or
no
or
unknown

Context: Morning operations note. If Mira completed dock training, then Mira receives a blue badge. If Mira receives a blue badge, then Mira is cleared for loading bay 2. If Mira is cleared for loading bay 2, then Mira may supervise pallet transfers. Owen received a visitor pass. If Owen received a visitor pass, then Owen may wait in the lobby. The coffee machine is broken. Mira completed dock training.

Question: May Mira supervise pallet transfers?

## case-002 | v2m-chain-002

Reply with only one word:
yes
or
no
or
unknown

Context: Shift memo. If Mira finished dock training, then Mira receives a blue badge. If Mira receives a blue badge, then Mira is cleared for loading bay 2. If Mira is cleared for loading bay 2, then Mira may supervise pallet transfers. Owen signed in as a visitor. The break room fridge is empty. Mira finished dock training.

Question: May Mira supervise pallet transfers?

## case-003 | v2m-chain-003

Reply with only one word:
yes
or
no
or
unknown

Context: Operations note. If Mira completed dock training, then Mira receives a blue badge. If Mira is cleared for loading bay 2, then Mira may supervise pallet transfers. Owen received a visitor pass. If Owen received a visitor pass, then Owen may wait in the lobby. Mira completed dock training. The coffee machine is broken.

Question: May Mira supervise pallet transfers?

## case-004 | v2m-exc-001

Reply with only one word:
yes
or
no
or
unknown

Context: Archive update. If Lena completed archive certification, then Lena may enter the restricted stacks unless Lena is on audit hold. The janitor checked the hallway lights. Lena completed archive certification. Lena filed her weekly report. Lena is on audit hold. Lena may not enter the restricted stacks. The stacks close at midnight.

Question: May Lena enter the restricted stacks?

## case-005 | v2m-exc-002

Reply with only one word:
yes
or
no
or
unknown

Context: Archive update. If Lena completed archive certification, then Lena may enter the restricted stacks unless Lena is on audit hold. The janitor checked the hallway lights. Lena completed archive certification. Lena filed her weekly report. The stacks close at midnight.

Question: May Lena enter the restricted stacks?

## case-006 | v2m-exc-003

Reply with only one word:
yes
or
no
or
unknown

Context: Records bulletin. If Lena finished archive certification, then Lena may enter the restricted stacks unless Lena is on audit hold. The janitor checked the hallway lights. Lena finished archive certification. Lena filed her weekly report. The stacks close at midnight.

Question: May Lena enter the restricted stacks?

## case-007 | v2m-ctr-001

Reply with only one word:
yes
or
no
or
unknown

Context: Safety bulletin. Nora completed solvent training. Nora did not complete solvent training. If Nora completed solvent training, then Nora may use the solvent cabinet. The supervisor filed the schedule. The first aid kit was restocked.

Question: May Nora use the solvent cabinet?

## case-008 | v2m-neg-001

Reply with only one word:
yes
or
no
or
unknown

Context: Control room log. Ravi may not activate the test rig. The maintenance log mentions old batteries. Ravi submitted the safety form. The storage room was cleaned after lunch.

Question: May Ravi activate the test rig?

## case-009 | v2m-att-001

Reply with only one word:
yes
or
no
or
unknown

Context: Inspection note. According to the temporary clerk, Marta completed furnace orientation. If Marta completed furnace orientation, then Marta may access the heat bay. Carlos completed ladder safety. If Carlos completed ladder safety, then Carlos may enter the scaffold room. The lunch truck arrived late.

Question: May Marta access the heat bay?

## case-010 | v2m-amb-001

Reply with only one word:
yes
or
no
or
unknown

Context: Shift summary. Alice completed amber orientation. Bruno filed the inventory form. She holds an amber badge. The printer jammed twice before noon. The afternoon briefing started late.

Question: Does Alice hold an amber badge?

## case-011 | v2m-unc-001

Reply with only one word:
yes
or
no
or
unknown

Context: Yard update. Maybe Farah completed crane briefing. If Farah completed crane briefing, then Farah may inspect the crane. Omar checked the north gate. The weather report was delayed. The spare hooks were counted at noon.

Question: May Farah inspect the crane?

## case-012 | v2m-disj-001

Reply with only one word:
yes
or
no
or
unknown

Context: Access memo. If Imani holds a silver pass or Imani has supervisor override, then Imani may enter the diagnostics room. The copier toner is low. Imani holds a silver pass. The hallway camera was rebooted. The reception desk closed at 17:00.

Question: May Imani enter the diagnostics room?

## case-013 | v2m-var-001

Reply with only one word:
yes
or
no
or
unknown

Context: Workshop report. All certified operators may use the milling machine. Bruno is a certified operator. Carla is a guest visitor. The shift report mentions a delayed delivery. Dina is a certified operator. The spare cutter was locked away.

Question: May Dina use the milling machine?

## case-014 | v2m-num-001

Reply with only one word:
yes
or
no
or
unknown

Context: Warehouse note. batch size = 4. The foreman mentioned spare boxes during the briefing. Mira logged the shipment at 09:00. The loading dock alarm was tested after lunch.

Question: Is batch size = 4?

## case-015 | v2m-num-002

Reply with only one word:
yes
or
no
or
unknown

Context: Inventory note. inventory count >= 3. The team moved two empty pallets before lunch. The loading dock closed at 18:00. A spare clipboard is missing from the office.

Question: Is inventory count >= 3?

## case-016 | v2m-mixed-001

Reply with only one word:
yes
or
no
or
unknown

Context: Lab access memo. If Greta completed access training, then Greta receives a green badge. If Greta receives a green badge and Greta has a workstation key, then Greta may enter lab 4 unless Greta is suspended. Greta completed access training. Greta has a workstation key. The coffee order arrived. Greta is suspended. Greta may not enter lab 4. Bruno checked the extinguisher before the drill.

Question: May Greta enter lab 4?

## case-017 | v2m-imp-001

Reply with only one word:
yes
or
no
or
unknown

Context: Badge desk note. If Paolo completed forklift briefing, then Paolo receives an orange permit. The vending machine jammed again. Paolo completed forklift briefing. A crate of gloves is missing from the cage.

Question: Does Paolo receive an orange permit?

## case-018 | v2m-conj-001

Reply with only one word:
yes
or
no
or
unknown

Context: Workshop notice. If Nina completed clean room orientation and Nina wears a particle badge, then Nina may enter the clean room. The janitor replaced a bulb. Nina completed clean room orientation. A courier signed the log. Nina wears a particle badge. The spare filters arrived late.

Question: May Nina enter the clean room?

## case-019 | v2m-disj-002

Reply with only one word:
yes
or
no
or
unknown

Context: Server room memo. If Omar holds a red pass or Omar has incident override, then Omar may enter server room B. The thermostat was recalibrated after dawn. Omar has incident override. The break room sink drips.

Question: May Omar enter server room B?

## case-020 | v2m-var-003

Reply with only one word:
yes
or
no
or
unknown

Context: Machine audit. All laser-certified technicians may calibrate the optic bench. Serena archived the shipping receipts. Theo is a laser-certified technician. The hallway fan is noisy. A toolbox went missing near the bench.

Question: May Theo calibrate the optic bench?

## case-021 | v2m-neg-002

Reply with only one word:
yes
or
no
or
unknown

Context: Badge log. Elias does not hold a silver badge. The printer toner arrived after noon. A courier signed the door sheet.

Question: Does Elias hold a silver badge?

## case-022 | v2m-neg-003

Reply with only one word:
yes
or
no
or
unknown

Context: Dock notice. Priya may not operate the pallet lift. The loading door squeaks in the morning. A clipboard was replaced before lunch.

Question: May Priya operate the pallet lift?

## case-023 | v2m-exc-004

Reply with only one word:
yes
or
no
or
unknown

Context: Archive bulletin. If Jonah completed vault training, then Jonah may enter the map vault unless Jonah is under review. The radiator clicked all afternoon. Jonah completed vault training. Jonah is under review. Jonah may not enter the map vault. A copier jam delayed the clerk.

Question: May Jonah enter the map vault?

## case-024 | v2m-mixed-002

Reply with only one word:
yes
or
no
or
unknown

Context: Lab memo. If Rosa completed biosafety orientation and Rosa carries a green wristband, then Rosa may enter lab 7 unless Rosa is quarantined. Rosa completed biosafety orientation. The lunch order was late. Rosa carries a green wristband. Rosa is quarantined. Rosa may not enter lab 7. A drawer lock was replaced.

Question: May Rosa enter lab 7?

## case-025 | v2m-var-004

Reply with only one word:
yes
or
no
or
unknown

Context: Workshop report. All certified operators may use the milling machine. Bruno is a certified operator. Carla may not use the milling machine. Dina is a certified operator. The shift report mentions a delayed delivery. The spare cutter was locked away.

Question: May Carla use the milling machine?

## case-026 | v2m-imp-002

Reply with only one word:
yes
or
no
or
unknown

Context: Locker note. If Aria completed solvent training, then Aria may open the solvent locker. The floor was mopped before noon. Aria may not open the solvent locker. A broom handle was replaced after the audit.

Question: May Aria open the solvent locker?

## case-027 | v2m-att-002

Reply with only one word:
yes
or
no
or
unknown

Context: Inspection note. According to the temp clerk, Marta completed furnace orientation. Marta may not access the heat bay. Carlos completed ladder safety. If Carlos completed ladder safety, then Carlos may enter the scaffold room. The lunch truck arrived late.

Question: May Marta access the heat bay?

## case-028 | v2m-chain-004

Reply with only one word:
yes
or
no
or
unknown

Context: Operations note. If Talia completed crane prep, then Talia receives a red tag. If Talia is cleared for south gantry, then Talia may inspect the hoist. The dispatch radio crackled after lunch. Talia completed crane prep. A clipboard went missing from the cage.

Question: May Talia inspect the hoist?

## case-029 | v2m-amb-002

Reply with only one word:
yes
or
no
or
unknown

Context: Shift summary. Marcus completed freezer orientation. Jonah filed the receipt correction. He received a silver pass. The ceiling vent rattled through the afternoon. A mop bucket was left by the stairs.

Question: Does Marcus receive a silver pass?

## case-030 | v2m-disj-003

Reply with only one word:
yes
or
no
or
unknown

Context: Access memo. If Salma holds a bronze pass or Salma has supervisor override, then Salma may enter the diagnostics room. The coffee urn is empty. The hallway camera rebooted after lunch. The reception desk closed early.

Question: May Salma enter the diagnostics room?
