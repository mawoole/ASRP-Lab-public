"""Scientific Method Engine contracts from RFC-0002.

Purpose:
    Define the domain-independent methodological review boundary for ASRP-Lab.
Responsibilities:
    Represent review requests, quality-gate outcomes, and explainable assessments.
Inputs:
    A scientific activity, referenced evidence, unknowns, and declared assumptions.
Outputs:
    Human-reviewable methodological assessments and recommendations.
Dependencies:
    Shared ASRP-SciOS contracts and the Python standard library.
Limitations:
    Sprint-001 defines no methodology rules, workflow, scoring model, or engine
    implementation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from ._validation import (
    ContractValue,
    freeze_mapping,
    freeze_strings,
    require_aware_datetime,
    require_non_empty,
)
from .common import ConfidenceAssessment, Traceability


@dataclass(frozen=True, slots=True)
class MethodologicalReviewRequest:
    """A domain-neutral scientific activity submitted for methodological review."""

    activity_id: str
    lifecycle_stage: str
    artefact: Mapping[str, ContractValue]
    traceability: Traceability
    evidence_references: tuple[str, ...] = ()
    unknown_references: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "activity_id", require_non_empty(self.activity_id, "activity_id")
        )
        object.__setattr__(
            self,
            "lifecycle_stage",
            require_non_empty(self.lifecycle_stage, "lifecycle_stage"),
        )
        object.__setattr__(self, "artefact", freeze_mapping(self.artefact))
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")
        for field_name in (
            "evidence_references",
            "unknown_references",
            "assumptions",
            "limitations",
        ):
            object.__setattr__(
                self,
                field_name,
                freeze_strings(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class QualityGateResult:
    """An explainable result for one methodological quality gate."""

    gate_id: str
    passed: bool
    rationale: str
    confidence: ConfidenceAssessment
    supporting_evidence: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", require_non_empty(self.gate_id, "gate_id"))
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be a boolean")
        object.__setattr__(
            self, "rationale", require_non_empty(self.rationale, "rationale")
        )
        if not isinstance(self.confidence, ConfidenceAssessment):
            raise TypeError("confidence must be a ConfidenceAssessment record")
        for field_name in ("supporting_evidence", "assumptions", "limitations"):
            object.__setattr__(
                self,
                field_name,
                freeze_strings(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class MethodologicalAssessment:
    """The non-authoritative output of a Scientific Method Engine review."""

    activity_id: str
    reviewer: str
    generated_at: datetime
    gate_results: tuple[QualityGateResult, ...]
    recommendations: tuple[str, ...]
    traceability: Traceability
    requires_human_review: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "activity_id", require_non_empty(self.activity_id, "activity_id")
        )
        object.__setattr__(self, "reviewer", require_non_empty(self.reviewer, "reviewer"))
        object.__setattr__(
            self,
            "generated_at",
            require_aware_datetime(self.generated_at, "generated_at"),
        )
        object.__setattr__(self, "gate_results", tuple(self.gate_results))
        if not all(isinstance(result, QualityGateResult) for result in self.gate_results):
            raise TypeError("gate_results must contain QualityGateResult records")
        object.__setattr__(
            self,
            "recommendations",
            freeze_strings(self.recommendations, "recommendations"),
        )
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")
        if self.requires_human_review is not True:
            raise ValueError("methodological assessments must require human review")


@runtime_checkable
class ScientificMethodEngine(Protocol):
    """Replaceable RFC-0002 methodological evaluation interface."""

    def evaluate(
        self, request: MethodologicalReviewRequest
    ) -> MethodologicalAssessment:
        """Evaluate scientific process quality without deciding scientific truth."""

