# Gold Answer Key

Canonical benchmark source: benchmarks/reasoning.messy.json.

Use this file to compare manual answers after solving the cases in prompts/external-chat-benchmark.messy.md. Each case below includes the full context, question, and gold answer.

## case-001 | reasoning-messy-chain-001

Gold answer: yes

Question: May Mira supervise pallet transfers?

Context:

> Morning operations note. If Mira completed dock training, then Mira receives a blue badge. If Mira receives a blue badge, then Mira is cleared for loading bay 2. If Mira is cleared for loading bay 2, then Mira may supervise pallet transfers. Owen received a visitor pass. If Owen received a visitor pass, then Owen may wait in the lobby. The coffee machine is broken. Mira completed dock training.

Expected behavior: The system should ignore the visitor side-chain and complete the three-step derivation for Mira.

## case-002 | reasoning-messy-chain-002

Gold answer: yes

Question: May Mira supervise pallet transfers?

Context:

> Shift memo. If Mira finished dock training, then Mira receives a blue badge. If Mira receives a blue badge, then Mira is cleared for loading bay 2. If Mira is cleared for loading bay 2, then Mira may supervise pallet transfers. Owen signed in as a visitor. The break room fridge is empty. Mira finished dock training.

Expected behavior: The paraphrased wording should preserve the same three-step chain and answer.

## case-003 | reasoning-messy-chain-003

Gold answer: unknown

Question: May Mira supervise pallet transfers?

Context:

> Operations note. If Mira completed dock training, then Mira receives a blue badge. If Mira is cleared for loading bay 2, then Mira may supervise pallet transfers. Owen received a visitor pass. If Owen received a visitor pass, then Owen may wait in the lobby. Mira completed dock training. The coffee machine is broken.

Expected behavior: The missing badge-to-clearance link leaves the final permission unsupported, so the answer should remain unknown despite the surrounding noise.

## case-004 | reasoning-messy-exc-001

Gold answer: no

Question: May Lena enter the restricted stacks?

Context:

> Archive update. If Lena completed archive certification, then Lena may enter the restricted stacks unless Lena is on audit hold. The janitor checked the hallway lights. Lena completed archive certification. Lena filed her weekly report. Lena is on audit hold. Lena may not enter the restricted stacks. The stacks close at midnight.

Expected behavior: The audit hold blocks the positive rule and the explicit negative permission supports answering no.

## case-005 | reasoning-messy-exc-002

Gold answer: unknown

Question: May Lena enter the restricted stacks?

Context:

> Archive update. If Lena completed archive certification, then Lena may enter the restricted stacks unless Lena is on audit hold. The janitor checked the hallway lights. Lena completed archive certification. Lena filed her weekly report. The stacks close at midnight.

Expected behavior: Without explicit evidence that Lena is not on audit hold, the guarded rule should not license a positive conclusion under the benchmark's entailment-based semantics.

## case-006 | reasoning-messy-exc-003

Gold answer: unknown

Question: May Lena enter the restricted stacks?

Context:

> Records bulletin. If Lena finished archive certification, then Lena may enter the restricted stacks unless Lena is on audit hold. The janitor checked the hallway lights. Lena finished archive certification. Lena filed her weekly report. The stacks close at midnight.

Expected behavior: The paraphrased exception case should remain unknown because the blocker is not ruled out explicitly.

## case-007 | reasoning-messy-ctr-001

Gold answer: unknown

Question: May Nora use the solvent cabinet?

Context:

> Safety bulletin. Nora completed solvent training. Nora did not complete solvent training. If Nora completed solvent training, then Nora may use the solvent cabinet. The supervisor filed the schedule. The first aid kit was restocked.

Expected behavior: The contradiction affects the rule premise, so the answer should remain unknown rather than forcing either yes or no.

## case-008 | reasoning-messy-neg-001

Gold answer: no

Question: May Ravi activate the test rig?

Context:

> Control room log. Ravi may not activate the test rig. The maintenance log mentions old batteries. Ravi submitted the safety form. The storage room was cleaned after lunch.

Expected behavior: The explicit negative permission directly supports answering no, and the surrounding facts are just distractors.

## case-009 | reasoning-messy-att-001

Gold answer: unknown

Question: May Marta access the heat bay?

Context:

> Inspection note. According to the temporary clerk, Marta completed furnace orientation. If Marta completed furnace orientation, then Marta may access the heat bay. Carlos completed ladder safety. If Carlos completed ladder safety, then Carlos may enter the scaffold room. The lunch truck arrived late.

