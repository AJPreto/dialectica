"""Markdown and SVG reporting helpers for Dialectica benchmark runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PREFERRED_CONDITION_ORDER = [
    "direct",
    "dialectica_compact",
    "dialectica_filtered",
    "dialectica_structural_compact",
    "dialectica_filtered_structural",
]

DISPLAY_LABELS = {
    "direct": "Direct",
    "dialectica_compact": "Compact",
    "dialectica_filtered": "Filtered",
    "dialectica_structural_compact": "Structural Compact",
    "dialectica_filtered_structural": "Filtered Structural",
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
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-family="Segoe UI, sans-serif" fill="#1f1f1f">{title}</text>',
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<text x="20" y="{margin_top + plot_height / 2}" transform="rotate(-90 20 {margin_top + plot_height / 2})" text-anchor="middle" font-size="14" font-family="Segoe UI, sans-serif" fill="#333">{y_label}</text>',
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
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" transform="rotate(35 {label_x:.2f} {label_y:.2f})" text-anchor="start" font-size="12" font-family="Segoe UI, sans-serif" fill="#333">{label}</text>'
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
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-family="Segoe UI, sans-serif" fill="#1f1f1f">{title}</text>',
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#444" stroke-width="2" />',
        f'<text x="{width / 2}" y="{height - 20}" text-anchor="middle" font-size="14" font-family="Segoe UI, sans-serif" fill="#333">{x_label}</text>',
        f'<text x="20" y="{margin_top + plot_height / 2}" transform="rotate(-90 20 {margin_top + plot_height / 2})" text-anchor="middle" font-size="14" font-family="Segoe UI, sans-serif" fill="#333">{y_label}</text>',
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
            f'<text x="{legend_x + 32}" y="{legend_item_y + 4}" font-size="12" font-family="Segoe UI, sans-serif" fill="#333">{entry.get("label", "")}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _display_label(condition_name: str) -> str:
    return DISPLAY_LABELS.get(condition_name, condition_name.replace("_", " ").title())
