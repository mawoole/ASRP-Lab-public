"""JSON and Markdown report rendering for Context Recovery Benchmark results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from .model import BenchmarkResult


BENCHMARK_ID = "sprint-005-context-recovery"


def _ratio(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.6f}"


def render_markdown_report(results: Sequence[BenchmarkResult]) -> str:
    """Render a cautious, reproducible proxy-metric benchmark report."""
    values = tuple(results)
    if not values:
        raise ValueError("at least one BenchmarkResult is required")
    first = values[0].metrics
    lines = [
        "# Context Recovery Benchmark Report",
        "",
        "## Benchmark",
        "",
        f"- Benchmark ID: `{BENCHMARK_ID}`",
        "- ASRP-SciOS runtime version: `0.4.0`",
        "- Evaluation type: automated synthetic proxy benchmark",
        "- Human evaluation executed: no",
        "",
        "## Fixture Summary",
        "",
        f"- Source entities: {first.source_graph_entity_count}",
        f"- Source relationships: {first.source_graph_relationship_count}",
        f"- Scenarios executed: {len(values)}",
        "",
        "## Metrics",
        "",
        "| Scenario | generation_time_ms | Entities | Relationships | Reduction | Seed | Relationship | Decision | Evidence | Unknown | Quality proxy | Stable hash |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for result in values:
        metrics = result.metrics
        lines.append(
            f"| {result.scenario_name} | {metrics.generation_time_ms:.6f} "
            f"| {metrics.context_entity_count} | {metrics.context_relationship_count} "
            f"| {_ratio(metrics.context_reduction_ratio)} | {metrics.seed_coverage:.6f} "
            f"| {metrics.relationship_coverage:.6f} | {metrics.decision_coverage:.6f} "
            f"| {metrics.evidence_coverage:.6f} | {metrics.unknown_coverage:.6f} "
            f"| {metrics.context_quality_proxy:.6f} | `{result.deterministic_output_hash}` |"
        )
    lines.extend(
        [
            "",
            "## Selected Context",
            "",
        ]
    )
    for result in values:
        lines.extend(
            [
                f"### {result.scenario_name}",
                "",
                "Selected entity IDs:",
                "",
                *(f"- `{value}`" for value in result.selected_entity_ids),
                "",
                f"Selected relationships: {result.selected_relationship_count}",
                "",
                "Warnings: " + ("; ".join(result.warnings) if result.warnings else "None"),
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "These results show deterministic, bounded graph selection on the controlled synthetic fixture. Coverage and compactness are proxy measurements of the generated ContextSnapshot; they do not establish faster human recovery or improved scientific productivity.",
            "",
            "The stable hash excludes `generation_time_ms`, because process timing is inherently variable. It includes scenario identity, all other metrics, selected entity and relationship identities, warnings, and limitations.",
            "",
            "## Limitations",
            "",
            "- Synthetic fixture only; external validity has not been assessed.",
            "- Automated proxy metrics only; the documented human protocol was not executed.",
            "- Timing is local generation latency, not human Context Recovery Time.",
            "- No statistical significance or human productivity claim is made.",
            "- Coverage reflects the fixture and Sprint-004 selection policy, not scientific correctness.",
            "",
            "## Next Step",
            "",
            "Run the documented controlled human evaluation in a future validation sprint with approved participants, tasks, scoring, and analysis.",
            "",
        ]
    )
    return "\n".join(lines)


def write_benchmark_reports(
    results: Sequence[BenchmarkResult], output_directory: Path | str
) -> tuple[Path, Path]:
    """Write local JSON and Markdown artifacts; no persistence service is used."""
    values = tuple(results)
    if not values:
        raise ValueError("at least one BenchmarkResult is required")
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "context_recovery_benchmark.json"
    markdown_path = output_path / "context_recovery_benchmark.md"
    payload = {
        "benchmark_id": BENCHMARK_ID,
        "evaluation_type": "automated_synthetic_proxy",
        "human_evaluation_executed": False,
        "results": [result.to_dict() for result in values],
    }
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown_report(values), encoding="utf-8")
    return json_path, markdown_path

