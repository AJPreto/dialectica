from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import dialectica
from dialectica.cli import main

SAMPLE_SWEEP = Path(__file__).resolve().parents[1] / "benchmarks" / "complexity_sweep.sample.json"


class PublicApiTests(unittest.TestCase):
    def test_parse_returns_valid_canonical_form(self) -> None:
        form = dialectica.parse("Employees may access the lab only if they completed safety training.")
        self.assertEqual(dialectica.validate_logical_form(form), [])
        self.assertEqual(form["blocks"][0]["id"], "b1")

    def test_duplicate_blocks_keep_relations_valid(self) -> None:
        form = dialectica.parse("The test passes but the test passes.")
        self.assertEqual(dialectica.validate_logical_form(form), [])
        self.assertEqual(len(form["blocks"]), 1)
        self.assertEqual(form["ambiguities"][0]["affected_blocks"], ["b1"])

    def test_reason_runs_full_pipeline(self) -> None:
        run = dialectica.reason(
            "If Alice completed amber orientation, then Alice holds an amber badge. "
            "Alice completed amber orientation. "
            "Does Alice hold an amber badge?"
        )
        self.assertEqual(run.answer, "entailed")
        self.assertIn("Derivation trace:", run.explanation)
        self.assertEqual(set(run.to_dict()), {"reasoner", "hybrid_document", "compiled", "reasoning", "explanation"})

    def test_reason_always_compiles_selected_reasoner(self) -> None:
        run = dialectica.reason("batch size = 4. Is batch size = 4?", reasoner="fol", targets=("smt",))
        self.assertEqual(set(run.compiled), {"smt", "fol"})
        self.assertEqual(run.answer, "entailed")


class CliOutputTests(unittest.TestCase):
    def test_dataset_with_utf8_bom_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = Path(tmpdir) / "core.json"
            dataset.write_text(json.dumps([{"id": "c1", "text": "Alice is here."}]), encoding="utf-8-sig")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["evaluate", "--dataset", str(dataset)]), 0)

    def test_sweep_writes_every_explicit_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            argv = [
                "evaluate-complexity-sweep",
                "--dataset",
                str(SAMPLE_SWEEP),
                "--performance-output",
                str(tmp / "perf.json"),
                "--summary-output",
                str(tmp / "summary.json"),
            ]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
            self.assertTrue((tmp / "perf.json").exists())
            self.assertTrue((tmp / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()
