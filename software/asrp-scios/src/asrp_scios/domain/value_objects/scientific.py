"""Scientific semantic value objects from ONT-001 and UML-001.

Purpose:
    Represent evidence direction, relationships, confidence, references, and review.
Responsibilities:
    Enforce closed vocabularies and immutable scientific metadata invariants.
Key classes:
    Confidence, ScientificReference, HumanReviewMetadata, EvidenceDirection,
    RelationshipType, EvidenceType, ConfidenceLevel, and DecisionType.
Out-of-scope:
    Confidence algorithms, evidence ranking, reviewer identity verification,
    and authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math

from asrp_scios.contracts._validation import (
    freeze_strings,
    require_aware_datetime,
    require_non_empty,
    require_optional_non_empty,
)
from asrp_scios.domain.lifecycle import ReviewStatus

from .identifiers import EntityId
from .version import Version


class RelationshipType(str, Enum):
    BELONGS_TO = "belongs_to"
    DERIVES_FROM = "derives_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REFINES = "refines"
    VALIDATES = "validates"
    INVALIDATES = "invalidates"
    TESTS = "tests"
    OBSERVES = "observes"
    GENERATES = "generates"
    REFERENCES = "references"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    EXPLAINS = "explains"
    REQUIRES_REVIEW = "requires_review"
    DECIDED_BY = "decided_by"
    USES_CONTEXT = "uses_context"


class EvidenceDirection(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REFINES = "refines"
    QUALIFIES = "qualifies"
    WEAKENS = "weakens"
    INVALIDATES = "invalidates"


class EvidenceType(str, Enum):
    EXPERIMENTAL = "ExperimentalEvidence"
    SIMULATION = "SimulationEvidence"
    LITERATURE = "LiteratureEvidence"
    MEASUREMENT = "MeasurementEvidence"
    REVIEW = "ReviewEvidence"
    REPRODUCIBILITY = "ReproducibilityEvidence"
    NEGATIVE = "NegativeEvidence"


class ConfidenceLevel(str, Enum):
    SPECULATIVE = "Speculative"
    PLAUSIBLE = "Plausible"
    SUPPORTED = "Supported"
    STRONGLY_SUPPORTED = "StronglySupported"
    VALIDATED = "Validated"
    REJECTED = "Rejected"


class DecisionType(str, Enum):
    SCIENTIFIC = "ScientificDecision"
    METHODOLOGICAL = "MethodologicalDecision"
    ARCHITECTURAL = "ArchitecturalDecision"
    PROGRAM = "ProgramDecision"
    PUBLICATION = "PublicationDecision"
    PATENT = "PatentDecision"


@dataclass(frozen=True, slots=True)
class Confidence:
    """A qualitative confidence level with rationale and supporting references."""

    level: ConfidenceLevel
    rationale: str
    assessed_at: datetime
    evidence_references: tuple[EntityId, ...] = ()
    score: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.level, ConfidenceLevel):
            raise TypeError("level must be a ConfidenceLevel")
        object.__setattr__(
            self, "rationale", require_non_empty(self.rationale, "rationale")
        )
        object.__setattr__(
            self,
            "assessed_at",
            require_aware_datetime(self.assessed_at, "assessed_at"),
        )
        references = tuple(self.evidence_references)
        if not all(isinstance(reference, EntityId) for reference in references):
            raise TypeError("evidence_references must contain EntityId values")
        object.__setattr__(self, "evidence_references", references)
        if self.score is not None:
            if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
                raise TypeError("score must be a number when provided")
            normalized_score = float(self.score)
            if not math.isfinite(normalized_score) or not 0.0 <= normalized_score <= 1.0:
                raise ValueError("score must be finite and between 0.0 and 1.0")
            object.__setattr__(self, "score", normalized_score)
        evidence_backed_levels = {
            ConfidenceLevel.SUPPORTED,
            ConfidenceLevel.STRONGLY_SUPPORTED,
            ConfidenceLevel.VALIDATED,
            ConfidenceLevel.REJECTED,
        }
        if self.level in evidence_backed_levels and not references:
            raise ValueError(f"{self.level.value} confidence requires evidence")


@dataclass(frozen=True, slots=True)
class ScientificReference:
    """A version-aware reference to a scientific entity or source."""

    entity_id: EntityId
    version: Version | None = None
    source: str | None = None
    citation: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, EntityId):
            raise TypeError("entity_id must be an EntityId")
        if self.version is not None and not isinstance(self.version, Version):
            raise TypeError("version must be a Version when provided")
        object.__setattr__(
            self, "source", require_optional_non_empty(self.source, "source")
        )
        object.__setattr__(
            self, "citation", require_optional_non_empty(self.citation, "citation")
        )


@dataclass(frozen=True, slots=True)
class HumanReviewMetadata:
    """Human responsibility metadata for validation and decision structures."""

    reviewer_id: str
    status: ReviewStatus
    reviewed_at: datetime | None = None
    rationale: str | None = None
    decision_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "reviewer_id", require_non_empty(self.reviewer_id, "reviewer_id")
        )
        if not isinstance(self.status, ReviewStatus):
            raise TypeError("status must be a ReviewStatus")
        if self.reviewed_at is not None:
            object.__setattr__(
                self,
                "reviewed_at",
                require_aware_datetime(self.reviewed_at, "reviewed_at"),
            )
        object.__setattr__(
            self, "rationale", require_optional_non_empty(self.rationale, "rationale")
        )
        object.__setattr__(
            self,
            "decision_reference",
            require_optional_non_empty(
                self.decision_reference, "decision_reference"
            ),
        )
        completed = {
            ReviewStatus.COMPLETED,
            ReviewStatus.ACCEPTED,
            ReviewStatus.REJECTED,
        }
        if self.status in completed and (
            self.reviewed_at is None or self.rationale is None
        ):
            raise ValueError("completed human review requires timestamp and rationale")

    @property
    def is_complete(self) -> bool:
        return self.status in {
            ReviewStatus.COMPLETED,
            ReviewStatus.ACCEPTED,
            ReviewStatus.REJECTED,
        }

