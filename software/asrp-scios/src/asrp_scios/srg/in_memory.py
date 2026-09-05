"""Dependency-free in-memory Scientific Research Graph MVP.

Purpose:
    Store and query Sprint-002B scientific domain objects for Sprint-003.
Responsibilities:
    Register entities/relationships, maintain adjacency indexes, perform bounded
    deterministic queries, build traceability views, and validate graph health.
Inputs:
    Immutable ScientificEntity and ScientificRelationship domain instances.
Outputs:
    Domain objects, immutable paths/subgraphs, and integrity diagnostics.
Invariants:
    Stable IDs are unique; every relationship endpoint exists; no silent deletion.
Dependencies:
    ASRP-SciOS domain model, SRG protocol values, and Python standard library.
Limitations:
    State is process-local, non-durable, single-process, and reset on disposal.
Non-goals:
    Persistence, graph databases, branches, inference, APIs, UI, LLMs, or events.
"""

from __future__ import annotations

from collections import deque

from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.relationships import ScientificRelationship
from asrp_scios.domain.value_objects import EntityId, RelationshipType

from .errors import (
    DuplicateEntityError,
    DuplicateRelationshipError,
    EntityNotFoundError,
    InvalidGraphQueryError,
)
from .model import (
    GraphDirection,
    GraphIntegrityIssue,
    GraphIntegrityReport,
    GraphPath,
    TraceabilitySubgraph,
)


TRACEABILITY_RELATIONSHIP_TYPES = frozenset(
    {
        RelationshipType.DERIVES_FROM,
        RelationshipType.SUPPORTS,
        RelationshipType.CONTRADICTS,
        RelationshipType.VALIDATES,
        RelationshipType.DECIDED_BY,
        RelationshipType.USES_CONTEXT,
        RelationshipType.REFERENCES,
        RelationshipType.SUPERSEDES,
    }
)


def _identity_key(value: EntityId | str, field_name: str) -> str:
    """Normalize entity and aggregate-root IDs to their stable textual value."""
    if isinstance(value, EntityId):
        return str(value)
    if isinstance(value, str):
        try:
            return str(EntityId(value))
        except (TypeError, ValueError) as error:
            raise InvalidGraphQueryError(f"invalid {field_name}: {error}") from error
    raise InvalidGraphQueryError(f"{field_name} must be an EntityId or string")


def _relationship_type(
    value: RelationshipType | str | None,
) -> RelationshipType | None:
    """Normalize an optional canonical relationship type."""
    if value is None:
        return None
    if isinstance(value, RelationshipType):
        return value
    if isinstance(value, str):
        try:
            return RelationshipType(value)
        except ValueError as error:
            raise InvalidGraphQueryError(
                f"unknown relationship type: {value}"
            ) from error
    raise InvalidGraphQueryError(
        "relationship_type must be a RelationshipType or string"
    )


def _direction(value: GraphDirection | str) -> GraphDirection:
    """Normalize a direction value while producing a graph-specific error."""
    if isinstance(value, GraphDirection):
        return value
    if isinstance(value, str):
        try:
            return GraphDirection(value)
        except ValueError as error:
            raise InvalidGraphQueryError(f"unknown graph direction: {value}") from error
    raise InvalidGraphQueryError("direction must be a GraphDirection or string")


