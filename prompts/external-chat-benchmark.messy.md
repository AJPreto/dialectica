# Messy Tier Manual ChatGPT Pack (Raw)

This pack mirrors the Tier 2 messy benchmark in [v2_reasoning.messy.json](C:/Users/marti/Documents/GitHub/dialectica/benchmarks/v2_reasoning.messy.json).

This is the raw manual variant. It minimizes benchmark steering and only specifies the answer format.

Instructions:
- Copy one full case block at a time into ChatGPT.
- Start a fresh chat if the current one becomes flaky.
- Each case is standalone.
- Reply should be one word only: `yes`, `no`, or `unknown`.
- When you have all answers, put them into `examples/v2/external-chat-messy-response.template.json`.

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

## case-014 | v2m-var-002

Reply with only one word:
yes
or
no
or
unknown

Context: Workshop report. All certified operators may use the milling machine. Bruno is a certified operator. Carla is a guest visitor. The shift report mentions a delayed delivery. Dina is a certified operator. The spare cutter was locked away.

Question: May Carla use the milling machine?

## case-015 | v2m-num-001

Reply with only one word:
yes
or
no
or
unknown

Context: Warehouse note. batch size = 4. The foreman mentioned spare boxes during the briefing. Mira logged the shipment at 09:00. The loading dock alarm was tested after lunch.

Question: Is batch size = 4?

## case-016 | v2m-num-002

Reply with only one word:
yes
or
no
or
unknown

Context: Inventory note. inventory count >= 3. The team moved two empty pallets before lunch. The loading dock closed at 18:00. A spare clipboard is missing from the office.

Question: Is inventory count >= 3?

## case-017 | v2m-mixed-001

Reply with only one word:
yes
or
no
or
unknown

Context: Lab access memo. If Greta completed access training, then Greta receives a green badge. If Greta receives a green badge and Greta has a workstation key, then Greta may enter lab 4 unless Greta is suspended. Greta completed access training. Greta has a workstation key. The coffee order arrived. Greta is suspended. Greta may not enter lab 4. Bruno checked the extinguisher before the drill.

Question: May Greta enter lab 4?
