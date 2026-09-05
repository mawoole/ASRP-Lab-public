"""Scientific Research Graph contracts from RFC-0001.

Purpose:
    Define a technology-agnostic API for preserving evolving scientific research.
Responsibilities:
    Model versioned entities, explicit relationships, research branches, and
    query criteria; define the structural graph engine interface.
Inputs:
    Immutable scientific artefacts with provenance, confidence, and traceability.
Outputs:
    Versioned graph records and query results.
Dependencies:
    Shared ASRP-SciOS contracts and the Python standard library.
Limitations:
    No graph storage, ontology, reasoning, ranking, or confidence algorithm is
    implemented in Sprint-001.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from ._validation import (
    ContractValue,
    freeze_mapping,
    freeze_strings,
    require_aware_datetime,
    require_non_empty,
    require_optional_non_empty,
)
from .common import ConfidenceAssessment, Provenance, Traceability


@dataclass(frozen=True, slots=True)
class ScientificEntity:
    """One immutable version of any identifiable scientific artefact."""

    entity_id: str
    entity_type: str
    version: int
    content: Mapping[str, ContractValue]
    provenance: Provenance
    confidence: ConfidenceAssessment
    traceability: Traceability

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "entity_id", require_non_empty(self.entity_id, "entity_id")
        )
        object.__setattr__(
            self, "entity_type", require_non_empty(self.entity_type, "entity_type")
        )
        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer")
        if self.version < 1:
            raise ValueError("version must be at least 1")
        object.__setattr__(self, "content", freeze_mapping(self.content))
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance record")
        if not isinstance(self.confidence, ConfidenceAssessment):
            raise TypeError("confidence must be a ConfidenceAssessment record")
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")


@dataclass(frozen=True, slots=True)
class ScientificRelationship:
    """An explicit, typed, and traceable relationship between two entities."""

    relationship_id: str
    relationship_type: str
    source_entity_id: str
    target_entity_id: str
    provenance: Provenance
    traceability: Traceability

    def __post_init__(self) -> None:
        for field_name in (
            "relationship_id",
            "relationship_type",
            "source_entity_id",
            "target_entity_id",
        ):
            object.__setattr__(
                self,
                field_name,
                require_non_empty(getattr(self, field_name), field_name),
            )
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance record")
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")


@dataclass(frozen=True, slots=True)
class ResearchBranch:
    """A named research path that may diverge and later be explicitly merged."""

    branch_id: str
    name: str
    created_at: datetime
    parent_branch_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "branch_id", require_non_empty(self.branch_id, "branch_id")
        )
        object.__setattr__(self, "name", require_non_empty(self.name, "name"))
        object.__setattr__(
            self, "created_at", require_aware_datetime(self.created_at, "created_at")
        )
        object.__setattr__(
            self,
            "parent_branch_id",
            require_optional_non_empty(self.parent_branch_id, "parent_branch_id"),
        )


@dataclass(frozen=True, slots=True)
class GraphQuery:
    """Portable graph query criteria without database-specific syntax."""

    start_entity_id: str | None = None
    entity_types: tuple[str, ...] = ()
    relationship_types: tuple[str, ...] = ()
    branch_id: str | None = None
    include_history: bool = False
    metadata: Mapping[str, ContractValue] = field(
        default_factory=lambda: freeze_mapping(None), hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "start_entity_id",
            require_optional_non_empty(self.start_entity_id, "start_entity_id"),
        )
        object.__setattr__(
            self, "entity_types", freeze_strings(self.entity_types, "entity_types")
        )
        object.__setattr__(
            self,
            "relationship_types",
            freeze_strings(self.relationship_types, "relationship_types"),
        )
        object.__setattr__(
            self,
            "branch_id",
            require_optional_non_empty(self.branch_id, "branch_id"),
        )
        if not isinstance(self.include_history, bool):
            raise TypeError("include_history must be a boolean")
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


GraphRecord = ScientificEntity | ScientificRelationship


@runtime_checkable
class ScientificResearchGraph(Protocol):
    """Storage-independent RFC-0001 graph engine interface.

    Implementations must preserve prior versions and branches, never silently
    discard graph records, and publish a traceable ``ScientificEvent`` for each
    successful mutation through their injected event bus.
    """

    def record_entity(self, entity: ScientificEntity, *, branch_id: str) -> None:
        """Append an entity version to a research branch without overwriting history."""

    def record_relationship(
        self, relationship: ScientificRelationship, *, branch_id: str
    ) -> None:
        """Append an explicit relationship to a research branch."""

    def get_entity(
        self,
        entity_id: str,
        *,
        version: int | None = None,
        branch_id: str | None = None,
    ) -> ScientificEntity | None:
        """Return a requested version, or the current version when omitted."""

    def query(self, query: GraphQuery) -> Sequence[GraphRecord]:
        """Return graph records matching portable query criteria."""

    def create_branch(self, branch: ResearchBranch) -> None:
        """Create an explicit alternative research path."""

    def merge_branch(
        self, *, source_branch_id: str, target_branch_id: str, traceability: Traceability
    ) -> None:
        """Merge branches explicitly while preserving both histories."""

