from __future__ import annotations

import unittest

from dialectica.compiler import compile_hybrid_document
from dialectica.engine import reason_over_fol_program, reason_over_horn_program
from dialectica.translator import translate_text


class V2PipelineTests(unittest.TestCase):
    def test_access_chain_is_entailed(self) -> None:
        document = translate_text(
            "If Alice completed amber orientation, then Alice holds an amber badge. "
            "If Alice holds an amber badge, then Alice may enter the amber workshop. "
            "Alice completed amber orientation. "
            "May Alice enter the amber workshop?"
        )
        compiled_document, compiled = compile_hybrid_document(document)
        reasoning = reason_over_horn_program(compiled["horn"]["artifact"])
        self.assertEqual(reasoning.answer, "entailed")
        self.assertEqual(compiled["horn"]["status"], "exact")
        query_statement = compiled_document.query_statement()
        self.assertIsNotNone(query_statement)
        self.assertEqual(query_statement.exportability["fol"].status, "exact")

    def test_universal_rule_is_entailed(self) -> None:
        document = translate_text(
            "All certified operators may use the milling machine. "
            "Bruno is a certified operator. "
            "May Bruno use the milling machine?"
        )
        _, compiled = compile_hybrid_document(document)
        reasoning = reason_over_horn_program(compiled["horn"]["artifact"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_modal_paraphrase_is_normalized_consistently(self) -> None:
        document = translate_text(
            "All certified operators can use the milling machine. "
            "Bruno is a certified operator. "
            "Can Bruno use the milling machine?"
        )
        _, compiled = compile_hybrid_document(document)
        reasoning = reason_over_horn_program(compiled["horn"]["artifact"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_uncertain_fact_is_withheld_from_horn(self) -> None:
        document = translate_text(
            "Maybe Alice completed amber orientation. "
            "If Alice completed amber orientation, then Alice holds an amber badge. "
            "Does Alice hold an amber badge?"
        )
        compiled_document, compiled = compile_hybrid_document(document)
        reasoning = reason_over_horn_program(compiled["horn"]["artifact"])
        self.assertEqual(reasoning.answer, "not_entailed")
        first_statement = compiled_document.statements[0]
        self.assertEqual(first_statement.exportability["horn"].status, "partial")
        self.assertIn("Uncertainty", first_statement.exportability["horn"].notes[0])

    def test_duplicate_statements_are_removed_conservatively(self) -> None:
        document = translate_text(
            "Alice completed amber orientation. "
            "Alice completed amber orientation. "
            "Does Alice complete amber orientation?"
        )
        self.assertEqual(len(document.statements), 2)
        facts = [statement for statement in document.statements if statement.kind == "fact"]
        self.assertEqual(len(facts), 1)
        pretranslation = document.metadata.get("pretranslation", {})
        self.assertEqual(pretranslation.get("duplicate_unit_count"), 1)

    def test_explicit_conjunction_is_decomposed_into_smaller_units(self) -> None:
        document = translate_text(
            "Alice completed amber orientation and Alice holds an amber badge. "
            "Does Alice hold an amber badge?"
        )
        self.assertEqual(len(document.statements), 3)
        facts = [statement for statement in document.statements if statement.kind == "fact"]
        self.assertEqual(len(facts), 2)
        predicates = {getattr(statement.formal_core, "predicate", "") for statement in facts}
        self.assertIn("completed_amber_orientation", predicates)
        self.assertIn("holds_an_amber_badge", predicates)
        pretranslation = document.metadata.get("pretranslation", {})
        self.assertEqual(pretranslation.get("decomposition_count"), 1)

    def test_disjunctive_rule_is_entailed_by_fol_backend(self) -> None:
        document = translate_text(
            "If Alice completed amber orientation or Alice holds an amber badge, "
            "then Alice may enter the amber workshop. "
            "Alice completed amber orientation. "
            "May Alice enter the amber workshop?"
        )
        compiled_document, compiled = compile_hybrid_document(document)
        horn_query = compiled_document.query_statement()
        self.assertIsNotNone(horn_query)
        self.assertEqual(horn_query.exportability["fol"].status, "exact")
        self.assertEqual(compiled_document.statements[0].exportability["horn"].status, "unsupported")
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_attributed_fact_is_withheld_from_fol_reasoning(self) -> None:
        document = translate_text(
            "According to the intern, Alice completed amber orientation. "
            "If Alice completed amber orientation, then Alice holds an amber badge. "
            "Does Alice hold an amber badge?"
        )
        compiled_document, compiled = compile_hybrid_document(document)
        self.assertEqual(compiled_document.statements[0].exportability["horn"].status, "partial")
        self.assertEqual(compiled_document.statements[0].exportability["fol"].status, "partial")
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "not_entailed")

    def test_comparison_query_is_supported_by_fol_backend(self) -> None:
        document = translate_text("batch size = 4. Is batch size = 4?")
        compiled_document, compiled = compile_hybrid_document(document)
        self.assertEqual(compiled_document.query_statement().formal_core.operator, "=")
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_generic_receive_rule_is_entailed_by_fol_backend(self) -> None:
        document = translate_text(
            "If Paolo completed forklift briefing, then Paolo receives an orange permit. "
            "Paolo completed forklift briefing. "
            "Does Paolo receive an orange permit?"
        )
        _, compiled = compile_hybrid_document(document)
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_paraphrased_finished_chain_is_entailed_by_fol_backend(self) -> None:
        document = translate_text(
            "If Mira finished dock training, then Mira receives a blue badge. "
            "If Mira receives a blue badge, then Mira is cleared for loading bay 2. "
            "If Mira is cleared for loading bay 2, then Mira may supervise pallet transfers. "
            "Mira finished dock training. "
            "May Mira supervise pallet transfers?"
        )
        _, compiled = compile_hybrid_document(document)
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_rule_conjunction_with_generic_verb_is_not_split_apart(self) -> None:
        document = translate_text(
            "If Nina completed clean room orientation and Nina wears a particle badge, "
            "then Nina may enter the clean room. "
            "Nina completed clean room orientation. "
            "Nina wears a particle badge. "
            "May Nina enter the clean room?"
        )
        self.assertEqual(document.statements[0].kind, "rule")
        _, compiled = compile_hybrid_document(document)
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_failed_conditional_is_not_converted_to_fake_fact(self) -> None:
        document = translate_text(
            "If Alice completed amber orientation, then access follows. "
            "Alice completed amber orientation. "
            "Does Alice hold an amber badge?"
        )
        self.assertEqual(document.statements[0].kind, "residue")
        self.assertIsNone(document.statements[0].formal_core)

    def test_fol_unless_requires_explicit_exception_clearance(self) -> None:
        document = translate_text(
            "If Alice completed amber orientation, then Alice may enter the amber workshop unless Alice is suspended. "
            "Alice completed amber orientation. "
            "May Alice enter the amber workshop?"
        )
        _, compiled = compile_hybrid_document(document)
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "not_entailed")

    def test_fol_unless_derives_when_exception_is_explicitly_false(self) -> None:
        document = translate_text(
            "If Alice completed amber orientation, then Alice may enter the amber workshop unless Alice is suspended. "
            "Alice completed amber orientation. "
            "Alice is not suspended. "
            "May Alice enter the amber workshop?"
        )
        _, compiled = compile_hybrid_document(document)
        reasoning = reason_over_fol_program(compiled["fol"]["artifact"]["program"])
        self.assertEqual(reasoning.answer, "entailed")

    def test_compile_rejects_unknown_export_target_cleanly(self) -> None:
        document = translate_text("Alice completed amber orientation. Does Alice complete amber orientation?")
        with self.assertRaisesRegex(ValueError, "Unsupported export target"):
            compile_hybrid_document(document, targets=("horn", "made_up"))


if __name__ == "__main__":
    unittest.main()
