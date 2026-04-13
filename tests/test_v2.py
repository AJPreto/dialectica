from __future__ import annotations

import unittest

from dialectica.compiler import compile_hybrid_document
from dialectica.engine import reason_over_horn_program
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


if __name__ == "__main__":
    unittest.main()

