"""Shared provenance, traceability, and confidence contracts.

Purpose:
    Preserve the metadata required to explain and reconstruct scientific work.
Responsibilities:
    Define immutable provenance, traceability, and confidence records.
Inputs:
    Identifiers, timestamps, references, and human-readable justification.
Outputs:
    Validated value objects used by events, graphs, and scientific systems.
Dependencies:
    Python standard library only.
Limitations:
    These records do not verify external identities, signatures, or evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from ._validation import (
    freeze_strings,
    require_aware_datetime,
    require_non_empty,
    require_optional_non_empty,
)


@dataclass(frozen=True, slots=True)
class Traceability:
    """References connecting an artefact to governing and implementation sources."""

    requirements: tuple[str, ...]
    decisions: tuple[str, ...]
    specifications: tuple[str, ...]
    implementation_version: str
    scientific_program: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "requirements", freeze_strings(self.requirements, "requirements")
        )
        object.__setattr__(
            self, "decisions", freeze_strings(self.decisions, "decisions")
        )
        object.__setattr__(
            self,
            "specifications",
            freeze_strings(self.specifications, "specifications"),
        )
        object.__setattr__(
            self,
            "implementation_version",
            require_non_empty(self.implementation_version, "implementation_version"),
        )
        object.__setattr__(
            self,
            "scientific_program",
            require_optional_non_empty(self.scientific_program, "scientific_program"),
        )


@dataclass(frozen=True, slots=True)
class Provenance:
    """Origin and dependency metadata for a scientific artefact."""

    creator: str
    created_at: datetime
    source: str
    related_evidence: tuple[str, ...] = ()
    review_history: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    method: str | None = None
    input_entities: tuple[str, ...] = ()
    transformation_process: str | None = None
    tool_or_system: str | None = None
    review_status: str | None = None
    version_history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "creator", require_non_empty(self.creator, "creator"))
        object.__setattr__(
            self, "created_at", require_aware_datetime(self.created_at, "created_at")
        )
        object.__setattr__(self, "source", require_non_empty(self.source, "source"))
        object.__setattr__(
            self,
            "related_evidence",
            freeze_strings(self.related_evidence, "related_evidence"),
        )
        object.__setattr__(
            self,
            "review_history",
            freeze_strings(self.review_history, "review_history"),
        )
        object.__setattr__(
            self, "dependencies", freeze_strings(self.dependencies, "dependencies")
        )
        object.__setattr__(
            self, "method", require_optional_non_empty(self.method, "method")
        )
        object.__setattr__(
            self,
            "input_entities",
            freeze_strings(self.input_entities, "input_entities"),
        )
        object.__setattr__(
            self,
            "transformation_process",
            require_optional_non_empty(
                self.transformation_process, "transformation_process"
            ),
        )
        object.__setattr__(
            self,
            "tool_or_system",
            require_optional_non_empty(self.tool_or_system, "tool_or_system"),
        )
        object.__setattr__(
            self,
            "review_status",
            require_optional_non_empty(self.review_status, "review_status"),
        )
        object.__setattr__(
            self,
            "version_history",
            freeze_strings(self.version_history, "version_history"),
        )


@dataclass(frozen=True, slots=True)
class ConfidenceAssessment:
    """A bounded confidence value accompanied by an explicit explanation."""

    score: float
    rationale: str
    assessed_at: datetime
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("score must be a number")
        normalized_score = float(self.score)
        if not math.isfinite(normalized_score) or not 0.0 <= normalized_score <= 1.0:
            raise ValueError("score must be finite and between 0.0 and 1.0")
        object.__setattr__(self, "score", normalized_score)
        object.__setattr__(
            self, "rationale", require_non_empty(self.rationale, "rationale")
        )
        object.__setattr__(
            self,
            "assessed_at",
            require_aware_datetime(self.assessed_at, "assessed_at"),
        )
        object.__setattr__(
            self, "assumptions", freeze_strings(self.assumptions, "assumptions")
        )
        object.__setattr__(
            self, "limitations", freeze_strings(self.limitations, "limitations")
        )
