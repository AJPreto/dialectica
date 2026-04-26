"""Markdown and SVG reporting helpers for Dialectica benchmark runs."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


PREFERRED_CONDITION_ORDER = [
    "direct",
    "dialectica_compact",
    "dialectica_filtered",
    "dialectica_structural_compact",
    "dialectica_filtered_structural",
    "horn_reasoner",
    "fol_reasoner",
]

DISPLAY_LABELS = {
    "direct": "Direct",
    "dialectica_compact": "Compact",
    "dialectica_filtered": "Filtered",
    "dialectica_structural_compact": "Structural Compact",
    "dialectica_filtered_structural": "Filtered Structural",
    "horn_reasoner": "Horn Reasoner",
    "fol_reasoner": "FOL Reasoner",
    "dialectica_gold_compact": "Gold Compact",
    "dialectica_gold_filtered": "Gold Filtered",
    "dialectica_gold_structural_compact": "Gold Structural Compact",
    "dialectica_gold_filtered_structural": "Gold Filtered Structural",
}

COLORS = [
    "#1f4e79",
    "#2a7f62",
    "#b45f06",
    "#c27ba0",
    "#6a329f",
    "#45818e",
    "#bf9000",
    "#cc4125",
]


def write_complexity_report_bundle(
    *,
    performance_summary: dict[str, Any],
    sweep_summary: dict[str, Any],
    markdown_path: str | Path,
    charts_dir: str | Path,
) -> dict[str, str]:
    markdown_destination = Path(markdown_path)
    charts_destination = Path(charts_dir)
    markdown_destination.parent.mkdir(parents=True, exist_ok=True)
    charts_destination.mkdir(parents=True, exist_ok=True)

    conditions = _ordered_conditions(performance_summary.get("aggregate", {}))

    accuracy_chart = charts_destination / "accuracy.svg"
    token_chart = charts_destination / "total_tokens.svg"
    latency_chart = charts_destination / "latency.svg"
    iteration_chart = charts_destination / "iterations.svg"
    token_trend_chart = charts_destination / "tokens_vs_context_size.svg"

    accuracy_values = [
        float(performance_summary["aggregate"].get(condition, {}).get("accuracy", 0.0) or 0.0)
        for condition in conditions
    ]
    token_values = [
        float(performance_summary["aggregate"].get(condition, {}).get("average_total_tokens", 0.0) or 0.0)
        for condition in conditions
    ]
    latency_values = [
        float(performance_summary["aggregate"].get(condition, {}).get("average_latency_seconds", 0.0) or 0.0)
        for condition in conditions
    ]
    iteration_values = [
        float(performance_summary["aggregate"].get(condition, {}).get("average_iterations", 0.0) or 0.0)
        for condition in conditions
    ]

    accuracy_chart.write_text(
        _bar_chart_svg(
            title="Accuracy by Condition",
            labels=[_display_label(condition) for condition in conditions],
            values=accuracy_values,
            y_label="Accuracy",
            percent=True,
        ),
        encoding="utf-8",
    )
    token_chart.write_text(
        _bar_chart_svg(
            title="Average Total Tokens by Condition",
            labels=[_display_label(condition) for condition in conditions],
            values=token_values,
            y_label="Average total tokens",
        ),
        encoding="utf-8",
    )
    latency_chart.write_text(
        _bar_chart_svg(
            title="Average Latency by Condition",
            labels=[_display_label(condition) for condition in conditions],
            values=latency_values,
            y_label="Seconds",
        ),
        encoding="utf-8",
    )
    iteration_chart.write_text(
        _bar_chart_svg(
            title="Average Iterations by Condition",
            labels=[_display_label(condition) for condition in conditions],
            values=iteration_values,
            y_label="Iterations",
        ),
        encoding="utf-8",
    )
    token_trend_chart.write_text(
        _line_chart_svg(
            title="Context Size vs Average Total Tokens",
            x_label="Average raw context characters",
            y_label="Average total tokens",
            series=_build_token_trend_series(sweep_summary),
        ),
        encoding="utf-8",
    )

    markdown_destination.write_text(
        _complexity_markdown(
            performance_summary=performance_summary,
            sweep_summary=sweep_summary,
            charts_dir=charts_destination,
            markdown_path=markdown_destination,
            chart_paths={
                "accuracy": accuracy_chart,
                "tokens": token_chart,
                "latency": latency_chart,
                "iterations": iteration_chart,
                "trend": token_trend_chart,
            },
        ),
        encoding="utf-8",
    )

    return {
        "markdown": str(markdown_destination),
        "accuracy_chart": str(accuracy_chart),
        "token_chart": str(token_chart),
        "latency_chart": str(latency_chart),
        "iteration_chart": str(iteration_chart),
        "token_trend_chart": str(token_trend_chart),
    }


def write_reasoning_report_bundle(
    *,
    report: dict[str, Any],
    markdown_path: str | Path,
    charts_dir: str | Path,
) -> dict[str, str]:
    markdown_destination = Path(markdown_path)
    charts_destination = Path(charts_dir)
    markdown_destination.parent.mkdir(parents=True, exist_ok=True)
    charts_destination.mkdir(parents=True, exist_ok=True)

    conditions = _ordered_conditions(report.get("aggregate", {}))
    accuracy_chart = charts_destination / "accuracy.svg"
    token_chart = charts_destination / "total_tokens.svg"
    latency_chart = charts_destination / "latency.svg"
    correctness_chart = charts_destination / "correctness_by_case.svg"
    token_trend_chart = charts_destination / "tokens_vs_context_size.svg"
    category_chart = charts_destination / "category_accuracy.svg"
    difficulty_chart = charts_destination / "difficulty_accuracy.svg"

    accuracy_values = [
        float(report.get("aggregate", {}).get(condition, {}).get("accuracy", 0.0) or 0.0)
        for condition in conditions
    ]
    token_values = [
        float(report.get("aggregate", {}).get(condition, {}).get("average_total_tokens", 0.0) or 0.0)
        for condition in conditions
    ]
    latency_values = [
        float(report.get("aggregate", {}).get(condition, {}).get("average_latency_seconds", 0.0) or 0.0)
        for condition in conditions
    ]

    accuracy_chart.write_text(
        _bar_chart_svg(
            title="Reasoning Comparison Accuracy",
            labels=[_display_label(condition) for condition in conditions],
            values=accuracy_values,
            y_label="Accuracy",
            percent=True,
        ),
        encoding="utf-8",
    )
    token_chart.write_text(
        _bar_chart_svg(
            title="Reasoning Comparison Average Total Tokens",
            labels=[_display_label(condition) for condition in conditions],
            values=token_values,
            y_label="Average total tokens",
        ),
        encoding="utf-8",
    )
    latency_chart.write_text(
        _bar_chart_svg(
            title="Reasoning Comparison Average Latency",
            labels=[_display_label(condition) for condition in conditions],
            values=latency_values,
            y_label="Seconds",
        ),
        encoding="utf-8",
    )
    correctness_chart.write_text(
        _line_chart_svg(
            title="Correctness by Case",
            x_label="Case index",
            y_label="Correct (1=yes, 0=no)",
            series=_build_reasoning_correctness_series(report, conditions),
        ),
        encoding="utf-8",
    )
    token_trend_chart.write_text(
        _line_chart_svg(
            title="Context Size vs Total Tokens",
            x_label="Context characters",
            y_label="Total tokens",
            series=_build_reasoning_token_series(report, conditions),
        ),
        encoding="utf-8",
    )
    category_chart.write_text(
        _grouped_bar_chart_svg(
            title="Category Accuracy by Mode",
            group_labels=list(report.get("category_summary", {}).keys()),
            series=_build_grouped_accuracy_series(report.get("category_summary", {}), conditions),
            y_label="Accuracy",
            percent=True,
        ),
        encoding="utf-8",
    )
    difficulty_chart.write_text(
        _grouped_bar_chart_svg(
            title="Difficulty Accuracy by Mode",
            group_labels=list(report.get("difficulty_summary", {}).keys()),
            series=_build_grouped_accuracy_series(report.get("difficulty_summary", {}), conditions),
            y_label="Accuracy",
            percent=True,
        ),
        encoding="utf-8",
    )

    markdown_destination.write_text(
        _reasoning_markdown(
            report=report,
            markdown_path=markdown_destination,
            chart_paths={
                "accuracy": accuracy_chart,
                "tokens": token_chart,
                "latency": latency_chart,
                "correctness": correctness_chart,
                "trend": token_trend_chart,
                "category": category_chart,
                "difficulty": difficulty_chart,
            },
            conditions=conditions,
        ),
        encoding="utf-8",
    )

    return {
        "markdown": str(markdown_destination),
        "accuracy_chart": str(accuracy_chart),
        "token_chart": str(token_chart),
        "latency_chart": str(latency_chart),
        "correctness_chart": str(correctness_chart),
        "token_trend_chart": str(token_trend_chart),
        "category_chart": str(category_chart),
        "difficulty_chart": str(difficulty_chart),
    }


def _ordered_conditions(aggregate: dict[str, Any]) -> list[str]:
    keys = [key for key in aggregate if not key.startswith("dialectica_gold")]
    ordered = [key for key in PREFERRED_CONDITION_ORDER if key in keys]
    remainder = sorted(key for key in keys if key not in ordered)
    return [*ordered, *remainder]


def _build_token_trend_series(sweep_summary: dict[str, Any]) -> list[dict[str, Any]]:
    levels = sweep_summary.get("levels", {})
    condition_names: list[str] = []
    for level_data in levels.values():
        for condition_name in level_data.get("conditions", {}):
            if condition_name.startswith("dialectica_gold"):
                continue
            if condition_name not in condition_names:
                condition_names.append(condition_name)
    ordered_names = [name for name in PREFERRED_CONDITION_ORDER if name in condition_names]
    ordered_names.extend(name for name in condition_names if name not in ordered_names)

    series: list[dict[str, Any]] = []
    for index, condition_name in enumerate(ordered_names):
        points: list[tuple[float, float]] = []
        for level_key in sorted(levels, key=lambda value: int(value)):
            level_data = levels[level_key]
            raw_size = float(level_data.get("average_context_characters", 0.0) or 0.0)
            total_tokens = float(
                level_data.get("conditions", {}).get(condition_name, {}).get("average_total_tokens", 0.0) or 0.0
            )
            points.append((raw_size, total_tokens))
        series.append(
            {
                "label": _display_label(condition_name),
                "color": COLORS[index % len(COLORS)],
                "points": points,
            }
        )
    return series


def _build_reasoning_correctness_series(report: dict[str, Any], conditions: list[str]) -> list[dict[str, Any]]:
    cases = report.get("cases", [])
    series: list[dict[str, Any]] = []
    for index, condition in enumerate(conditions):
        points: list[tuple[float, float]] = []
        for case_index, case in enumerate(cases, start=1):
            condition_map = {item["name"]: item for item in case.get("conditions", [])}
            current = condition_map.get(condition, {})
            points.append((float(case_index), 1.0 if current.get("correct") else 0.0))
        series.append(
            {
                "label": _display_label(condition),
                "color": COLORS[index % len(COLORS)],
                "points": points,
            }
        )
    return series


def _build_reasoning_token_series(report: dict[str, Any], conditions: list[str]) -> list[dict[str, Any]]:
    cases = report.get("cases", [])
    series: list[dict[str, Any]] = []
    for index, condition in enumerate(conditions):
        points: list[tuple[float, float]] = []
        for case in cases:
            condition_map = {item["name"]: item for item in case.get("conditions", [])}
            current = condition_map.get(condition, {})
            points.append(
                (
                    float(len(str(case.get("context", "")))),
                    float(current.get("token_counts", {}).get("total_tokens", 0) or 0),
                )
            )
        points.sort(key=lambda item: item[0])
        series.append(
            {
                "label": _display_label(condition),
                "color": COLORS[index % len(COLORS)],
                "points": points,
            }
        )
    return series


def _build_grouped_accuracy_series(summary: dict[str, Any], conditions: list[str]) -> list[dict[str, Any]]:
    series: list[dict[str, Any]] = []
    for index, condition in enumerate(conditions):
        values: list[float] = []
        for group_data in summary.values():
            values.append(float(group_data.get("modes", {}).get(condition, {}).get("accuracy", 0.0) or 0.0))
        series.append(
            {
                "label": _display_label(condition),
                "color": COLORS[index % len(COLORS)],
                "values": values,
            }
        )
    return series


def _complexity_markdown(
    *,
    performance_summary: dict[str, Any],
    sweep_summary: dict[str, Any],
    charts_dir: Path,
    markdown_path: Path,
    chart_paths: dict[str, Path],
) -> str:
    relative_chart = {name: path.relative_to(markdown_path.parent).as_posix() for name, path in chart_paths.items()}
    provider = performance_summary.get("provider")
    model = performance_summary.get("model")
    dataset_path = performance_summary.get("dataset_path")
    representation_levels = sweep_summary.get("candidate_representation_crossover_levels", [])
    prompt_levels = sweep_summary.get("candidate_prompt_inflection_levels", {})

    lines = [
        "# Complexity Sweep Report",
        "",
        f"- Dataset: `{dataset_path}`",
        f"- Provider: `{provider}`",
        f"- Model: `{model}`",
        f"- Representation crossover levels: `{representation_levels}`",
        f"- Prompt inflection levels: `{prompt_levels}`",
        "",
        "## Charts",
        "",
        "### Accuracy by condition",
        f"![Accuracy chart]({relative_chart['accuracy']})",
        "",
        "### Average total tokens by condition",
        f"![Token chart]({relative_chart['tokens']})",
        "",
        "### Average latency by condition",
        f"![Latency chart]({relative_chart['latency']})",
        "",
        "### Average iterations by condition",
        f"![Iteration chart]({relative_chart['iterations']})",
        "",
        "### Context size vs average total tokens",
        f"![Token trend chart]({relative_chart['trend']})",
        "",
        "## Level Summary",
        "",
        "| Level | Raw chars | Compact chars | Direct acc | Compact acc | Filtered acc | Direct tokens | Filtered tokens | Crossover |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    for level_key in sorted(sweep_summary.get("levels", {}), key=lambda value: int(value)):
        level_data = sweep_summary["levels"][level_key]
        conditions = level_data.get("conditions", {})
        lines.append(
            "| {level} | {raw:.0f} | {compact:.0f} | {direct:.3f} | {compact_acc:.3f} | {filtered:.3f} | {direct_tokens:.1f} | {filtered_tokens:.1f} | {crossover:.3f} |".format(
                level=level_key,
                raw=float(level_data.get("average_context_characters", 0.0) or 0.0),
                compact=float(level_data.get("average_compact_characters", 0.0) or 0.0),
                direct=float(conditions.get("direct", {}).get("accuracy", 0.0) or 0.0),
                compact_acc=float(conditions.get("dialectica_compact", {}).get("accuracy", 0.0) or 0.0),
                filtered=float(conditions.get("dialectica_filtered", {}).get("accuracy", 0.0) or 0.0),
                direct_tokens=float(conditions.get("direct", {}).get("average_total_tokens", 0.0) or 0.0),
                filtered_tokens=float(conditions.get("dialectica_filtered", {}).get("average_total_tokens", 0.0) or 0.0),
                crossover=float(level_data.get("compact_context_smaller_than_raw_share", 0.0) or 0.0),
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `compact chars` asks whether the encoded representation itself is smaller than the raw context.",
            "- `filtered acc` measures the new question-conditioned filtered-only path.",
            "- The token trend chart is the easiest place to inspect whether any condition becomes more efficient as the context window grows.",
            "",
        ]
    )

    return "\n".join(lines)


def _reasoning_markdown(
    *,
    report: dict[str, Any],
    markdown_path: Path,
    chart_paths: dict[str, Path],
    conditions: list[str],
) -> str:
    relative_chart = {name: path.relative_to(markdown_path.parent).as_posix() for name, path in chart_paths.items()}
    comparison_table = report.get("comparison_table", [])
    diagnostics = report.get("diagnostics", {})
    category_summary = report.get("category_summary", {})
    difficulty_summary = report.get("difficulty_summary", {})
    error_report = report.get("error_report", [])
    lines = [
        "# Reasoning Comparison Report",
        "",
        f"- Dataset: `{report.get('dataset_path')}`",
        f"- Provider: `{report.get('provider')}`",
        f"- Model: `{report.get('model')}`",
        f"- Cases: `{len(report.get('cases', []))}`",
        "",
        "## Charts",
        "",
        "### Accuracy",
        f"![Accuracy chart]({relative_chart['accuracy']})",
        "",
        "### Average total tokens",
        f"![Token chart]({relative_chart['tokens']})",
        "",
        "### Average latency",
        f"![Latency chart]({relative_chart['latency']})",
        "",
        "### Correctness by case",
        f"![Correctness chart]({relative_chart['correctness']})",
        "",
        "### Context size vs total tokens",
        f"![Token trend chart]({relative_chart['trend']})",
        "",
        "### Category accuracy",
        f"![Category accuracy chart]({relative_chart['category']})",
        "",
        "### Difficulty accuracy",
        f"![Difficulty accuracy chart]({relative_chart['difficulty']})",
        "",
        "## Comparison Table",
        "",
        "| Condition | Accuracy | Avg tokens | Avg latency (s) | Negation | Exceptions | Contradictions | Paraphrase stability | Avg depth solved |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    if comparison_table:
        for row in comparison_table:
            lines.append(
                "| {label} | {accuracy:.3f} | {tokens:.1f} | {latency:.3f} | {negation:.3f} | {exceptions:.3f} | {contradictions:.3f} | {paraphrase:.3f} | {depth:.2f} |".format(
                    label=_markdown_cell(row.get("label", row.get("mode", ""))),
                    accuracy=float(row.get("accuracy", 0.0) or 0.0),
                    tokens=float(row.get("average_total_tokens", 0.0) or 0.0),
                    latency=float(row.get("average_latency_seconds", 0.0) or 0.0),
                    negation=float(row.get("negation_score", 0.0) or 0.0),
                    exceptions=float(row.get("exception_score", 0.0) or 0.0),
                    contradictions=float(row.get("contradiction_score", 0.0) or 0.0),
                    paraphrase=float(row.get("paraphrase_stability", 0.0) or 0.0),
                    depth=float(row.get("average_reasoning_depth_solved", 0.0) or 0.0),
                )
            )
    else:
        aggregate = report.get("aggregate", {})
        for condition in conditions:
            current = aggregate.get(condition, {})
            lines.append(
                "| {label} | {accuracy:.3f} | {tokens:.1f} | {latency:.3f} | 0.000 | 0.000 | 0.000 | 0.000 | 0.00 |".format(
                    label=_markdown_cell(_display_label(condition)),
                    accuracy=float(current.get("accuracy", 0.0) or 0.0),
                    tokens=float(current.get("average_total_tokens", 0.0) or 0.0),
                    latency=float(current.get("average_latency_seconds", 0.0) or 0.0),
                )
            )

    lines.extend(
        [
            "",
            "## Key Diagnostics",
            "",
            "- Horn contradiction-flag match rate: `{:.3f}`".format(
                float(diagnostics.get("contradiction_sensitivity", {}).get("horn_reasoner_flag_match_rate", 0.0) or 0.0)
            ),
            "- Horn explanation faithfulness proxy: `{:.3f}`".format(
                float(diagnostics.get("explanation_faithfulness_proxy", {}).get("horn_reasoner", {}).get("pass_rate", 0.0) or 0.0)
            ),
            "- Horn export expectation match rate: `{:.3f}`".format(
                float(diagnostics.get("export_success_rate", {}).get("by_target", {}).get("horn", {}).get("expectation_match_rate", 0.0) or 0.0)
            ),
            "",
            "## Category Summary",
            "",
            "| Category | Cases | Direct | Compact | Filtered | Filtered Structural | Horn Reasoner | FOL Reasoner |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for category, payload in category_summary.items():
        lines.append(
            "| {category} | {cases} | {direct:.3f} | {compact:.3f} | {filtered:.3f} | {filtered_struct:.3f} | {horn_reasoner:.3f} | {fol_reasoner:.3f} |".format(
                category=_markdown_cell(category),
                cases=int(payload.get("case_count", 0) or 0),
                direct=float(payload.get("modes", {}).get("direct", {}).get("accuracy", 0.0) or 0.0),
                compact=float(payload.get("modes", {}).get("dialectica_compact", {}).get("accuracy", 0.0) or 0.0),
                filtered=float(payload.get("modes", {}).get("dialectica_filtered", {}).get("accuracy", 0.0) or 0.0),
                filtered_struct=float(payload.get("modes", {}).get("dialectica_filtered_structural", {}).get("accuracy", 0.0) or 0.0),
                horn_reasoner=float(payload.get("modes", {}).get("horn_reasoner", {}).get("accuracy", 0.0) or 0.0),
                fol_reasoner=float(payload.get("modes", {}).get("fol_reasoner", {}).get("accuracy", 0.0) or 0.0),
            )
        )

    lines.extend(
        [
            "",
            "## Difficulty Summary",
            "",
            "| Difficulty | Cases | Direct | Compact | Filtered | Filtered Structural | Horn Reasoner | FOL Reasoner |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for difficulty, payload in difficulty_summary.items():
        lines.append(
            "| {difficulty} | {cases} | {direct:.3f} | {compact:.3f} | {filtered:.3f} | {filtered_struct:.3f} | {horn_reasoner:.3f} | {fol_reasoner:.3f} |".format(
                difficulty=_markdown_cell(difficulty),
                cases=int(payload.get("case_count", 0) or 0),
                direct=float(payload.get("modes", {}).get("direct", {}).get("accuracy", 0.0) or 0.0),
                compact=float(payload.get("modes", {}).get("dialectica_compact", {}).get("accuracy", 0.0) or 0.0),
                filtered=float(payload.get("modes", {}).get("dialectica_filtered", {}).get("accuracy", 0.0) or 0.0),
                filtered_struct=float(payload.get("modes", {}).get("dialectica_filtered_structural", {}).get("accuracy", 0.0) or 0.0),
                horn_reasoner=float(payload.get("modes", {}).get("horn_reasoner", {}).get("accuracy", 0.0) or 0.0),
                fol_reasoner=float(payload.get("modes", {}).get("fol_reasoner", {}).get("accuracy", 0.0) or 0.0),
            )
        )

    lines.extend(
        [
            "",
            "## Error Report",
            "",
            "| Case | Mode | Category | Predicted | Gold | Expected failure mode |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for entry in error_report[:30]:
        lines.append(
            "| {case_id} | {mode} | {category} | {predicted} | {gold} | {failure} |".format(
                case_id=_markdown_cell(entry.get("case_id", "")),
                mode=_markdown_cell(_display_label(str(entry.get("mode", "")))),
                category=_markdown_cell(entry.get("category", "")),
                predicted=_markdown_cell(entry.get("predicted", "")),
                gold=_markdown_cell(entry.get("gold", "")),
                failure=_markdown_cell(entry.get("expected_failure_mode", "") or ""),
            )
        )

    return "\n".join(lines)


def _bar_chart_svg(*, title: str, labels: list[str], values: list[float], y_label: str, percent: bool = False) -> str:
    width = 960
    height = 540
    margin_left = 90
    margin_right = 40
    margin_top = 60
    margin_bottom = 150
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    max_value = max(values, default=0.0)
    scale_max = max_value if max_value > 0 else 1.0
    if percent:
        scale_max = max(scale_max, 1.0)

    bar_count = max(len(values), 1)
    slot_width = plot_width / bar_count
    bar_width = slot_width * 0.7
    y_ticks = 5

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fffdf8" />',
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-family="Segoe UI, sans-serif" fill="#1f1f1f">{_svg_text(title)}</text>',
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<text x="20" y="{margin_top + plot_height / 2}" transform="rotate(-90 20 {margin_top + plot_height / 2})" text-anchor="middle" font-size="14" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(y_label)}</text>',
    ]

    for tick_index in range(y_ticks + 1):
        value = scale_max * tick_index / y_ticks
        y = height - margin_bottom - (plot_height * tick_index / y_ticks)
        label = f"{value:.2f}" if percent or scale_max < 10 else f"{value:.0f}"
        parts.append(f'<line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" stroke="#e6e0d4" stroke-width="1" />')
        parts.append(
            f'<text x="{margin_left - 10}" y="{y + 5}" text-anchor="end" font-size="12" font-family="Segoe UI, sans-serif" fill="#555">{label}</text>'
        )

    for index, (label, value) in enumerate(zip(labels, values, strict=False)):
        x = margin_left + slot_width * index + (slot_width - bar_width) / 2
        bar_height = 0 if scale_max == 0 else (value / scale_max) * plot_height
        y = height - margin_bottom - bar_height
        color = COLORS[index % len(COLORS)]
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" fill="{color}" rx="4" />')
        value_label = f"{value:.3f}" if percent or value < 10 else f"{value:.1f}"
        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-size="12" font-family="Segoe UI, sans-serif" fill="#333">{value_label}</text>'
        )
        label_x = x + bar_width / 2
        label_y = height - margin_bottom + 24
        parts.append(
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" transform="rotate(35 {label_x:.2f} {label_y:.2f})" text-anchor="start" font-size="12" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(label)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _grouped_bar_chart_svg(
    *,
    title: str,
    group_labels: list[str],
    series: list[dict[str, Any]],
    y_label: str,
    percent: bool = False,
) -> str:
    width = 1200
    height = 620
    margin_left = 90
    margin_right = 60
    margin_top = 60
    margin_bottom = 190
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    all_values = [value for entry in series for value in entry.get("values", [])]
    max_value = max(all_values, default=0.0)
    scale_max = max_value if max_value > 0 else 1.0
    if percent:
        scale_max = max(scale_max, 1.0)

    group_count = max(len(group_labels), 1)
    series_count = max(len(series), 1)
    slot_width = plot_width / group_count
    group_width = slot_width * 0.82
    gap_width = group_width * 0.08
    bar_width = max((group_width - gap_width) / series_count, 8.0)
    y_ticks = 5

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fffdf8" />',
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-family="Segoe UI, sans-serif" fill="#1f1f1f">{_svg_text(title)}</text>',
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<text x="20" y="{margin_top + plot_height / 2}" transform="rotate(-90 20 {margin_top + plot_height / 2})" text-anchor="middle" font-size="14" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(y_label)}</text>',
    ]

    for tick_index in range(y_ticks + 1):
        value = scale_max * tick_index / y_ticks
        y = height - margin_bottom - (plot_height * tick_index / y_ticks)
        label = f"{value:.2f}" if percent or scale_max < 10 else f"{value:.0f}"
        parts.append(f'<line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" stroke="#e6e0d4" stroke-width="1" />')
        parts.append(
            f'<text x="{margin_left - 10}" y="{y + 5}" text-anchor="end" font-size="12" font-family="Segoe UI, sans-serif" fill="#555">{label}</text>'
        )

    for group_index, label in enumerate(group_labels):
        group_x = margin_left + slot_width * group_index + (slot_width - group_width) / 2
        for series_index, entry in enumerate(series):
            values = entry.get("values", [])
            value = float(values[group_index] if group_index < len(values) else 0.0)
            x = group_x + series_index * bar_width
            bar_height = 0 if scale_max == 0 else (value / scale_max) * plot_height
            y = height - margin_bottom - bar_height
            color = entry.get("color", COLORS[series_index % len(COLORS)])
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width - 2:.2f}" height="{bar_height:.2f}" fill="{color}" rx="3" />')
        label_x = group_x + group_width / 2
        label_y = height - margin_bottom + 24
        parts.append(
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" transform="rotate(35 {label_x:.2f} {label_y:.2f})" text-anchor="start" font-size="12" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(label)}</text>'
        )

    legend_x = margin_left
    legend_y = height - 90
    for index, entry in enumerate(series):
        color = entry.get("color", COLORS[index % len(COLORS)])
        x = legend_x + index * 190
        parts.append(f'<rect x="{x}" y="{legend_y - 12}" width="18" height="18" fill="{color}" rx="2" />')
        parts.append(
            f'<text x="{x + 26}" y="{legend_y + 2}" font-size="12" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(entry.get("label", ""))}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _line_chart_svg(*, title: str, x_label: str, y_label: str, series: list[dict[str, Any]]) -> str:
    width = 960
    height = 540
    margin_left = 90
    margin_right = 180
    margin_top = 60
    margin_bottom = 90
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    all_points = [point for entry in series for point in entry.get("points", [])]
    x_values = [point[0] for point in all_points] or [0.0]
    y_values = [point[1] for point in all_points] or [0.0]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = 0.0, max(y_values)
    if x_max == x_min:
        x_max = x_min + 1.0
    if y_max == y_min:
        y_max = y_min + 1.0

    def scale_x(value: float) -> float:
        return margin_left + ((value - x_min) / (x_max - x_min)) * plot_width

    def scale_y(value: float) -> float:
        return height - margin_bottom - ((value - y_min) / (y_max - y_min)) * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fffdf8" />',
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-family="Segoe UI, sans-serif" fill="#1f1f1f">{_svg_text(title)}</text>',
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<text x="{width / 2}" y="{height - 20}" text-anchor="middle" font-size="14" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(x_label)}</text>',
        f'<text x="20" y="{margin_top + plot_height / 2}" transform="rotate(-90 20 {margin_top + plot_height / 2})" text-anchor="middle" font-size="14" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(y_label)}</text>',
    ]

    for tick_index in range(6):
        x_value = x_min + (x_max - x_min) * tick_index / 5
        y_value = y_min + (y_max - y_min) * tick_index / 5
        x = scale_x(x_value)
        y = scale_y(y_value)
        parts.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{height - margin_bottom}" stroke="#efe7da" stroke-width="1" />')
        parts.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{width - margin_right}" y2="{y:.2f}" stroke="#efe7da" stroke-width="1" />')
        parts.append(
            f'<text x="{x:.2f}" y="{height - margin_bottom + 22}" text-anchor="middle" font-size="12" font-family="Segoe UI, sans-serif" fill="#555">{x_value:.0f}</text>'
        )
        parts.append(
            f'<text x="{margin_left - 10}" y="{y + 5:.2f}" text-anchor="end" font-size="12" font-family="Segoe UI, sans-serif" fill="#555">{y_value:.0f}</text>'
        )

    legend_y = margin_top + 20
    for index, entry in enumerate(series):
        points = entry.get("points", [])
        if not points:
            continue
        color = entry.get("color", COLORS[index % len(COLORS)])
        path = " ".join(
            [
                ("M" if point_index == 0 else "L") + f" {scale_x(point[0]):.2f} {scale_y(point[1]):.2f}"
                for point_index, point in enumerate(points)
            ]
        )
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" />')
        for point in points:
            parts.append(f'<circle cx="{scale_x(point[0]):.2f}" cy="{scale_y(point[1]):.2f}" r="4" fill="{color}" />')
        legend_x = width - margin_right + 16
        legend_item_y = legend_y + index * 24
        parts.append(f'<line x1="{legend_x}" y1="{legend_item_y}" x2="{legend_x + 24}" y2="{legend_item_y}" stroke="{color}" stroke-width="4" />')
        parts.append(
            f'<text x="{legend_x + 32}" y="{legend_item_y + 4}" font-size="12" font-family="Segoe UI, sans-serif" fill="#333">{_svg_text(entry.get("label", ""))}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _display_label(condition_name: str) -> str:
    return DISPLAY_LABELS.get(condition_name, condition_name.replace("_", " ").title())


def _svg_text(value: Any) -> str:
    return escape(str(value), quote=True)


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    return escape(text, quote=False).replace("|", r"\|")
