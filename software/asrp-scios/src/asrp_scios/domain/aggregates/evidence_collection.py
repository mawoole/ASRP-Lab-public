"""EvidenceCollection aggregate root.

Purpose:
    Preserve positive, negative, and qualifying evidence for one target claim.
Responsibilities:
    Require provenance and direction for every evidence item and emit additions.
Key classes:
    EvidenceCollection.
Out-of-scope:
    Evidence retrieval, automatic quality scoring, persistence, and ranking.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from asrp_scios.contracts._validation import require_optional_non_empty
from asrp_scios.domain.entities import Evidence, ScientificEntity
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.value_objects import AggregateId, EntityId, EvidenceType

from .base import create_aggregate_event


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceCollection(ScientificEntity):
    """AGG-001 evidence root for a single question, hypothesis, or discovery."""

    id: AggregateId
    target_entity_id: EntityId
    evidence_items: tuple[Evidence, ...] = ()
    quality_rationale: str | None = None

    def __post_init__(self) -> None:
        super(EvidenceCollection, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        if not isinstance(self.target_entity_id, EntityId):
            raise TypeError("target_entity_id must be an EntityId")
        items = tuple(self.evidence_items)
        if not all(isinstance(item, Evidence) for item in items):
            raise TypeError("evidence_items must contain Evidence values")
        identifiers = tuple(item.id for item in items)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("evidence_items cannot contain duplicate identities")
        # Evidence validates its own mandatory provenance and direction; retaining
        # complete objects here makes those invariants impossible to omit.
        object.__setattr__(self, "evidence_items", items)
        object.__setattr__(
            self,
            "quality_rationale",
            require_optional_non_empty(self.quality_rationale, "quality_rationale"),
        )

    def add_evidence(
        self, evidence: Evidence, *, added_at: datetime, added_by: str
    ) -> tuple[EvidenceCollection, ScientificEvent]:
        """Return a collection containing a new, fully attributed evidence item."""
        if not isinstance(evidence, Evidence):
            raise TypeError("evidence must be an Evidence")
        if any(existing.id == evidence.id for existing in self.evidence_items):
            raise ValueError("evidence item is already present")
        updated = replace(
            self,
            evidence_items=self.evidence_items + (evidence,),
            version=self.version.next_patch(),
            updated_at=added_at,
        )
        event_type = (
            "NegativeEvidenceRecorded"
            if evidence.evidence_type is EvidenceType.NEGATIVE
            else "EvidenceItemAdded"
        )
        event = create_aggregate_event(
            updated,
            event_type,
            produced_by=added_by,
            payload={
                "evidence_id": str(evidence.id),
                "evidence_type": evidence.evidence_type.value,
                "direction": evidence.direction.value,
                "target_entity_id": str(self.target_entity_id),
            },
            occurred_at=added_at,
            related_entity_ids=(evidence.id, self.target_entity_id),
        )
        return updated, event
