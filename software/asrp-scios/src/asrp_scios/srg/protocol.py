"""Scientific Research Graph MVP structural protocol.

Purpose:
    Define the domain-object API implemented by the Sprint-003 graph service.
Responsibilities:
    Specify mutation, lookup, neighborhood, path, traceability, and validation.
Inputs:
    Sprint-002B entities, relationships, typed identifiers, and bounded queries.
Outputs:
    Immutable domain objects and deterministic query-result values.
Invariants:
    Implementations reject invalid mutations and never discard scientific data.
Dependencies:
    ASRP-SciOS domain model and SRG result values.
Limitations:
    This additive MVP protocol does not model Sprint-001 branches or history.
Non-goals:
    Persistence, event delivery, APIs, orchestration, inference, and graph DBs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.relationships import ScientificRelationship
from asrp_scios.domain.value_objects import EntityId, RelationshipType

from .model import (
    GraphDirection,
    GraphIntegrityReport,
    GraphPath,
    TraceabilitySubgraph,
)


@runtime_checkable
class ScientificResearchGraph(Protocol):
    """Purpose: provide the typed Sprint-003 SRG service boundary.

    Inputs: immutable domain entities/relationships and explicit query bounds.
    Outputs: deterministic tuples, paths, traceability views, and health reports.
    Invariants: IDs are unique and every relationship endpoint exists.
    Non-goals: RFC-0001 branch/history behavior, persistence, or event transport.
    """

    def register_entity(self, entity: ScientificEntity) -> None:
        """Register one immutable entity; reject an existing stable ID."""
        ...

    def get_entity(self, entity_id: EntityId | str) -> ScientificEntity | None:
        """Return an entity by stable ID, or ``None`` when it is unknown."""
        ...

    def add_relationship(self, relationship: ScientificRelationship) -> None:
        """Register a typed relationship whose two endpoints already exist."""
        ...

    def get_relationships(
        self,
        *,
        entity_id: EntityId | str | None = None,
        source_id: EntityId | str | None = None,
        target_id: EntityId | str | None = None,
        relationship_type: RelationshipType | str | None = None,
        direction: GraphDirection | str | None = None,
    ) -> tuple[ScientificRelationship, ...]:
        """Return relationships matching the supplied conjunctive filters."""
        ...

    def get_neighbors(
        self,
        entity_id: EntityId | str,
        *,
        relationship_type: RelationshipType | str | None = None,
        direction: GraphDirection | str = GraphDirection.BOTH,
    ) -> tuple[ScientificEntity, ...]:
        """Return unique neighboring entities in stable identity order."""
        ...

    def find_paths(
        self,
        source_id: EntityId | str,
        target_id: EntityId | str,
        *,
        max_depth: int,
    ) -> tuple[GraphPath, ...]:
        """Return all simple directed paths within the required hop bound."""
        ...

    def get_traceability(
        self, entity_id: EntityId | str
    ) -> TraceabilitySubgraph:
        """Return the connected component formed by traceability relationships."""
        ...

    def validate_graph_integrity(self) -> GraphIntegrityReport:
        """Inspect endpoint and adjacency consistency without changing state."""
        ...
