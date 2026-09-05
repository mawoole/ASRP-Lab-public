"""Sprint-005 deterministic Context Recovery Benchmark public API."""

from .fixture import ContextRecoveryFixture, build_context_recovery_fixture
from .model import BenchmarkResult, BenchmarkScenario, ContextRecoveryMetrics
from .report import render_markdown_report, write_benchmark_reports
from .runner import (
    ContextRecoveryBenchmark,
    calculate_context_recovery_metrics,
    compute_deterministic_output_hash,
)

__all__ = [
    "BenchmarkResult",
    "BenchmarkScenario",
    "ContextRecoveryBenchmark",
    "ContextRecoveryFixture",
    "ContextRecoveryMetrics",
    "build_context_recovery_fixture",
    "calculate_context_recovery_metrics",
    "compute_deterministic_output_hash",
    "render_markdown_report",
    "write_benchmark_reports",
]

