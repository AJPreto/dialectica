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


if __name__ == "__main__":
    unittest.main()
