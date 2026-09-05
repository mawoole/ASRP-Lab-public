"""Command-line entry point for the Sprint-005 Context Recovery Benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))

from benchmarks.context_recovery import (  # noqa: E402
    ContextRecoveryBenchmark,
    build_context_recovery_fixture,
    write_benchmark_reports,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic synthetic Context Recovery Benchmark."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "artifacts",
        help="Directory for JSON and Markdown reports.",
    )
    arguments = parser.parse_args(argv)
    benchmark = ContextRecoveryBenchmark(build_context_recovery_fixture())
    results = benchmark.run_all()
    json_path, markdown_path = write_benchmark_reports(results, arguments.output_dir)
    for result in results:
        print(
            f"{result.scenario_id}: entities={result.metrics.context_entity_count}, "
            f"relationships={result.metrics.context_relationship_count}, "
            f"hash={result.deterministic_output_hash}"
        )
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

