"""Deterministic Context Engineering selection policy.

Purpose:
    Encode Sprint-004 entity, relationship, and historical-record priorities.
Responsibilities:
    Rank canonical types and identify traceability-preserving historical links.
Inputs:
    Existing ScientificEntity and ScientificRelationship domain objects.
Outputs:
    Stable sortable priority keys and history/traceability classifications.
Dependencies:
    ASRP-SciOS domain model and Sprint-003 traceability relationship vocabulary.
Limitations:
    Policy performs no retrieval, inference, persistence, or scientific scoring.
"""

from __future__ import annotations

from dataclasses import dataclass

from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.relationships import ScientificRelationship
from asrp_scios.domain.value_objects import RelationshipType
from asrp_scios.srg import TRACEABILITY_RELATIONSHIP_TYPES


DEFAULT_ENTITY_TYPE_PRIORITY = (
    "ResearchDecision",
    "Evidence",
    "Unknown",
    "Hypothesis",
    "ScientificQuestion",
    "KnowledgeItem",
    "Discovery",
    "ResearchCampaign",
    "ScientificProgram",
)

DEFAULT_RELATIONSHIP_TYPE_PRIORITY = (
    RelationshipType.DECIDED_BY,
    RelationshipType.SUPPORTS,
    RelationshipType.CONTRADICTS,
    RelationshipType.VALIDATES,
    RelationshipType.INVALIDATES,
    RelationshipType.DERIVES_FROM,
    RelationshipType.USES_CONTEXT,
    RelationshipType.REFERENCES,
    RelationshipType.SUPERSEDES,
    RelationshipType.DEPENDS_ON,
)

_ENTITY_TYPE_ALIASES = {"ResearchProgram": "ScientificProgram"}


@dataclass(frozen=True, slots=True)
class ContextSelectionPolicy:
    """Canonical type priorities for bounded ContextSnapshot generation."""

    entity_type_priority: tuple[str, ...] = DEFAULT_ENTITY_TYPE_PRIORITY
    relationship_type_priority: tuple[
        RelationshipType, ...
    ] = DEFAULT_RELATIONSHIP_TYPE_PRIORITY

    def __post_init__(self) -> None:
        entity_priority = tuple(self.entity_type_priority)
        if not entity_priority or not all(
            isinstance(value, str) and value.strip() for value in entity_priority
        ):
            raise ValueError("entity_type_priority must contain non-empty names")
        if len(entity_priority) != len(set(entity_priority)):
            raise ValueError("entity_type_priority cannot contain duplicates")
        relationship_priority = tuple(self.relationship_type_priority)
        if not relationship_priority or not all(
            isinstance(value, RelationshipType) for value in relationship_priority
        ):
            raise TypeError(
                "relationship_type_priority must contain RelationshipType values"
            )
        if len(relationship_priority) != len(set(relationship_priority)):
            raise ValueError("relationship_type_priority cannot contain duplicates")
        object.__setattr__(self, "entity_type_priority", entity_priority)
        object.__setattr__(
            self, "relationship_type_priority", relationship_priority
        )

    def entity_sort_key(self, entity: ScientificEntity) -> tuple[int, str]:
        """Order entities by CS-004 priority and then stable identity."""
        entity_type = _ENTITY_TYPE_ALIASES.get(entity.entity_type, entity.entity_type)
        try:
            priority = self.entity_type_priority.index(entity_type)
        except ValueError:
            priority = len(self.entity_type_priority)
        return priority, str(entity.id)

    def relationship_sort_key(
        self, relationship: ScientificRelationship
    ) -> tuple[int, str, str]:
        """Order relationships by CS-005 priority, type, and stable identity."""
        try:
            priority = self.relationship_type_priority.index(
                relationship.relationship_type
            )
        except ValueError:
            priority = len(self.relationship_type_priority)
        return priority, relationship.relationship_type.value, str(
            relationship.relationship_id
        )

    @staticmethod
    def is_historical(entity: ScientificEntity) -> bool:
        """Return true for archived or deprecated entity states."""
        return getattr(entity.status, "value", None) in {"Archived", "Deprecated"}

    @staticmethod
    def is_historical_relationship(
        relationship: ScientificRelationship,
    ) -> bool:
        """Return true for archived or deprecated relationship states."""
        return getattr(relationship.status, "value", None) in {
            "Archived",
            "Deprecated",
        }

    @staticmethod
    def preserves_traceability(relationship: ScientificRelationship) -> bool:
        """Return true when a relationship belongs to the SRG traceability set."""
        return relationship.relationship_type in TRACEABILITY_RELATIONSHIP_TYPES