Expected behavior: The attributed training claim should stay residue instead of becoming settled ground truth, so the answer should remain unknown.

## case-010 | reasoning-messy-amb-001

Gold answer: unknown

Question: Does Alice hold an amber badge?

Context:

> Shift summary. Alice completed amber orientation. Bruno filed the inventory form. She holds an amber badge. The printer jammed twice before noon. The afternoon briefing started late.

Expected behavior: The pronoun should remain unresolved in the longer context rather than being forced onto Alice, so the answer should remain unknown.

## case-011 | reasoning-messy-unc-001

Gold answer: unknown

Question: May Farah inspect the crane?

Context:

> Yard update. Maybe Farah completed crane briefing. If Farah completed crane briefing, then Farah may inspect the crane. Omar checked the north gate. The weather report was delayed. The spare hooks were counted at noon.

Expected behavior: The uncertain briefing statement should be preserved as uncertainty, not promoted to a fact, so the answer should remain unknown.

## case-012 | reasoning-messy-disj-001

Gold answer: yes

Question: May Imani enter the diagnostics room?

Context:

> Access memo. If Imani holds a silver pass or Imani has supervisor override, then Imani may enter the diagnostics room. The copier toner is low. Imani holds a silver pass. The hallway camera was rebooted. The reception desk closed at 17:00.

Expected behavior: The plain-language answer is yes, but the Horn route should still refuse the disjunctive rule.

## case-013 | reasoning-messy-var-001

Gold answer: yes

Question: May Dina use the milling machine?

Context:

> Workshop report. All certified operators may use the milling machine. Bruno is a certified operator. Carla is a guest visitor. The shift report mentions a delayed delivery. Dina is a certified operator. The spare cutter was locked away.

Expected behavior: The quantifier should bind correctly to Dina despite the extra entity and delivery chatter.

## case-014 | reasoning-messy-num-001

Gold answer: yes

Question: Is batch size = 4?

Context:

> Warehouse note. batch size = 4. The foreman mentioned spare boxes during the briefing. Mira logged the shipment at 09:00. The loading dock alarm was tested after lunch.

Expected behavior: The equality fact should survive the noise, but the Horn route should still fail to answer the comparison query.

## case-015 | reasoning-messy-num-002

Gold answer: yes

Question: Is inventory count >= 3?

Context:

> Inventory note. inventory count >= 3. The team moved two empty pallets before lunch. The loading dock closed at 18:00. A spare clipboard is missing from the office.

Expected behavior: The inequality should be answerable in principle, but the Horn route is still expected to miss it.

## case-016 | reasoning-messy-mixed-001

Gold answer: no

Question: May Greta enter lab 4?

Context:

> Lab access memo. If Greta completed access training, then Greta receives a green badge. If Greta receives a green badge and Greta has a workstation key, then Greta may enter lab 4 unless Greta is suspended. Greta completed access training. Greta has a workstation key. The coffee order arrived. Greta is suspended. Greta may not enter lab 4. Bruno checked the extinguisher before the drill.

Expected behavior: The system should complete the badge chain, notice the suspension, and use the explicit negative permission to answer no.

## case-017 | reasoning-messy-imp-001

Gold answer: yes

Question: Does Paolo receive an orange permit?

Context:

> Badge desk note. If Paolo completed forklift briefing, then Paolo receives an orange permit. The vending machine jammed again. Paolo completed forklift briefing. A crate of gloves is missing from the cage.

Expected behavior: The system should ignore the office chatter and derive the orange permit from the single completed-briefing fact.

## case-018 | reasoning-messy-conj-001

Gold answer: yes

Question: May Nina enter the clean room?

Context:

> Workshop notice. If Nina completed clean room orientation and Nina wears a particle badge, then Nina may enter the clean room. The janitor replaced a bulb. Nina completed clean room orientation. A courier signed the log. Nina wears a particle badge. The spare filters arrived late.

Expected behavior: Both conjuncts are present, so the permission should be derivable despite the surrounding memo noise.

## case-019 | reasoning-messy-disj-002

Gold answer: yes

Question: May Omar enter server room B?

Context:

> Server room memo. If Omar holds a red pass or Omar has incident override, then Omar may enter server room B. The thermostat was recalibrated after dawn. Omar has incident override. The break room sink drips.

Expected behavior: The plain-language answer is yes, but the Horn route should still refuse the disjunctive rule.

## case-020 | reasoning-messy-var-003

