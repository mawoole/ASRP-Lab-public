"""Directed scientific relationship model from ONT-001.

Purpose:
    Represent explicit semantic links between scientific entities.
Responsibilities:
    Validate relationship identity, direction, confidence, provenance, and rationale.
Key classes:
    ScientificRelationship.
Out-of-scope:
    Graph traversal, persistence, symmetric-edge expansion, and query execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from asrp_scios.contracts._validation import (
    require_aware_datetime,
    require_non_empty,
)
from asrp_scios.domain.lifecycle import LifecycleStatus
from asrp_scios.domain.value_objects import (
    Confidence,
    EntityId,
    Provenance,
    RelationshipType,
    Traceability,
)


@dataclass(frozen=True, slots=True)
class ScientificRelationship:
    """An immutable directed relationship with scientific meaning."""

    relationship_id: EntityId
    relationship_type: RelationshipType
    source_entity_id: EntityId
    target_entity_id: EntityId
    confidence: Confidence
    provenance: Provenance
    traceability: Traceability
    created_at: datetime
    created_by: str
    rationale: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    def __post_init__(self) -> None:
        for field_name in (
            "relationship_id",
            "source_entity_id",
            "target_entity_id",
        ):
            if not isinstance(getattr(self, field_name), EntityId):
                raise TypeError(f"{field_name} must be an EntityId")
        if not isinstance(self.relationship_type, RelationshipType):
            raise TypeError("relationship_type must be a RelationshipType")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence")
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance record")
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")
        object.__setattr__(
            self, "created_at", require_aware_datetime(self.created_at, "created_at")
        )
        object.__setattr__(
            self, "created_by", require_non_empty(self.created_by, "created_by")
        )
        object.__setattr__(
            self, "rationale", require_non_empty(self.rationale, "rationale")
        )
        if not isinstance(self.status, LifecycleStatus):
            raise TypeError("status must be a LifecycleStatus")

