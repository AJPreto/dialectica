"""Command-line interface for Dialectica."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .api import run_server
from .answer_eval import evaluate_answer_dataset, write_performance_summary, write_report
from .canonical import canonicalize_logical_form, serialize_logical_form
from .compiler import compile_hybrid_document, compiled_document_to_dict
from .complexity import (
    generate_complexity_dataset,
    summarize_complexity_report,
    write_complexity_dataset,
    write_complexity_summary,
)
from .engine import reason_over_fol_program, reason_over_horn_program
from .evaluate import evaluate_dataset
from .explainer import explain_fol_reasoning, explain_reasoning
from .fingerprint import compare_fingerprints, fingerprint_logical_form, summarize_fingerprint
from .translator import translate_text
from .v2_eval import evaluate_v2_comparison, write_v2_report
from .parser import parse_document, parse_text
from .providers import ProviderError
from .reporting import write_complexity_report_bundle, write_v2_report_bundle
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

    fingerprint_parser = subparsers.add_parser("fingerprint", help="Build a structural fingerprint from text")
    fingerprint_parser.add_argument("text", nargs="?", help="Text to fingerprint. If omitted, stdin is used.")
    fingerprint_parser.add_argument("--language", default="en")
    fingerprint_parser.add_argument("--document", action="store_true", help="Parse input as a multi-sentence document")
    fingerprint_parser.add_argument("--summary", action="store_true", help="Print a concise fingerprint summary")
    fingerprint_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    compare_parser = subparsers.add_parser("compare-fingerprints", help="Compare structural fingerprints for two texts")
    compare_parser.add_argument("left", help="First text input")
    compare_parser.add_argument("right", help="Second text input")
    compare_parser.add_argument("--language", default="en")
    compare_parser.add_argument("--document", action="store_true", help="Parse inputs as multi-sentence documents")
    compare_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    v2_parser = subparsers.add_parser("v2-run", help="Run the experimental V2 neuro-symbolic pipeline")
    v2_parser.add_argument("text", nargs="?", help="Context text. If omitted, stdin is used.")
    v2_parser.add_argument("--query", help="Optional separate query. If omitted, the last question in the text is used.")
    v2_parser.add_argument(
        "--targets",
        default="horn,fol,smt",
        help="Comma-separated export targets to compile, default: horn,fol,smt",
    )
    v2_parser.add_argument(
        "--reasoner",
        default="horn",
        choices=("horn", "fol"),
        help="Reasoning backend to run over the compiled outputs, default: horn",
    )
    v2_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

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
        choices=("oracle", "openai", "ollama"),
        help="Model provider used to answer benchmark questions",
    )
    answer_eval_parser.add_argument("--model", help="Model name for the selected provider")
    answer_eval_parser.add_argument(
        "--include-gold-dialectica",
        action="store_true",
        help="Also run a Dialectica condition using gold logical forms when present in the dataset",
    )
    answer_eval_parser.add_argument("--output", help="Optional path to write the full JSON report")
    answer_eval_parser.add_argument(
        "--performance-output",
        help="Optional path to write a compact performance summary JSON file",
    )
    answer_eval_parser.add_argument("--pretty", action="store_true", help="Pretty-print the evaluation result")

    complexity_generate_parser = subparsers.add_parser(
        "generate-complexity-benchmark",
        help="Generate a synthetic complexity-sweep objective QA benchmark",
    )
    complexity_generate_parser.add_argument("--levels", type=int, default=6, help="Number of difficulty levels to generate")
    complexity_generate_parser.add_argument(
        "--scenarios-per-level",
        type=int,
        default=3,
        help="Number of scenarios to generate at each level",
    )
    complexity_generate_parser.add_argument(
        "--followups",
        type=int,
        default=3,
        help="Number of follow-up questions to derive from each scenario",
    )
    complexity_generate_parser.add_argument("--seed", type=int, default=7, help="Deterministic random seed")
    complexity_generate_parser.add_argument(
        "--output",
        default=str(Path("benchmarks") / "complexity_sweep.generated.json"),
        help="Path to write the generated benchmark dataset",
    )
    complexity_generate_parser.add_argument("--pretty", action="store_true", help="Pretty-print the generated dataset")

    complexity_eval_parser = subparsers.add_parser(
        "evaluate-complexity-sweep",
        help="Run answer evaluation and summarize results by complexity level",
    )
    complexity_eval_parser.add_argument(
        "--dataset",
        default=str(Path("benchmarks") / "complexity_sweep.generated.json"),
        help="Path to a generated complexity-sweep benchmark dataset JSON file",
    )
    complexity_eval_parser.add_argument(
        "--provider",
        default="oracle",
        choices=("oracle", "openai", "ollama"),
        help="Model provider used to answer benchmark questions",
    )
    complexity_eval_parser.add_argument("--model", help="Model name for the selected provider")
    complexity_eval_parser.add_argument(
        "--include-gold-dialectica",
        action="store_true",
        help="Also run Dialectica conditions using gold logical forms when present in the dataset",
    )
    complexity_eval_parser.add_argument("--output", help="Optional path to write the full JSON report")
    complexity_eval_parser.add_argument(
        "--performance-output",
        help="Optional path to write a compact performance summary JSON file",
    )
    complexity_eval_parser.add_argument(
        "--summary-output",
        help="Optional path to write the level-by-level complexity summary JSON file",
    )
    complexity_eval_parser.add_argument(
        "--markdown-output",
        help="Optional path to write a markdown report that embeds generated charts",
    )
    complexity_eval_parser.add_argument(
        "--charts-dir",
        help="Optional directory to write SVG charts for the markdown report",
    )
    complexity_eval_parser.add_argument("--pretty", action="store_true", help="Pretty-print the complexity summary")

    v2_eval_parser = subparsers.add_parser(
        "evaluate-v2",
        help="Compare direct prompting, V1 filtered encoding, and the experimental V2 Horn backend",
    )
    v2_eval_parser.add_argument(
        "--dataset",
        default=str(Path("benchmarks") / "v2_reasoning.sample.json"),
        help="Path to a V2-compatible comparison benchmark JSON file",
    )
    v2_eval_parser.add_argument(
        "--provider",
        default="ollama",
        choices=("oracle", "openai", "ollama"),
        help="Model provider used for the direct and V1 filtered baselines",
    )
    v2_eval_parser.add_argument("--model", help="Model name for the selected provider")
    v2_eval_parser.add_argument("--output", help="Optional path to write the full JSON comparison report")
    v2_eval_parser.add_argument("--markdown-output", help="Optional path to write a markdown V2 report")
    v2_eval_parser.add_argument("--charts-dir", help="Optional directory to write SVG charts for the V2 report")
    v2_eval_parser.add_argument("--pretty", action="store_true", help="Pretty-print the comparison report")

    v2_render_parser = subparsers.add_parser(
        "render-v2-report",
        help="Render charts and a markdown summary from an existing V2 comparison JSON report",
    )
    v2_render_parser.add_argument("--report", required=True, help="Path to an existing V2 comparison JSON report")
    v2_render_parser.add_argument("--markdown-output", help="Optional markdown output path")
    v2_render_parser.add_argument("--charts-dir", help="Optional charts output directory")
    v2_render_parser.add_argument("--pretty", action="store_true", help="Pretty-print the render manifest")

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

    if args.command == "fingerprint":
        text = args.text if args.text is not None else sys.stdin.read().strip()
        parsed = parse_document(text, language=args.language) if args.document else parse_text(text, language=args.language)
        logical_form = canonicalize_logical_form(parsed)
        fingerprint = fingerprint_logical_form(logical_form)
        payload = summarize_fingerprint(fingerprint) if args.summary else fingerprint
        indent = 2 if args.pretty else None
        print(json.dumps(payload, indent=indent))
        return 0

    if args.command == "compare-fingerprints":
        parse_fn = parse_document if args.document else parse_text
        left_form = canonicalize_logical_form(parse_fn(args.left, language=args.language))
        right_form = canonicalize_logical_form(parse_fn(args.right, language=args.language))
        comparison = compare_fingerprints(
            fingerprint_logical_form(left_form),
            fingerprint_logical_form(right_form),
        )
        indent = 2 if args.pretty else None
        print(json.dumps(comparison, indent=indent))
        return 0

    if args.command == "v2-run":
        text = args.text if args.text is not None else sys.stdin.read().strip()
        requested_targets = [part.strip() for part in args.targets.split(",") if part.strip()]
        if args.reasoner not in requested_targets:
            requested_targets.append(args.reasoner)
        targets = tuple(requested_targets)
        document = translate_text(text, query=args.query)
        compiled_document, compiled_outputs = compile_hybrid_document(document, targets=targets)
        if args.reasoner == "fol":
            reasoning = reason_over_fol_program(compiled_outputs.get("fol", {}).get("artifact", {}).get("program", {}))
            explanation = explain_fol_reasoning(compiled_document, reasoning)
        else:
            reasoning = reason_over_horn_program(compiled_outputs.get("horn", {}).get("artifact", {}))
            explanation = explain_reasoning(compiled_document, reasoning)
        payload = {
            "reasoner": args.reasoner,
            "hybrid_document": compiled_document_to_dict(compiled_document),
            "compiled": compiled_outputs,
            "reasoning": reasoning.to_dict(),
            "explanation": explanation,
        }
        indent = 2 if args.pretty else None
        print(json.dumps(payload, indent=indent))
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
            performance_output = args.performance_output or _derive_performance_path(args.output)
            write_performance_summary(report["performance_summary"], performance_output)
        elif args.performance_output:
            write_performance_summary(report["performance_summary"], args.performance_output)
        indent = 2 if args.pretty else None
        print(json.dumps(report, indent=indent))
        return 0

    if args.command == "generate-complexity-benchmark":
        dataset = generate_complexity_dataset(
            levels=args.levels,
            scenarios_per_level=args.scenarios_per_level,
            followups=args.followups,
            seed=args.seed,
        )
        write_complexity_dataset(dataset, args.output)
        indent = 2 if args.pretty else None
        print(json.dumps(dataset, indent=indent))
        return 0

    if args.command == "evaluate-complexity-sweep":
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
        summary = summarize_complexity_report(report)
        if args.output:
            write_report(report, args.output)
            performance_output = args.performance_output or _derive_performance_path(args.output)
            write_performance_summary(report["performance_summary"], performance_output)
            summary_output = args.summary_output or _derive_summary_path(args.output)
            write_complexity_summary(summary, summary_output)
            markdown_output = args.markdown_output or _derive_markdown_path(args.output)
            charts_dir = args.charts_dir or _derive_charts_dir(args.output)
            write_complexity_report_bundle(
                performance_summary=report["performance_summary"],
                sweep_summary=summary,
                markdown_path=markdown_output,
                charts_dir=charts_dir,
            )
        elif args.performance_output:
            write_performance_summary(report["performance_summary"], args.performance_output)
            if args.markdown_output:
                write_complexity_report_bundle(
                    performance_summary=report["performance_summary"],
                    sweep_summary=summary,
                    markdown_path=args.markdown_output,
                    charts_dir=args.charts_dir or _derive_charts_dir(args.markdown_output),
                )
        elif args.summary_output:
            write_complexity_summary(summary, args.summary_output)
            if args.markdown_output:
                write_complexity_report_bundle(
                    performance_summary=report["performance_summary"],
                    sweep_summary=summary,
                    markdown_path=args.markdown_output,
                    charts_dir=args.charts_dir or _derive_charts_dir(args.markdown_output),
                )
        elif args.markdown_output:
            write_complexity_report_bundle(
                performance_summary=report["performance_summary"],
                sweep_summary=summary,
                markdown_path=args.markdown_output,
                charts_dir=args.charts_dir or _derive_charts_dir(args.markdown_output),
            )
        indent = 2 if args.pretty else None
        print(json.dumps(summary, indent=indent))
        return 0

    if args.command == "evaluate-v2":
        try:
            report = evaluate_v2_comparison(
                args.dataset,
                provider_name=args.provider,
                model=args.model,
            )
        except ProviderError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if args.output:
            write_v2_report(report, args.output)
            write_v2_report_bundle(
                report=report,
                markdown_path=args.markdown_output or _derive_markdown_path(args.output),
                charts_dir=args.charts_dir or _derive_charts_dir(args.output),
            )
        elif args.markdown_output:
            write_v2_report_bundle(
                report=report,
                markdown_path=args.markdown_output,
                charts_dir=args.charts_dir or _derive_charts_dir(args.markdown_output),
            )
        indent = 2 if args.pretty else None
        print(json.dumps(report, indent=indent))
        return 0

    if args.command == "render-v2-report":
        with Path(args.report).open("r", encoding="utf-8") as handle:
            report = json.load(handle)
        bundle = write_v2_report_bundle(
            report=report,
            markdown_path=args.markdown_output or _derive_markdown_path(args.report),
            charts_dir=args.charts_dir or _derive_charts_dir(args.report),
        )
        indent = 2 if args.pretty else None
        print(json.dumps(bundle, indent=indent))
        return 0

    return 1


def _derive_performance_path(output_path: str) -> str:
    path = Path(output_path)
    suffix = path.suffix or ".json"
    return str(path.with_name(f"{path.stem}.performance{suffix}"))


def _derive_summary_path(output_path: str) -> str:
    path = Path(output_path)
    suffix = path.suffix or ".json"
    return str(path.with_name(f"{path.stem}.sweep{suffix}"))


def _derive_markdown_path(output_path: str) -> str:
    path = Path(output_path)
    return str(path.with_name(f"{path.stem}.report.md"))


def _derive_charts_dir(output_path: str) -> str:
    path = Path(output_path)
    return str(path.with_name(f"{path.stem}.charts"))
