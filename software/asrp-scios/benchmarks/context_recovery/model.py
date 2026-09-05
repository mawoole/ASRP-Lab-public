"""Immutable values used by the Sprint-005 Context Recovery Benchmark."""

from __future__ import annotations

from dataclasses import dataclass
import math

from asrp_scios.context import ContextRequest
from asrp_scios.domain.value_objects import EntityId


def _non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _ratio(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be numeric")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return normalized


def _count(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True, slots=True, kw_only=True)
class BenchmarkScenario:
    """One bounded, synthetic task-context recovery request."""

    scenario_id: str
    scenario_name: str
    purpose: str
    seed_entity_ids: tuple[EntityId, ...]
    expected_entity_types: tuple[str, ...]
    max_depth: int = 2
    max_entities: int = 18

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "scenario_id", _non_empty(self.scenario_id, "scenario_id")
        )
        object.__setattr__(
            self, "scenario_name", _non_empty(self.scenario_name, "scenario_name")
        )
        object.__setattr__(self, "purpose", _non_empty(self.purpose, "purpose"))
        seed_ids = tuple(self.seed_entity_ids)
        if not seed_ids or not all(isinstance(value, EntityId) for value in seed_ids):
            raise ValueError("seed_entity_ids must contain at least one EntityId")
        if len({str(value) for value in seed_ids}) != len(seed_ids):
            raise ValueError("seed_entity_ids cannot contain duplicates")
        object.__setattr__(self, "seed_entity_ids", tuple(sorted(seed_ids, key=str)))
        expected_types = tuple(self.expected_entity_types)
        if not expected_types or not all(
            isinstance(value, str) and value.strip() for value in expected_types
        ):
            raise ValueError("expected_entity_types must contain non-empty names")
        object.__setattr__(self, "expected_entity_types", expected_types)
        if isinstance(self.max_depth, bool) or not isinstance(self.max_depth, int):
            raise TypeError("max_depth must be an integer")
        if self.max_depth < 0:
            raise ValueError("max_depth cannot be negative")
        if isinstance(self.max_entities, bool) or not isinstance(self.max_entities, int):
            raise TypeError("max_entities must be an integer")
        if self.max_entities < len(seed_ids):
            raise ValueError("max_entities cannot be smaller than the seed count")

    def to_context_request(self) -> ContextRequest:
        """Create the deterministic Sprint-004 request for this scenario."""
        return ContextRequest(
            request_id=EntityId(f"benchmark-request:{self.scenario_id}"),
            task_id=EntityId(f"benchmark-task:{self.scenario_id}"),
            purpose=self.purpose,
            seed_entity_ids=self.seed_entity_ids,
            max_depth=self.max_depth,
            max_entities=self.max_entities,
            generated_by="ASRP-Lab Sprint-005 benchmark",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextRecoveryMetrics:
    """Automated proxy metrics for one generated ContextSnapshot."""

    generation_time_ms: float
    seed_coverage: float
    relationship_coverage: float
    decision_coverage: float
    evidence_coverage: float
    unknown_coverage: float
    context_entity_count: int
    context_relationship_count: int
    source_graph_entity_count: int
    source_graph_relationship_count: int
    context_reduction_ratio: float | None
    context_quality_proxy: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.generation_time_ms, bool)
            or not isinstance(self.generation_time_ms, (int, float))
            or not math.isfinite(float(self.generation_time_ms))
            or self.generation_time_ms < 0
        ):
            raise ValueError("generation_time_ms must be a finite non-negative number")
        object.__setattr__(self, "generation_time_ms", float(self.generation_time_ms))
        for field_name in (
            "seed_coverage",
            "relationship_coverage",
            "decision_coverage",
            "evidence_coverage",
            "unknown_coverage",
            "context_quality_proxy",
        ):
            object.__setattr__(
                self, field_name, _ratio(getattr(self, field_name), field_name)
            )
        for field_name in (
            "context_entity_count",
            "context_relationship_count",
            "source_graph_entity_count",
            "source_graph_relationship_count",
        ):
            object.__setattr__(
                self, field_name, _count(getattr(self, field_name), field_name)
            )
        if self.context_reduction_ratio is not None:
            object.__setattr__(
                self,
                "context_reduction_ratio",
                _ratio(self.context_reduction_ratio, "context_reduction_ratio"),
            )

    def to_dict(self, *, include_timing: bool = True) -> dict[str, object]:
        """Return a JSON-compatible metric mapping."""
        values: dict[str, object] = {
            "seed_coverage": self.seed_coverage,
            "relationship_coverage": self.relationship_coverage,
            "decision_coverage": self.decision_coverage,
            "evidence_coverage": self.evidence_coverage,
            "unknown_coverage": self.unknown_coverage,
            "context_entity_count": self.context_entity_count,
            "context_relationship_count": self.context_relationship_count,
            "source_graph_entity_count": self.source_graph_entity_count,
            "source_graph_relationship_count": self.source_graph_relationship_count,
            "context_reduction_ratio": self.context_reduction_ratio,
            "context_quality_proxy": self.context_quality_proxy,
        }
        if include_timing:
            values = {"generation_time_ms": self.generation_time_ms, **values}
        return values


@dataclass(frozen=True, slots=True, kw_only=True)
class BenchmarkResult:
    """Structured, traceable result from one context recovery scenario."""

    scenario_id: str
    scenario_name: str
    metrics: ContextRecoveryMetrics
    selected_entity_ids: tuple[str, ...]
    selected_relationship_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]
    deterministic_output_hash: str

    @property
    def generation_time_ms(self) -> float:
        return self.metrics.generation_time_ms

    @property
    def selected_relationship_count(self) -> int:
        return len(self.selected_relationship_ids)

    def stable_payload(self) -> dict[str, object]:
        """Return the hash input, excluding volatile wall-clock duration."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "metrics": self.metrics.to_dict(include_timing=False),
            "selected_entity_ids": list(self.selected_entity_ids),
            "selected_relationship_ids": list(self.selected_relationship_ids),
            "selected_relationship_count": self.selected_relationship_count,
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
        }

    def to_dict(self) -> dict[str, object]:
        """Return the complete JSON-compatible benchmark result."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "generation_time_ms": self.generation_time_ms,
            "metrics": self.metrics.to_dict(),
            "selected_entity_ids": list(self.selected_entity_ids),
            "selected_relationship_ids": list(self.selected_relationship_ids),
            "selected_relationship_count": self.selected_relationship_count,
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
            "deterministic_output_hash": self.deterministic_output_hash,
        }