Gold answer: yes

Question: May Theo calibrate the optic bench?

Context:

> Machine audit. All laser-certified technicians may calibrate the optic bench. Serena archived the shipping receipts. Theo is a laser-certified technician. The hallway fan is noisy. A toolbox went missing near the bench.

Expected behavior: The quantifier should instantiate cleanly for Theo even with unrelated audit chatter nearby.

## case-021 | reasoning-messy-neg-002

Gold answer: no

Question: Does Elias hold a silver badge?

Context:

> Badge log. Elias does not hold a silver badge. The printer toner arrived after noon. A courier signed the door sheet.

Expected behavior: The explicit negative badge fact directly supports answering no.

## case-022 | reasoning-messy-neg-003

Gold answer: no

Question: May Priya operate the pallet lift?

Context:

> Dock notice. Priya may not operate the pallet lift. The loading door squeaks in the morning. A clipboard was replaced before lunch.

Expected behavior: The explicit negative permission supports answering no directly.

## case-023 | reasoning-messy-exc-004

Gold answer: no

Question: May Jonah enter the map vault?

Context:

> Archive bulletin. If Jonah completed vault training, then Jonah may enter the map vault unless Jonah is under review. The radiator clicked all afternoon. Jonah completed vault training. Jonah is under review. Jonah may not enter the map vault. A copier jam delayed the clerk.

Expected behavior: The review status blocks the positive rule and the explicit negative permission supports answering no.

## case-024 | reasoning-messy-mixed-002

Gold answer: no

Question: May Rosa enter lab 7?

Context:

> Lab memo. If Rosa completed biosafety orientation and Rosa carries a green wristband, then Rosa may enter lab 7 unless Rosa is quarantined. Rosa completed biosafety orientation. The lunch order was late. Rosa carries a green wristband. Rosa is quarantined. Rosa may not enter lab 7. A drawer lock was replaced.

Expected behavior: The system should complete the positive chain, notice the quarantine blocker, and use the explicit negative permission to answer no.

## case-025 | reasoning-messy-var-004

Gold answer: no

Question: May Carla use the milling machine?

Context:

> Workshop report. All certified operators may use the milling machine. Bruno is a certified operator. Carla may not use the milling machine. Dina is a certified operator. The shift report mentions a delayed delivery. The spare cutter was locked away.

Expected behavior: The explicit negative permission for Carla supports answering no, while the universal rule still applies to the other named operators.

## case-026 | reasoning-messy-imp-002

Gold answer: no

Question: May Aria open the solvent locker?

Context:

> Locker note. If Aria completed solvent training, then Aria may open the solvent locker. The floor was mopped before noon. Aria may not open the solvent locker. A broom handle was replaced after the audit.

Expected behavior: The rule is present but unsupported, while the explicit negative permission supports answering no.

## case-027 | reasoning-messy-att-002

Gold answer: no

Question: May Marta access the heat bay?

Context:

> Inspection note. According to the temp clerk, Marta completed furnace orientation. Marta may not access the heat bay. Carlos completed ladder safety. If Carlos completed ladder safety, then Carlos may enter the scaffold room. The lunch truck arrived late.

Expected behavior: The attributed positive claim should not override the explicit negative permission, so the answer should be no.

## case-028 | reasoning-messy-chain-004

Gold answer: unknown

Question: May Talia inspect the hoist?

Context:

> Operations note. If Talia completed crane prep, then Talia receives a red tag. If Talia is cleared for south gantry, then Talia may inspect the hoist. The dispatch radio crackled after lunch. Talia completed crane prep. A clipboard went missing from the cage.

Expected behavior: The final permission remains unsupported because the tag-to-clearance step is missing.

## case-029 | reasoning-messy-amb-002

Gold answer: unknown

Question: Does Marcus receive a silver pass?

Context:

> Shift summary. Marcus completed freezer orientation. Jonah filed the receipt correction. He received a silver pass. The ceiling vent rattled through the afternoon. A mop bucket was left by the stairs.

Expected behavior: The pronoun should remain unresolved rather than being forced onto Marcus.

## case-030 | reasoning-messy-disj-003

Gold answer: unknown

Question: May Salma enter the diagnostics room?

Context:

> Access memo. If Salma holds a bronze pass or Salma has supervisor override, then Salma may enter the diagnostics room. The coffee urn is empty. The hallway camera rebooted after lunch. The reception desk closed early.

Expected behavior: Neither antecedent is stated, so the permission should remain unknown even though the rule is present.
