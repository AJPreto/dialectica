"""Command-line interface for Dialectica."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ._io import load_json, write_json
from .answer_eval import evaluate_answer_dataset
from .api import run_server
from .canonical import serialize_logical_form
from .compiler import SUPPORTED_EXPORT_TARGETS
from .complexity import generate_complexity_dataset, summarize_complexity_report
from .evaluate import evaluate_dataset
from .fingerprint import compare_fingerprints, fingerprint_logical_form, summarize_fingerprint
from .parser import parse
from .pipeline import reason
from .providers import ProviderError
from .reasoning_eval import evaluate_reasoning_comparison
from .reporting import write_complexity_report_bundle, write_reasoning_report_bundle
from .validation import validate_logical_form

PROVIDERS = ("oracle", "openai", "ollama")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (ProviderError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dialectica", description="Dialectica logical-form tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def command(name: str, handler, help_text: str, *, pretty: str = "Pretty-print JSON output") -> argparse.ArgumentParser:
        sub = subparsers.add_parser(name, help=help_text)
        sub.set_defaults(handler=handler)
        if pretty:
            sub.add_argument("--pretty", action="store_true", help=pretty)
        return sub

    sub = command("parse", _cmd_parse, "Parse text into a logical form")
    _add_text_arguments(sub, "Text to parse")
    sub.add_argument("--canonical", action="store_true", help="Print canonical serialization instead of JSON")

    sub = command("fingerprint", _cmd_fingerprint, "Build a structural fingerprint from text")
    _add_text_arguments(sub, "Text to fingerprint")
    sub.add_argument("--summary", action="store_true", help="Print a concise fingerprint summary")

    sub = command("compare-fingerprints", _cmd_compare_fingerprints, "Compare structural fingerprints for two texts")
    sub.add_argument("left", help="First text input")
    sub.add_argument("right", help="Second text input")
    sub.add_argument("--language", default="en")
    sub.add_argument("--document", action="store_true", help="Parse inputs as multi-sentence documents")

    sub = command("reason", _cmd_reason, "Run the neuro-symbolic reasoning pipeline")
    sub.add_argument("text", nargs="?", help="Context text. If omitted, stdin is used.")
    sub.add_argument("--query", help="Optional separate query. If omitted, the last question in the text is used.")
    sub.add_argument(
        "--targets",
        default=",".join(SUPPORTED_EXPORT_TARGETS),
        help="Comma-separated export targets to compile, default: horn,fol,smt",
    )
    sub.add_argument(
        "--reasoner",
        default="horn",
        choices=("horn", "fol"),
        help="Reasoning backend to run over the compiled outputs, default: horn",
    )

    sub = command("serve", _cmd_serve, "Run the local HTTP API", pretty="")
    sub.add_argument("--host", default="127.0.0.1")
    sub.add_argument("--port", type=int, default=8000)

    sub = command("evaluate", _cmd_evaluate, "Run the benchmark harness", pretty="Pretty-print the evaluation result")
    sub.add_argument("--dataset", default=str(Path("benchmarks") / "core.json"), help="Path to benchmark dataset JSON")

    sub = command(
        "evaluate-answers",
        _cmd_evaluate_answers,
        "Run end-to-end answer evaluation",
        pretty="Pretty-print the evaluation result",
    )
    sub.add_argument(
        "--dataset",
        default=str(Path("benchmarks") / "objective_qa.sample.json"),
        help="Path to objective QA benchmark dataset JSON",
    )
    _add_provider_arguments(sub, default="oracle", help_text="Model provider used to answer benchmark questions")
    sub.add_argument(
        "--include-gold-dialectica",
        action="store_true",
        help="Also run a Dialectica condition using gold logical forms when present in the dataset",
    )
    sub.add_argument("--output", help="Optional path to write the full JSON report")
    sub.add_argument("--performance-output", help="Optional path to write a compact performance summary JSON file")

    sub = command(
        "generate-complexity-benchmark",
        _cmd_generate_complexity,
        "Generate a synthetic complexity-sweep objective QA benchmark",
        pretty="Pretty-print the generated dataset",
    )
    sub.add_argument("--levels", type=int, default=6, help="Number of difficulty levels to generate")
    sub.add_argument("--scenarios-per-level", type=int, default=3, help="Number of scenarios to generate at each level")
    sub.add_argument("--followups", type=int, default=3, help="Number of follow-up questions to derive from each scenario")
    sub.add_argument("--seed", type=int, default=7, help="Deterministic random seed")
    sub.add_argument(
        "--output",
        default=str(Path("benchmarks") / "complexity_sweep.generated.json"),
        help="Path to write the generated benchmark dataset",
    )

    sub = command(
        "evaluate-complexity-sweep",
        _cmd_evaluate_complexity,
        "Run answer evaluation and summarize results by complexity level",
        pretty="Pretty-print the complexity summary",
    )
    sub.add_argument(
        "--dataset",
        default=str(Path("benchmarks") / "complexity_sweep.generated.json"),
        help="Path to a generated complexity-sweep benchmark dataset JSON file",
    )
    _add_provider_arguments(sub, default="oracle", help_text="Model provider used to answer benchmark questions")
    sub.add_argument(
        "--include-gold-dialectica",
        action="store_true",
        help="Also run Dialectica conditions using gold logical forms when present in the dataset",
    )
    sub.add_argument("--output", help="Optional path to write the full JSON report")
    sub.add_argument("--performance-output", help="Optional path to write a compact performance summary JSON file")
    sub.add_argument("--summary-output", help="Optional path to write the level-by-level complexity summary JSON file")
    sub.add_argument("--markdown-output", help="Optional path to write a markdown report that embeds generated charts")
    sub.add_argument("--charts-dir", help="Optional directory to write SVG charts for the markdown report")

    sub = command(
        "evaluate-reasoning",
        _cmd_evaluate_reasoning,
        "Compare direct prompting, encoded prompting, and symbolic reasoning backends",
        pretty="Pretty-print the comparison report",
    )
    sub.add_argument(
        "--dataset",
        default=str(Path("benchmarks") / "reasoning.messy.json"),
        help="Path to a reasoning comparison benchmark JSON file",
    )
    _add_provider_arguments(sub, default="ollama", help_text="Model provider used for the direct and encoded baselines")
    sub.add_argument("--output", help="Optional path to write the full JSON comparison report")
    sub.add_argument("--markdown-output", help="Optional path to write a markdown reasoning report")
    sub.add_argument("--charts-dir", help="Optional directory to write SVG charts for the reasoning report")

    sub = command(
        "render-reasoning-report",
        _cmd_render_reasoning,
        "Render charts and a markdown summary from an existing reasoning comparison JSON report",
        pretty="Pretty-print the render manifest",
    )
    sub.add_argument("--report", required=True, help="Path to an existing reasoning comparison JSON report")
    sub.add_argument("--markdown-output", help="Optional markdown output path")
    sub.add_argument("--charts-dir", help="Optional charts output directory")

    return parser


def _add_text_arguments(command_parser: argparse.ArgumentParser, help_text: str) -> None:
    command_parser.add_argument("text", nargs="?", help=f"{help_text}. If omitted, stdin is used.")
    command_parser.add_argument("--language", default="en")
    command_parser.add_argument("--document", action="store_true", help="Parse input as a multi-sentence document")


def _add_provider_arguments(command_parser: argparse.ArgumentParser, *, default: str, help_text: str) -> None:
    command_parser.add_argument("--provider", default=default, choices=PROVIDERS, help=help_text)
    command_parser.add_argument("--model", help="Model name for the selected provider")


def _cmd_parse(args: argparse.Namespace) -> int:
    logical_form = parse(_read_text(args), language=args.language, document=args.document)
    if args.canonical:
        print(serialize_logical_form(logical_form))
        return 0
    _print_json({"logical_form": logical_form, "validation_errors": validate_logical_form(logical_form)}, args)
    return 0


def _cmd_fingerprint(args: argparse.Namespace) -> int:
    fingerprint = fingerprint_logical_form(parse(_read_text(args), language=args.language, document=args.document))
    _print_json(summarize_fingerprint(fingerprint) if args.summary else fingerprint, args)
    return 0


def _cmd_compare_fingerprints(args: argparse.Namespace) -> int:
    left, right = (
        fingerprint_logical_form(parse(text, language=args.language, document=args.document))
        for text in (args.left, args.right)
    )
    _print_json(compare_fingerprints(left, right), args)
    return 0


def _cmd_reason(args: argparse.Namespace) -> int:
    targets = tuple(part.strip() for part in args.targets.split(",") if part.strip())
    unsupported = [target for target in targets if target not in SUPPORTED_EXPORT_TARGETS]
    if unsupported:
        raise ValueError(
            f"Unsupported export target(s): {', '.join(unsupported)}. "
            f"Supported targets: {', '.join(SUPPORTED_EXPORT_TARGETS)}."
        )
    run = reason(_read_text(args), query=args.query, reasoner=args.reasoner, targets=targets)
    _print_json(run.to_dict(), args)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    run_server(host=args.host, port=args.port)
    return 0


def _cmd_evaluate(args: argparse.Namespace) -> int:
    _print_json(evaluate_dataset(args.dataset), args)
    return 0


def _cmd_evaluate_answers(args: argparse.Namespace) -> int:
    report = _run_answer_evaluation(args)
    if args.output:
        write_json(report, args.output)
    performance_output = args.performance_output or _derived_path(args.output, ".performance")
    if performance_output:
        write_json(report["performance_summary"], performance_output)
    _print_json(report, args)
    return 0


def _cmd_generate_complexity(args: argparse.Namespace) -> int:
    dataset = generate_complexity_dataset(
        levels=args.levels,
        scenarios_per_level=args.scenarios_per_level,
        followups=args.followups,
        seed=args.seed,
    )
    write_json(dataset, args.output)
    _print_json(dataset, args)
    return 0


def _cmd_evaluate_complexity(args: argparse.Namespace) -> int:
    report = _run_answer_evaluation(args)
    summary = summarize_complexity_report(report)
    # Explicit paths always win; --output additionally derives every sibling artifact.
    if args.output:
        write_json(report, args.output)
    performance_output = args.performance_output or _derived_path(args.output, ".performance")
    if performance_output:
        write_json(report["performance_summary"], performance_output)
    summary_output = args.summary_output or _derived_path(args.output, ".sweep")
    if summary_output:
        write_json(summary, summary_output)
    markdown_output = args.markdown_output or _derived_path(args.output, ".report", suffix=".md")
    if markdown_output:
        write_complexity_report_bundle(
            performance_summary=report["performance_summary"],
            sweep_summary=summary,
            markdown_path=markdown_output,
            charts_dir=args.charts_dir or _derived_path(args.output or markdown_output, ".charts", suffix=""),
        )
    _print_json(summary, args)
    return 0


def _cmd_evaluate_reasoning(args: argparse.Namespace) -> int:
    report = evaluate_reasoning_comparison(args.dataset, provider_name=args.provider, model=args.model)
    if args.output:
        write_json(report, args.output)
    markdown_output = args.markdown_output or _derived_path(args.output, ".report", suffix=".md")
    if markdown_output:
        write_reasoning_report_bundle(
            report=report,
            markdown_path=markdown_output,
            charts_dir=args.charts_dir or _derived_path(args.output or markdown_output, ".charts", suffix=""),
        )
    _print_json(report, args)
    return 0


def _cmd_render_reasoning(args: argparse.Namespace) -> int:
    bundle = write_reasoning_report_bundle(
        report=load_json(args.report),
        markdown_path=args.markdown_output or _derived_path(args.report, ".report", suffix=".md"),
        charts_dir=args.charts_dir or _derived_path(args.report, ".charts", suffix=""),
    )
    _print_json(bundle, args)
    return 0


def _run_answer_evaluation(args: argparse.Namespace) -> dict[str, Any]:
    return evaluate_answer_dataset(
        args.dataset,
        provider_name=args.provider,
        model=args.model,
        include_gold_dialectica=args.include_gold_dialectica,
    )


def _read_text(args: argparse.Namespace) -> str:
    return args.text if args.text is not None else sys.stdin.read().strip()


def _print_json(payload: Any, args: argparse.Namespace) -> None:
    print(json.dumps(payload, indent=2 if args.pretty else None))


def _derived_path(base: str | None, tag: str, *, suffix: str | None = None) -> str | None:
    """Return a sibling path such as ``out.performance.json`` for ``out.json``; ``None`` without a base."""
    if not base:
        return None
    path = Path(base)
    if suffix is None:
        suffix = path.suffix or ".json"
    return str(path.with_name(f"{path.stem}{tag}{suffix}"))
