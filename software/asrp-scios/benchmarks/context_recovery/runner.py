"""Benchmark runner, proxy metrics, and stable hashing for Sprint-005."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
import hashlib
import json
from time import perf_counter_ns

from asrp_scios.context import ContextQualityResult, ContextSnapshotGenerator
from asrp_scios.domain.aggregates import ContextSnapshot

from .fixture import ContextRecoveryFixture
from .model import BenchmarkResult, BenchmarkScenario, ContextRecoveryMetrics


BENCHMARK_LIMITATIONS = (
    "Synthetic fixture only; results may not generalize to real project graphs.",
    "Metrics are automated proxies; no human evaluation was performed.",
    "generation_time_ms is process-local generation latency, not human Context Recovery Time.",
    "Coverage measures deterministic graph selection, not scientific validity or productivity improvement.",
)


def compute_deterministic_output_hash(payload: Mapping[str, object]) -> str:
    """Hash canonical JSON without timestamps or measured duration."""
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def calculate_context_recovery_metrics(
    *,
    snapshot: ContextSnapshot,
    quality: ContextQualityResult,
    generation_time_ms: float,
    source_graph_entity_count: int,
    source_graph_relationship_count: int,
) -> ContextRecoveryMetrics:
    """Calculate deterministic coverage/size proxies and safe compactness."""
    if not isinstance(snapshot, ContextSnapshot):
        raise TypeError("snapshot must be a ContextSnapshot")
    if not isinstance(quality, ContextQualityResult):
        raise TypeError("quality must be a ContextQualityResult")
    context_entity_count = len(snapshot.scientific_entity_ids)
    context_relationship_count = len(snapshot.relationships)
    reduction_ratio = (
        None
        if source_graph_entity_count == 0
        else round(1.0 - context_entity_count / source_graph_entity_count, 6)
    )
    return ContextRecoveryMetrics(
        generation_time_ms=round(float(generation_time_ms), 6),
        seed_coverage=quality.seed_coverage,
        relationship_coverage=quality.relationship_coverage,
        decision_coverage=quality.decision_coverage,
        evidence_coverage=quality.evidence_coverage,
        unknown_coverage=quality.unknown_coverage,
        context_entity_count=context_entity_count,
        context_relationship_count=context_relationship_count,
        source_graph_entity_count=source_graph_entity_count,
        source_graph_relationship_count=source_graph_relationship_count,
        context_reduction_ratio=reduction_ratio,
        context_quality_proxy=quality.completeness_score,
    )


class ContextRecoveryBenchmark:
    """Execute bounded context-generation scenarios against one fixture."""

    __slots__ = ("_fixture", "_generator", "_timer")

    def __init__(
        self,
        fixture: ContextRecoveryFixture,
        *,
        generator: ContextSnapshotGenerator | None = None,
        timer: Callable[[], int] = perf_counter_ns,
    ) -> None:
        if not isinstance(fixture, ContextRecoveryFixture):
            raise TypeError("fixture must be a ContextRecoveryFixture")
        if generator is not None and not isinstance(generator, ContextSnapshotGenerator):
            raise TypeError("generator must be a ContextSnapshotGenerator")
        if not callable(timer):
            raise TypeError("timer must be callable")
        self._fixture = fixture
        self._generator = generator or ContextSnapshotGenerator(
            clock=lambda: fixture.fixed_time
        )
        self._timer = timer

    @property
    def fixture(self) -> ContextRecoveryFixture:
        return self._fixture

    def run_scenario(self, scenario: BenchmarkScenario | str) -> BenchmarkResult:
        """Generate one snapshot and return its structured proxy result."""
        selected_scenario = (
            self._fixture.scenario(scenario) if isinstance(scenario, str) else scenario
        )
        if not isinstance(selected_scenario, BenchmarkScenario):
            raise TypeError("scenario must be a BenchmarkScenario or scenario ID")
        request = selected_scenario.to_context_request()
        start_ns = self._timer()
        snapshot = self._generator.generate_context_snapshot(
            request, self._fixture.graph
        )
        elapsed_ns = self._timer() - start_ns
        if elapsed_ns < 0:
            raise ValueError("timer must be monotonic")
        quality = self._generator.compute_context_quality(snapshot, request)
        metrics = calculate_context_recovery_metrics(
            snapshot=snapshot,
            quality=quality,
            generation_time_ms=elapsed_ns / 1_000_000,
            source_graph_entity_count=len(self._fixture.entities),
            source_graph_relationship_count=len(self._fixture.relationships),
        )
        provisional = BenchmarkResult(
            scenario_id=selected_scenario.scenario_id,
            scenario_name=selected_scenario.scenario_name,
            metrics=metrics,
            selected_entity_ids=tuple(map(str, snapshot.scientific_entity_ids)),
            selected_relationship_ids=tuple(map(str, snapshot.relationships)),
            warnings=quality.warnings,
            limitations=BENCHMARK_LIMITATIONS + quality.limitations,
            deterministic_output_hash="pending",
        )
        return replace(
            provisional,
            deterministic_output_hash=compute_deterministic_output_hash(
                provisional.stable_payload()
            ),
        )

    def run_all(self) -> tuple[BenchmarkResult, ...]:
        """Execute every fixture scenario in its stable declared order."""
        return tuple(self.run_scenario(scenario) for scenario in self._fixture.scenarios)

