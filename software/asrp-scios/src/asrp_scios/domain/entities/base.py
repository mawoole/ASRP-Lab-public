"""Abstract scientific entity baseline from ONT-001 and UML-001.

Purpose:
    Define the shared identity, lifecycle, version, provenance, and traceability
    carried by every concrete scientific entity.
Responsibilities:
    Validate common fields and prevent direct use of the generic base concept.
Key classes:
    ScientificEntity.
Out-of-scope:
    Persistence, graph storage, repositories, and cross-aggregate operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

from asrp_scios.contracts._validation import (
    ContractValue,
    freeze_mapping,
    freeze_strings,
    require_aware_datetime,
    require_non_empty,
)
from asrp_scios.domain.lifecycle import (
    EvidenceStatus,
    HypothesisStatus,
    LifecycleStatus,
    ResearchDecisionStatus,
    ScientificStatus,
)
from asrp_scios.domain.value_objects import (
    EntityId,
    Provenance,
    Traceability,
    Version,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ScientificEntity:
    """Abstract conceptual base for identifiable scientific objects."""

    id: EntityId
    title: str
    description: str
    status: ScientificStatus
    version: Version
    created_at: datetime
    updated_at: datetime
    created_by: str
    provenance: Provenance
    traceability: Traceability
    relationships: tuple[EntityId, ...] = ()
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, ContractValue] = field(
        default_factory=lambda: freeze_mapping(None), hash=False
    )

    def __post_init__(self) -> None:
        if type(self) is ScientificEntity:
            raise TypeError("ScientificEntity is abstract; use a concrete subclass")
        if not isinstance(self.id, EntityId):
            raise TypeError("id must be an EntityId")
        object.__setattr__(self, "title", require_non_empty(self.title, "title"))
        object.__setattr__(
            self, "description", require_non_empty(self.description, "description")
        )
        valid_status_types = (
            LifecycleStatus,
            HypothesisStatus,
            EvidenceStatus,
            ResearchDecisionStatus,
        )
        if not isinstance(self.status, valid_status_types):
            raise TypeError("status must be a supported scientific lifecycle status")
        if not isinstance(self.version, Version):
            raise TypeError("version must be a Version")
        object.__setattr__(
            self, "created_at", require_aware_datetime(self.created_at, "created_at")
        )
        object.__setattr__(
            self, "updated_at", require_aware_datetime(self.updated_at, "updated_at")
        )
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be earlier than created_at")
        object.__setattr__(
            self, "created_by", require_non_empty(self.created_by, "created_by")
        )
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance record")
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")
        relationships = tuple(self.relationships)
        if not all(isinstance(item, EntityId) for item in relationships):
            raise TypeError("relationships must contain EntityId values")
        object.__setattr__(self, "relationships", relationships)
        object.__setattr__(self, "tags", freeze_strings(self.tags, "tags"))
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))

    @property
    def entity_type(self) -> str:
        """Return the canonical concrete ontology class name."""
        return type(self).__name__

    @property
    def type(self) -> str:
        """Provide the ONT-001 canonical ``type`` field without mutable storage."""
        return self.entity_type