class InMemoryScientificResearchGraph:
    """Purpose: provide the operational in-memory SRG MVP.

    Inputs: frozen Sprint-002B entities and directed relationships.
    Outputs: deterministic immutable query results and integrity diagnostics.
    Invariants: entity and relationship IDs are unique and endpoints pre-exist.
    Non-goals: durable storage, history/branch semantics, event publication,
    inference, ranking, authorization, APIs, UI, and orchestration.

    Semantic duplicate edges are allowed when their relationship IDs differ;
    their provenance or rationale may represent distinct scientific assertions.
    Archived and deprecated entities remain registered and queryable. Lifecycle
    transitions belong to their domain aggregates, not this graph index.
    """

    __slots__ = ("_entities", "_relationships", "_outgoing", "_incoming")

    def __init__(self) -> None:
        self._entities: dict[str, ScientificEntity] = {}
        self._relationships: dict[str, ScientificRelationship] = {}
        self._outgoing: dict[str, list[str]] = {}
        self._incoming: dict[str, list[str]] = {}

    def register_entity(self, entity: ScientificEntity) -> None:
        """Register one entity without replacing a prior stable identity."""
        if not isinstance(entity, ScientificEntity):
            raise TypeError("entity must be a ScientificEntity")
        entity_key = str(entity.id)
        if entity_key in self._entities:
            raise DuplicateEntityError(f"entity is already registered: {entity_key}")
        self._entities[entity_key] = entity
        self._outgoing.setdefault(entity_key, [])
        self._incoming.setdefault(entity_key, [])

    def get_entity(self, entity_id: EntityId | str) -> ScientificEntity | None:
        """Return the registered entity or ``None`` for an unknown stable ID."""
        return self._entities.get(_identity_key(entity_id, "entity_id"))

    def add_relationship(self, relationship: ScientificRelationship) -> None:
        """Register a domain relationship after validating identity and endpoints."""
        if not isinstance(relationship, ScientificRelationship):
            raise TypeError("relationship must be a ScientificRelationship")
        relationship_key = str(relationship.relationship_id)
        if relationship_key in self._relationships:
            raise DuplicateRelationshipError(
                f"relationship is already registered: {relationship_key}"
            )
        source_key = str(relationship.source_entity_id)
        target_key = str(relationship.target_entity_id)
        if source_key not in self._entities:
            raise EntityNotFoundError(
                f"relationship source is not registered: {source_key}"
            )
        if target_key not in self._entities:
            raise EntityNotFoundError(
                f"relationship target is not registered: {target_key}"
            )
        self._relationships[relationship_key] = relationship
        self._outgoing[source_key].append(relationship_key)
        self._incoming[target_key].append(relationship_key)

    def get_relationship(
        self, relationship_id: EntityId | str
    ) -> ScientificRelationship | None:
        """Return one relationship by stable ID, or ``None`` when unknown."""
        return self._relationships.get(
            _identity_key(relationship_id, "relationship_id")
        )

    def get_relationships(
        self,
        *,
        entity_id: EntityId | str | None = None,
        source_id: EntityId | str | None = None,
        target_id: EntityId | str | None = None,
        relationship_type: RelationshipType | str | None = None,
        direction: GraphDirection | str | None = None,
    ) -> tuple[ScientificRelationship, ...]:
        """Return relationships matching every supplied filter.

        With ``entity_id`` and no direction, both directions are searched. An
        empty filter returns every relationship. IDs used as filters must refer
        to registered entities.
        """
        normalized_type = _relationship_type(relationship_type)
        entity_key = self._optional_existing_entity(entity_id, "entity_id")
        source_key = self._optional_existing_entity(source_id, "source_id")
        target_key = self._optional_existing_entity(target_id, "target_id")
        if direction is not None and entity_key is None:
            raise InvalidGraphQueryError("direction requires entity_id")
        normalized_direction = (
            _direction(direction) if direction is not None else GraphDirection.BOTH
        )

        if entity_key is None:
            candidate_keys = set(self._relationships)
        elif normalized_direction is GraphDirection.OUTGOING:
            candidate_keys = set(self._outgoing[entity_key])
        elif normalized_direction is GraphDirection.INCOMING:
            candidate_keys = set(self._incoming[entity_key])
        else:
            candidate_keys = set(self._outgoing[entity_key]) | set(
                self._incoming[entity_key]
            )

        matches: list[ScientificRelationship] = []
        for relationship_key in sorted(candidate_keys):
            relationship = self._relationships[relationship_key]
            if source_key is not None and str(relationship.source_entity_id) != source_key:
                continue
            if target_key is not None and str(relationship.target_entity_id) != target_key:
                continue
            if (
                normalized_type is not None
                and relationship.relationship_type is not normalized_type
            ):
                continue
            matches.append(relationship)
        return tuple(matches)

    def get_neighbors(
        self,
        entity_id: EntityId | str,
        *,
        relationship_type: RelationshipType | str | None = None,
        direction: GraphDirection | str = GraphDirection.BOTH,
    ) -> tuple[ScientificEntity, ...]:
        """Return unique adjacent entities in lexicographic stable-ID order."""
        entity_key = self._require_existing_entity(entity_id, "entity_id")
        normalized_direction = _direction(direction)
        relationships = self.get_relationships(
            entity_id=entity_key,
            relationship_type=relationship_type,
            direction=normalized_direction,
        )
        neighbor_keys: set[str] = set()
        for relationship in relationships:
            source_key = str(relationship.source_entity_id)
            target_key = str(relationship.target_entity_id)
            if normalized_direction in (GraphDirection.OUTGOING, GraphDirection.BOTH):
                if source_key == entity_key:
                    neighbor_keys.add(target_key)
            if normalized_direction in (GraphDirection.INCOMING, GraphDirection.BOTH):
                if target_key == entity_key:
                    neighbor_keys.add(source_key)
        return tuple(self._entities[key] for key in sorted(neighbor_keys))

    def find_paths(
        self,
        source_id: EntityId | str,
        target_id: EntityId | str,
        *,
        max_depth: int,
    ) -> tuple[GraphPath, ...]:
        """Return all simple directed paths up to ``max_depth`` relationship hops.

        Results are breadth-first, then lexicographic by relationship ID. This
        preserves stable tests while ensuring cycles cannot loop indefinitely.
        """
        source_key = self._require_existing_entity(source_id, "source_id")
        target_key = self._require_existing_entity(target_id, "target_id")
        if isinstance(max_depth, bool) or not isinstance(max_depth, int):
            raise InvalidGraphQueryError("max_depth must be an integer")
        if max_depth < 0:
            raise InvalidGraphQueryError("max_depth cannot be negative")
        if source_key == target_key:
            return (GraphPath((self._entities[source_key].id,)),)
        if max_depth == 0:
            return ()

        queue: deque[tuple[str, tuple[str, ...], tuple[str, ...]]] = deque(
            [(source_key, (source_key,), ())]
        )
        paths: list[GraphPath] = []
        while queue:
            current_key, entity_keys, relationship_keys = queue.popleft()
            if len(relationship_keys) >= max_depth:
                continue
            for relationship_key in sorted(self._outgoing[current_key]):
                relationship = self._relationships[relationship_key]
                next_key = str(relationship.target_entity_id)
                if next_key in entity_keys:
                    continue
                next_entity_keys = entity_keys + (next_key,)
                next_relationship_keys = relationship_keys + (relationship_key,)
                if next_key == target_key:
                    paths.append(
                        GraphPath(
                            entity_ids=tuple(
                                self._entities[key].id for key in next_entity_keys
                            ),
                            relationship_ids=tuple(
                                self._relationships[key].relationship_id
                                for key in next_relationship_keys
                            ),
                        )
                    )
                elif len(next_relationship_keys) < max_depth:
                    queue.append(
                        (next_key, next_entity_keys, next_relationship_keys)
                    )
        return tuple(paths)

    def get_traceability(
        self, entity_id: EntityId | str
    ) -> TraceabilitySubgraph:
        """Return the bidirectional traceability component around one entity."""
        root_key = self._require_existing_entity(entity_id, "entity_id")
        visited_entity_keys = {root_key}
        included_relationship_keys: set[str] = set()
        queue: deque[str] = deque([root_key])

        while queue:
            current_key = queue.popleft()
            relationship_keys = set(self._outgoing[current_key]) | set(
                self._incoming[current_key]
            )
            for relationship_key in sorted(relationship_keys):
                relationship = self._relationships[relationship_key]
                if relationship.relationship_type not in TRACEABILITY_RELATIONSHIP_TYPES:
                    continue
                included_relationship_keys.add(relationship_key)
                for neighbor_key in (
                    str(relationship.source_entity_id),
                    str(relationship.target_entity_id),
                ):
                    if neighbor_key not in visited_entity_keys:
                        visited_entity_keys.add(neighbor_key)
                        queue.append(neighbor_key)

        return TraceabilitySubgraph(
            root_entity_id=self._entities[root_key].id,
            entities=tuple(
                self._entities[key] for key in sorted(visited_entity_keys)
            ),
            relationships=tuple(
                self._relationships[key]
                for key in sorted(included_relationship_keys)
            ),
        )

    def validate_graph_integrity(self) -> GraphIntegrityReport:
        """Inspect IDs, endpoint existence, and both adjacency indexes."""
        issues: list[GraphIntegrityIssue] = []
        for entity_key, entity in sorted(self._entities.items()):
            if not isinstance(entity, ScientificEntity):
                issues.append(
                    GraphIntegrityIssue(
                        "INVALID_ENTITY_OBJECT",
                        "entity index contains a non-ScientificEntity value",
                        entity_id=entity_key,
                    )
                )
            elif str(entity.id) != entity_key:
                issues.append(
                    GraphIntegrityIssue(
                        "ENTITY_KEY_MISMATCH",
                        "entity index key does not match entity identity",
                        entity_id=entity_key,
                    )
                )

        for relationship_key, relationship in sorted(self._relationships.items()):
            if not isinstance(relationship, ScientificRelationship):
                issues.append(
                    GraphIntegrityIssue(
                        "INVALID_RELATIONSHIP_OBJECT",
                        "relationship index contains a non-relationship value",
                        relationship_id=relationship_key,
                    )
                )
                continue
            source_key = str(relationship.source_entity_id)
            target_key = str(relationship.target_entity_id)
            if str(relationship.relationship_id) != relationship_key:
                issues.append(
                    GraphIntegrityIssue(
                        "RELATIONSHIP_KEY_MISMATCH",
                        "relationship index key does not match relationship identity",
                        relationship_id=relationship_key,
                    )
                )
            if not isinstance(relationship.relationship_type, RelationshipType):
                issues.append(
                    GraphIntegrityIssue(
                        "INVALID_RELATIONSHIP_TYPE",
                        "relationship type is not canonical",
                        relationship_id=relationship_key,
                    )
                )
            if source_key not in self._entities:
                issues.append(
                    GraphIntegrityIssue(
                        "MISSING_SOURCE_ENTITY",
                        "relationship source is not registered",
                        entity_id=source_key,
                        relationship_id=relationship_key,
                    )
                )
            elif relationship_key not in self._outgoing.get(source_key, ()):
                issues.append(
                    GraphIntegrityIssue(
                        "MISSING_OUTGOING_INDEX",
                        "relationship is absent from its source adjacency index",
                        entity_id=source_key,
                        relationship_id=relationship_key,
                    )
                )
            if target_key not in self._entities:
                issues.append(
                    GraphIntegrityIssue(
                        "MISSING_TARGET_ENTITY",
                        "relationship target is not registered",
                        entity_id=target_key,
                        relationship_id=relationship_key,
                    )
                )
            elif relationship_key not in self._incoming.get(target_key, ()):
                issues.append(
                    GraphIntegrityIssue(
                        "MISSING_INCOMING_INDEX",
                        "relationship is absent from its target adjacency index",
                        entity_id=target_key,
                        relationship_id=relationship_key,
                    )
                )

        self._validate_adjacency_index(self._outgoing, "outgoing", issues)
        self._validate_adjacency_index(self._incoming, "incoming", issues)
        return GraphIntegrityReport(tuple(issues))

    def _validate_adjacency_index(
        self,
        index: dict[str, list[str]],
        direction: str,
        issues: list[GraphIntegrityIssue],
    ) -> None:
        for entity_key, relationship_keys in sorted(index.items()):
            if entity_key not in self._entities:
                issues.append(
                    GraphIntegrityIssue(
                        f"UNKNOWN_{direction.upper()}_INDEX_ENTITY",
                        f"{direction} index refers to an unknown entity",
                        entity_id=entity_key,
                    )
                )
            if len(relationship_keys) != len(set(relationship_keys)):
                issues.append(
                    GraphIntegrityIssue(
                        f"DUPLICATE_{direction.upper()}_INDEX_ENTRY",
                        f"{direction} index contains duplicate relationship IDs",
                        entity_id=entity_key,
                    )
                )
            for relationship_key in sorted(set(relationship_keys)):
                relationship = self._relationships.get(relationship_key)
                if relationship is None:
                    issues.append(
                        GraphIntegrityIssue(
                            f"UNKNOWN_{direction.upper()}_RELATIONSHIP",
                            f"{direction} index refers to an unknown relationship",
                            entity_id=entity_key,
                            relationship_id=relationship_key,
                        )
                    )
                    continue
                expected_key = str(
                    relationship.source_entity_id
                    if direction == "outgoing"
                    else relationship.target_entity_id
                )
                if expected_key != entity_key:
                    issues.append(
                        GraphIntegrityIssue(
                            f"INVALID_{direction.upper()}_INDEX_ENDPOINT",
                            f"{direction} index stores relationship under wrong entity",
                            entity_id=entity_key,
                            relationship_id=relationship_key,
                        )
                    )

    def _optional_existing_entity(
        self, value: EntityId | str | None, field_name: str
    ) -> str | None:
        if value is None:
            return None
        return self._require_existing_entity(value, field_name)

    def _require_existing_entity(
        self, value: EntityId | str, field_name: str
    ) -> str:
        entity_key = _identity_key(value, field_name)
        if entity_key not in self._entities:
            raise EntityNotFoundError(f"entity is not registered: {entity_key}")
        return entity_key
