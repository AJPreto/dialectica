from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dialectica.reporting import write_v2_report_bundle
from dialectica.scoring import normalize_answer
from dialectica.v2_eval import evaluate_v2_comparison


class V2BenchmarkTests(unittest.TestCase):
    def test_expanded_report_contains_diagnostics(self) -> None:
        dataset = [
            {
                "id": "case-1",
                "difficulty": "easy",
                "category": "simple_implication",
                "categories": ["simple_implication"],
                "paraphrase_group": "implication-pair",
                "context": "If Alice completed amber orientation, then Alice holds an amber badge. Alice completed amber orientation.",
                "question": "Does Alice hold an amber badge?",
                "gold_answer": "yes",
                "answer_type": "boolean",
                "expected_answer": "yes",
                "expected_horn_answer": "entailed",
                "expected_inference_success": True,
                "expected_contradiction_flag": False,
                "expected_exportability": {"horn": "exact", "fol": "exact", "smt": "unsupported"},
                "expected_reasoning_depth": 1,
                "expected_failure_mode": None,
                "expected_behavior": "Single-step implication should work.",
            },
            {
                "id": "case-2",
                "difficulty": "easy",
                "category": "simple_implication",
                "categories": ["simple_implication", "paraphrase_robustness"],
                "paraphrase_group": "implication-pair",
                "context": "If Alice completed the amber orientation, then Alice holds the amber badge. Alice completed the amber orientation.",
                "question": "Does Alice hold the amber badge?",
                "gold_answer": "yes",
                "answer_type": "boolean",
                "expected_answer": "yes",
                "expected_horn_answer": "entailed",
                "expected_inference_success": True,
                "expected_contradiction_flag": False,
                "expected_exportability": {"horn": "exact", "fol": "exact", "smt": "unsupported"},
                "expected_reasoning_depth": 1,
                "expected_failure_mode": None,
                "expected_behavior": "Paraphrase should stay stable.",
            },
            {
                "id": "case-3",
                "difficulty": "medium",
                "category": "contradiction_detection",
                "categories": ["contradiction_detection", "negation", "non_exportable_or_partial"],
                "context": "Alice completed amber orientation. Alice did not complete amber orientation. If Alice completed amber orientation, then Alice holds an amber badge.",
                "question": "Does Alice hold an amber badge?",
                "gold_answer": "no",
                "answer_type": "boolean",
                "expected_answer": "no",
                "expected_horn_answer": "entailed",
                "expected_inference_success": False,
                "expected_contradiction_flag": True,
                "expected_exportability": {"horn": "partial", "fol": "exact", "smt": "unsupported"},
                "expected_reasoning_depth": 1,
                "expected_failure_mode": "contradiction_unresolved",
                "expected_behavior": "This should surface a contradiction and an honest Horn failure.",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.json"
            dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
            report = evaluate_v2_comparison(dataset_path, provider_name="oracle")

            self.assertIn("category_summary", report)
            self.assertIn("simple_implication", report["category_summary"])
            self.assertIn("diagnostics", report)
            self.assertIn("paraphrase_stability", report["diagnostics"])
            self.assertIn("v2_fol", report["aggregate"])
            self.assertEqual(
                report["diagnostics"]["paraphrase_stability"]["modes"]["direct"]["group_count"],
                1,
            )
            self.assertGreaterEqual(
                report["diagnostics"]["export_success_rate"]["by_target"]["horn"]["expectation_match_rate"],
                0.0,
            )
            self.assertTrue(
                any(entry["mode"] == "v2_horn" for entry in report["error_report"]),
                "The contradiction case should create a V2 Horn error entry.",
            )

    def test_v2_report_bundle_renders(self) -> None:
        report = {
            "dataset_path": "benchmarks/v2_reasoning.expanded.json",
            "provider": "oracle",
            "model": None,
            "mode_order": ["direct", "dialectica_compact", "dialectica_filtered", "dialectica_filtered_structural", "v2_horn", "v2_fol"],
            "aggregate": {
                "direct": {"accuracy": 1.0, "average_total_tokens": 0.0, "average_latency_seconds": 0.0},
                "dialectica_compact": {"accuracy": 1.0, "average_total_tokens": 0.0, "average_latency_seconds": 0.0},
                "dialectica_filtered": {"accuracy": 1.0, "average_total_tokens": 0.0, "average_latency_seconds": 0.0},
                "dialectica_filtered_structural": {"accuracy": 1.0, "average_total_tokens": 0.0, "average_latency_seconds": 0.0},
                "v2_horn": {"accuracy": 0.5, "average_total_tokens": 0.0, "average_latency_seconds": 0.0},
                "v2_fol": {"accuracy": 1.0, "average_total_tokens": 0.0, "average_latency_seconds": 0.0},
            },
            "category_summary": {
                "simple_implication": {
                    "case_count": 2,
                    "modes": {
                        "direct": {"accuracy": 1.0},
                        "dialectica_compact": {"accuracy": 1.0},
                        "dialectica_filtered": {"accuracy": 1.0},
                        "dialectica_filtered_structural": {"accuracy": 1.0},
                        "v2_horn": {"accuracy": 1.0},
                        "v2_fol": {"accuracy": 1.0},
                    },
                }
            },
            "difficulty_summary": {
                "easy": {
                    "case_count": 2,
                    "modes": {
                        "direct": {"accuracy": 1.0},
                        "dialectica_compact": {"accuracy": 1.0},
                        "dialectica_filtered": {"accuracy": 1.0},
                        "dialectica_filtered_structural": {"accuracy": 1.0},
                        "v2_horn": {"accuracy": 0.5},
                        "v2_fol": {"accuracy": 1.0},
                    },
                }
            },
            "comparison_table": [
                {
                    "mode": "direct",
                    "label": "Direct",
                    "accuracy": 1.0,
                    "average_total_tokens": 0.0,
                    "average_latency_seconds": 0.0,
                    "negation_score": 1.0,
                    "exception_score": 1.0,
                    "contradiction_score": 1.0,
                    "paraphrase_stability": 1.0,
                    "average_reasoning_depth_solved": 1.0,
                }
            ],
            "diagnostics": {
                "contradiction_sensitivity": {"v2_horn_flag_match_rate": 1.0, "modes": {"direct": {"accuracy": 1.0}}},
                "explanation_faithfulness_proxy": {"v2_horn": {"pass_rate": 0.5}},
                "export_success_rate": {"by_target": {"horn": {"expectation_match_rate": 0.5}}},
            },
            "error_report": [
                {
                    "case_id": "case-3",
                    "mode": "v2_horn",
                    "category": "contradiction_detection",
                    "predicted": "yes",
                    "gold": "no",
                    "expected_failure_mode": "contradiction_unresolved",
                }
            ],
            "cases": [
                {
                    "id": "case-1",
                    "context": "short context",
                    "gold_answer": "yes",
                    "conditions": [
                        {"name": "direct", "correct": True, "token_counts": {"total_tokens": 0}},
                        {"name": "v2_horn", "correct": True, "token_counts": {"total_tokens": 0}},
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "report.md"
            charts_dir = Path(tmpdir) / "charts"
            manifest = write_v2_report_bundle(report=report, markdown_path=markdown_path, charts_dir=charts_dir)

            self.assertTrue(markdown_path.exists())
            self.assertTrue((charts_dir / "category_accuracy.svg").exists())
            self.assertIn("markdown", manifest)

    def test_ternary_unknown_answers_are_supported(self) -> None:
        self.assertEqual(normalize_answer("cannot determine", "ternary"), "unknown")

        dataset = [
            {
                "id": "case-unknown",
                "difficulty": "medium",
                "category": "simple_implication",
                "categories": ["simple_implication"],
                "context": "If Alice completed amber orientation, then Alice holds an amber badge. Bruno completed amber orientation.",
                "question": "Does Alice hold an amber badge?",
                "gold_answer": "unknown",
                "answer_type": "ternary",
                "choices": ["yes", "no", "unknown"],
                "expected_answer": "unknown",
                "expected_horn_answer": "not_entailed",
                "expected_inference_success": True,
                "expected_contradiction_flag": False,
                "expected_exportability": {"horn": "exact", "fol": "exact", "smt": "unsupported"},
                "expected_reasoning_depth": 1,
                "expected_failure_mode": None,
                "expected_behavior": "The missing antecedent match should leave the answer unknown.",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.json"
            dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
            report = evaluate_v2_comparison(dataset_path, provider_name="oracle")

            self.assertEqual(report["cases"][0]["answer_type"], "ternary")
            self.assertEqual(report["cases"][0]["choices"], ["yes", "no", "unknown"])
            v2_horn = next(condition for condition in report["cases"][0]["conditions"] if condition["name"] == "v2_horn")
            self.assertEqual(v2_horn["predicted"], "unknown")
            self.assertTrue(v2_horn["correct"])


if __name__ == "__main__":
    unittest.main()
