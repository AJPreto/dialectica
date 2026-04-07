"""Command-line interface for Dialectica."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .api import run_server
from .answer_eval import evaluate_answer_dataset, write_report
from .canonical import canonicalize_logical_form, serialize_logical_form
from .evaluate import evaluate_dataset
from .parser import parse_document, parse_text
from .providers import ProviderError
from .validation import validate_logical_form


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dialectica", description="Dialectica prototype tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="Parse text into a logical form")
    parse_parser.add_argument("text", nargs="?", help="Text to parse. If omitted, stdin is used.")
    parse_parser.add_argument("--language", default="en")
    parse_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parse_parser.add_argument("--canonical", action="store_true", help="Print canonical serialization instead of JSON")
    parse_parser.add_argument("--document", action="store_true", help="Parse input as a multi-sentence document")

    serve_parser = subparsers.add_parser("serve", help="Run the local HTTP API")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    eval_parser = subparsers.add_parser("evaluate", help="Run the benchmark harness")
    eval_parser.add_argument(
        "--dataset",
        default=str(Path("benchmarks") / "core.json"),
        help="Path to benchmark dataset JSON",
    )
    eval_parser.add_argument("--pretty", action="store_true", help="Pretty-print the evaluation result")

    answer_eval_parser = subparsers.add_parser("evaluate-answers", help="Run end-to-end answer evaluation")
    answer_eval_parser.add_argument(
        "--dataset",
        default=str(Path("benchmarks") / "objective_qa.sample.json"),
        help="Path to objective QA benchmark dataset JSON",
    )
    answer_eval_parser.add_argument(
        "--provider",
        default="oracle",
        choices=("oracle", "openai"),
        help="Model provider used to answer benchmark questions",
    )
    answer_eval_parser.add_argument("--model", help="Model name for the selected provider")
    answer_eval_parser.add_argument(
        "--include-gold-dialectica",
        action="store_true",
        help="Also run a Dialectica condition using gold logical forms when present in the dataset",
    )
    answer_eval_parser.add_argument("--output", help="Optional path to write the full JSON report")
    answer_eval_parser.add_argument("--pretty", action="store_true", help="Pretty-print the evaluation result")

    args = parser.parse_args(argv)

    if args.command == "parse":
        text = args.text if args.text is not None else sys.stdin.read().strip()
        parsed = parse_document(text, language=args.language) if args.document else parse_text(text, language=args.language)
        logical_form = canonicalize_logical_form(parsed)
        errors = validate_logical_form(logical_form)
        if args.canonical:
            print(serialize_logical_form(logical_form))
        else:
            payload = {"logical_form": logical_form, "validation_errors": errors}
            indent = 2 if args.pretty else None
            print(json.dumps(payload, indent=indent))
        return 0

    if args.command == "serve":
        run_server(host=args.host, port=args.port)
        return 0

    if args.command == "evaluate":
        report = evaluate_dataset(args.dataset)
        indent = 2 if args.pretty else None
        print(json.dumps(report, indent=indent))
        return 0

    if args.command == "evaluate-answers":
        try:
            report = evaluate_answer_dataset(
                args.dataset,
                provider_name=args.provider,
                model=args.model,
                include_gold_dialectica=args.include_gold_dialectica,
            )
        except ProviderError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if args.output:
            write_report(report, args.output)
        indent = 2 if args.pretty else None
        print(json.dumps(report, indent=indent))
        return 0

    return 1
