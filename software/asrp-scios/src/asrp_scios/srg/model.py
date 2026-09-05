"""Immutable SRG query and result values.

Purpose:
    Represent directions, bounded paths, traceability subgraphs, and integrity.
Responsibilities:
    Validate query-result structure and keep returned graph views immutable.
Inputs:
    Existing domain entity, relationship, and identifier objects.
Outputs:
    Typed deterministic values returned by the in-memory SRG service.
Invariants:
    Paths alternate entities and relationships; integrity reports are immutable.
Dependencies:
    ASRP-SciOS domain model and Python standard library.
Limitations:
    Values do not serialize, persist, infer, rank, or execute queries.
Non-goals:
    Database query languages, ontology reasoning, and graph analytics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from asrp_scios.contracts._validation import require_non_empty
from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.relationships import ScientificRelationship
from asrp_scios.domain.value_objects import EntityId


class GraphDirection(str, Enum):
    """Purpose: select directed graph traversal; inputs/outputs: canonical text.

    Invariants: only outgoing, incoming, and both are valid.
    Non-goals: defining symmetric ontology relationships.
    """

    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class GraphPath:
    """Purpose: represent one simple directed path.

    Inputs: ordered entity and relationship IDs.
    Outputs: an immutable alternating path description.
    Invariants: entity count is exactly relationship count plus one.
    Non-goals: path scoring, ranking, persistence, or lazy traversal.
    """

    entity_ids: tuple[EntityId, ...]
    relationship_ids: tuple[EntityId, ...] = ()

    def __post_init__(self) -> None:
        entity_ids = tuple(self.entity_ids)
        relationship_ids = tuple(self.relationship_ids)
        if not entity_ids or not all(isinstance(value, EntityId) for value in entity_ids):
            raise ValueError("entity_ids must contain at least one EntityId")
        if not all(isinstance(value, EntityId) for value in relationship_ids):
            raise TypeError("relationship_ids must contain EntityId values")
        if len(entity_ids) != len(relationship_ids) + 1:
            raise ValueError(
                "a graph path requires one more entity than relationship"
            )
        if len({str(value) for value in entity_ids}) != len(entity_ids):
            raise ValueError("GraphPath must be simple and cannot repeat an entity")
        object.__setattr__(self, "entity_ids", entity_ids)
        object.__setattr__(self, "relationship_ids", relationship_ids)

    @property
    def depth(self) -> int:
        """Return the number of relationship hops in this path."""
        return len(self.relationship_ids)


@dataclass(frozen=True, slots=True)
class TraceabilitySubgraph:
    """Purpose: return the traceability component around one scientific entity.

    Inputs: a root ID plus direction-preserving entities and relationships.
    Outputs: an immutable, deterministic connected subgraph.
    Invariants: the root and every relationship endpoint occur in ``entities``.
    Non-goals: scientific inference, completeness claims, or context ranking.
    """

    root_entity_id: EntityId
    entities: tuple[ScientificEntity, ...]
    relationships: tuple[ScientificRelationship, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.root_entity_id, EntityId):
            raise TypeError("root_entity_id must be an EntityId")
        entities = tuple(self.entities)
        relationships = tuple(self.relationships)
        if not all(isinstance(value, ScientificEntity) for value in entities):
            raise TypeError("entities must contain ScientificEntity values")
        if not all(
            isinstance(value, ScientificRelationship) for value in relationships
        ):
            raise TypeError(
                "relationships must contain ScientificRelationship values"
            )
        entity_keys = {str(value.id) for value in entities}
        if str(self.root_entity_id) not in entity_keys:
            raise ValueError("traceability subgraph must contain its root entity")
        for relationship in relationships:
            if str(relationship.source_entity_id) not in entity_keys or str(
                relationship.target_entity_id
            ) not in entity_keys:
                raise ValueError(
                    "traceability relationship endpoints must occur in entities"
                )
        object.__setattr__(self, "entities", entities)
        object.__setattr__(self, "relationships", relationships)


@dataclass(frozen=True, slots=True)
class GraphIntegrityIssue:
    """Purpose: describe one detected in-memory graph inconsistency.

    Inputs: stable issue code, explanation, and optional graph identifiers.
    Outputs: immutable diagnostic data.
    Invariants: code and message are non-empty.
    Non-goals: automatic repair or persistence diagnostics.
    """

    code: str
    message: str
    entity_id: str | None = None
    relationship_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", require_non_empty(self.code, "code"))
        object.__setattr__(
            self, "message", require_non_empty(self.message, "message")
        )


@dataclass(frozen=True, slots=True)
class GraphIntegrityReport:
    """Purpose: report graph health without mutating or repairing the graph.

    Inputs: ordered integrity issues from a complete in-memory validation pass.
    Outputs: immutable issues and an ``is_valid`` convenience property.
    Invariants: every issue is a ``GraphIntegrityIssue``.
    Non-goals: repair, recovery, migration, or durability guarantees.
    """

    issues: tuple[GraphIntegrityIssue, ...] = ()

    def __post_init__(self) -> None:
        issues = tuple(self.issues)
        if not all(isinstance(value, GraphIntegrityIssue) for value in issues):
            raise TypeError("issues must contain GraphIntegrityIssue values")
        object.__setattr__(self, "issues", issues)

    @property
    def is_valid(self) -> bool:
        """Return true only when no integrity issue was detected."""
        return not self.issues
