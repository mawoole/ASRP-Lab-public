"""Sprint-003 acceptance tests for the in-memory Scientific Research Graph."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import unittest

from asrp_scios.domain.aggregates import ContextSnapshot, Hypothesis, ResearchDecision
from asrp_scios.domain.entities import Evidence, Observation, Unknown
from asrp_scios.domain.lifecycle import (
    EvidenceStatus,
    HypothesisStatus,
    LifecycleStatus,
    ResearchDecisionStatus,
)
from asrp_scios.domain.relationships import ScientificRelationship
from asrp_scios.domain.value_objects import (
    AggregateId,
    Confidence,
    ConfidenceLevel,
    DecisionType,
    EntityId,
    EvidenceDirection,
    EvidenceType,
    Provenance,
    RelationshipType,
    ScientificReference,
    Traceability,
    Version,
)
from asrp_scios.srg import (
    DuplicateEntityError,
    DuplicateRelationshipError,
    EntityNotFoundError,
    GraphDirection,
    InMemoryScientificResearchGraph,
    InvalidGraphQueryError,
    ScientificResearchGraph,
)


NOW = datetime(2026, 8, 7, 15, 0, tzinfo=timezone.utc)


def provenance() -> Provenance:
    return Provenance(
        creator="researcher-1",
        created_at=NOW,
        source="Sprint-003 test fixture",
        method="controlled construction",
    )


def traceability() -> Traceability:
    return Traceability(
        requirements=("Sprint-003",),
        decisions=("ADR-0002",),
        specifications=("RFC-0001", "ONT-001"),
        implementation_version="0.3.0",
    )


def entity_fields(
    identifier: EntityId, status: object = LifecycleStatus.ACTIVE
) -> dict[str, object]:
    return {
        "id": identifier,
        "title": f"Entity {identifier}",
        "description": "A domain-independent scientific graph fixture.",
        "status": status,
        "version": Version(1),
        "created_at": NOW,
        "updated_at": NOW,
        "created_by": "researcher-1",
        "provenance": provenance(),
        "traceability": traceability(),
    }


def observation(identifier: str, *, archived: bool = False) -> Observation:
    return Observation(
        **entity_fields(
            EntityId(identifier),
            LifecycleStatus.ARCHIVED if archived else LifecycleStatus.ACTIVE,
        ),
        observed_at=NOW,
        observation_source="Calibrated instrument",
    )


def relationship(
    identifier: str,
    source_id: EntityId,
    target_id: EntityId,
    relationship_type: RelationshipType,
) -> ScientificRelationship:
    return ScientificRelationship(
        relationship_id=EntityId(identifier),
        relationship_type=relationship_type,
        source_entity_id=source_id,
        target_entity_id=target_id,
        confidence=Confidence(
            ConfidenceLevel.PLAUSIBLE,
            "The relationship is explicit but awaiting further review.",
            NOW,
            score=0.6,
        ),
        provenance=provenance(),
        traceability=traceability(),
        created_at=NOW,
        created_by="researcher-1",
        rationale="The source record explicitly identifies this relationship.",
    )


class EntityRegistrationTests(unittest.TestCase):
    def test_empty_graph_and_unknown_entity_lookup(self) -> None:
        graph = InMemoryScientificResearchGraph()
        self.assertIsNone(graph.get_entity(EntityId("unknown")))
        self.assertEqual(graph.get_relationships(), ())
        self.assertTrue(graph.validate_graph_integrity().is_valid)

    def test_register_and_retrieve_entity_by_typed_or_text_id(self) -> None:
        graph = InMemoryScientificResearchGraph()
        entity = observation("observation-1")
        graph.register_entity(entity)
        self.assertIs(graph.get_entity(entity.id), entity)
        self.assertIs(graph.get_entity("observation-1"), entity)

    def test_aggregate_id_and_entity_id_share_one_stable_graph_identity(self) -> None:
        graph = InMemoryScientificResearchGraph()
        hypothesis = Hypothesis(
            **entity_fields(AggregateId("hypothesis-1"), HypothesisStatus.PROPOSED),
            statement="A measurable relation exists.",
            question_id=EntityId("question-1"),
        )
        graph.register_entity(hypothesis)
        self.assertIs(graph.get_entity(EntityId("hypothesis-1")), hypothesis)

    def test_duplicate_entity_id_fails_without_replacing_original(self) -> None:
        graph = InMemoryScientificResearchGraph()
        original = observation("observation-1")
        graph.register_entity(original)
        with self.assertRaises(DuplicateEntityError):
            graph.register_entity(observation("observation-1"))
        self.assertIs(graph.get_entity("observation-1"), original)

    def test_archived_entities_remain_registered_and_queryable(self) -> None:
        graph = InMemoryScientificResearchGraph()
        archived = observation("observation-archived", archived=True)
        graph.register_entity(archived)
        self.assertIs(graph.get_entity(archived.id), archived)
        self.assertIs(archived.status, LifecycleStatus.ARCHIVED)

    def test_first_class_scientific_entity_types_are_accepted(self) -> None:
        graph = InMemoryScientificResearchGraph()
        evidence = Evidence(
            **entity_fields(EntityId("evidence-1"), EvidenceStatus.COLLECTED),
            evidence_type=EvidenceType.EXPERIMENTAL,
            direction=EvidenceDirection.SUPPORTS,
            source_reference=ScientificReference(EntityId("observation-source")),
            method="Controlled measurement",
            confidence=Confidence(
                ConfidenceLevel.PLAUSIBLE,
                "Initial evidence is internally consistent.",
                NOW,
            ),
        )
        unknown = Unknown(
            **entity_fields(EntityId("unknown-1")),
            importance="This uncertainty may affect interpretation.",
        )
        decision = ResearchDecision(
            **entity_fields(
                AggregateId("decision-1"), ResearchDecisionStatus.PROPOSED
            ),
            decision_type=DecisionType.SCIENTIFIC,
        )
        context = ContextSnapshot(
            **entity_fields(AggregateId("context-1")),
            task_reference=EntityId("task-1"),
            context_data={"scope": "current experiment"},
        )
        for entity in (evidence, unknown, decision, context):
            graph.register_entity(entity)
            self.assertIs(graph.get_entity(entity.id), entity)


class RelationshipQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = InMemoryScientificResearchGraph()
        self.a = observation("entity-a")
        self.b = observation("entity-b")
        self.c = observation("entity-c")
        for entity in (self.c, self.a, self.b):
            self.graph.register_entity(entity)

    def test_add_relationship_requires_both_endpoints(self) -> None:
        missing_source = relationship(
            "relationship-1",
            EntityId("missing"),
            self.b.id,
            RelationshipType.SUPPORTS,
        )
        with self.assertRaisesRegex(EntityNotFoundError, "source"):
            self.graph.add_relationship(missing_source)

        missing_target = relationship(
            "relationship-2",
            self.a.id,
            EntityId("missing"),
            RelationshipType.SUPPORTS,
        )
        with self.assertRaisesRegex(EntityNotFoundError, "target"):
            self.graph.add_relationship(missing_target)

    def test_duplicate_relationship_identity_is_rejected(self) -> None:
        edge = relationship(
            "relationship-1", self.a.id, self.b.id, RelationshipType.SUPPORTS
        )
        self.graph.add_relationship(edge)
        with self.assertRaises(DuplicateRelationshipError):
            self.graph.add_relationship(edge)
        self.assertIs(self.graph.get_relationship(edge.relationship_id), edge)

    def test_distinct_assertions_may_share_endpoints_and_type(self) -> None:
        first = relationship(
            "relationship-1", self.a.id, self.b.id, RelationshipType.SUPPORTS
        )
        second = relationship(
            "relationship-2", self.a.id, self.b.id, RelationshipType.SUPPORTS
        )
        self.graph.add_relationship(first)
        self.graph.add_relationship(second)
        self.assertEqual(self.graph.get_relationships(source_id=self.a.id), (first, second))

    def test_relationship_queries_filter_direction_endpoints_and_type(self) -> None:
        outgoing_support = relationship(
            "relationship-2", self.a.id, self.b.id, RelationshipType.SUPPORTS
        )
        incoming_contradiction = relationship(
            "relationship-1", self.c.id, self.a.id, RelationshipType.CONTRADICTS
        )
        outgoing_reference = relationship(
            "relationship-3", self.a.id, self.c.id, RelationshipType.REFERENCES
        )
        for edge in (outgoing_support, incoming_contradiction, outgoing_reference):
            self.graph.add_relationship(edge)

        self.assertEqual(
            self.graph.get_relationships(entity_id=self.a.id),
            (incoming_contradiction, outgoing_support, outgoing_reference),
        )
        self.assertEqual(
            self.graph.get_relationships(
                entity_id=self.a.id, direction=GraphDirection.OUTGOING
            ),
            (outgoing_support, outgoing_reference),
        )
        self.assertEqual(
            self.graph.get_relationships(target_id=self.a.id),
            (incoming_contradiction,),
        )
        self.assertEqual(
            self.graph.get_relationships(relationship_type="supports"),
            (outgoing_support,),
        )

    def test_invalid_relationship_filter_and_direction_fail_clearly(self) -> None:
        with self.assertRaisesRegex(InvalidGraphQueryError, "relationship type"):
            self.graph.get_relationships(relationship_type="supported_by")
        with self.assertRaisesRegex(InvalidGraphQueryError, "direction requires"):
            self.graph.get_relationships(direction="outgoing")
        with self.assertRaisesRegex(InvalidGraphQueryError, "graph direction"):
            self.graph.get_neighbors(self.a.id, direction="sideways")

    def test_neighbor_queries_are_directional_filtered_unique_and_sorted(self) -> None:
        edges = (
            relationship(
                "relationship-3", self.a.id, self.c.id, RelationshipType.REFERENCES
            ),
            relationship(
                "relationship-1", self.a.id, self.b.id, RelationshipType.SUPPORTS
            ),
            relationship(
                "relationship-2", self.c.id, self.a.id, RelationshipType.SUPPORTS
            ),
            relationship(
                "relationship-4", self.a.id, self.b.id, RelationshipType.SUPPORTS
            ),
        )
        for edge in edges:
            self.graph.add_relationship(edge)
        self.assertEqual(
            tuple(entity.id for entity in self.graph.get_neighbors(self.a.id, direction="outgoing")),
            (self.b.id, self.c.id),
        )
        self.assertEqual(
            tuple(entity.id for entity in self.graph.get_neighbors(self.a.id, direction="incoming")),
            (self.c.id,),
        )
        self.assertEqual(
            tuple(
                entity.id
                for entity in self.graph.get_neighbors(
                    self.a.id,
                    direction="both",
                    relationship_type=RelationshipType.SUPPORTS,
                )
            ),
            (self.b.id, self.c.id),
        )


class PathAndTraceabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = InMemoryScientificResearchGraph()
        self.a = observation("entity-a")
        self.b = observation("entity-b")
        self.c = observation("entity-c")
        self.d = observation("entity-d")
        for entity in (self.a, self.b, self.c, self.d):
            self.graph.register_entity(entity)

    def test_path_query_finds_direct_and_multihop_paths_deterministically(self) -> None:
        edges = (
            relationship("relationship-1", self.a.id, self.b.id, RelationshipType.DERIVES_FROM),
            relationship("relationship-2", self.b.id, self.c.id, RelationshipType.SUPPORTS),
            relationship("relationship-3", self.a.id, self.c.id, RelationshipType.REFERENCES),
        )
        for edge in edges:
            self.graph.add_relationship(edge)
        paths = self.graph.find_paths(self.a.id, self.c.id, max_depth=2)
        self.assertEqual(tuple(path.depth for path in paths), (1, 2))
        self.assertEqual(paths[0].entity_ids, (self.a.id, self.c.id))
        self.assertEqual(paths[1].entity_ids, (self.a.id, self.b.id, self.c.id))
        self.assertEqual(
            self.graph.find_paths(self.a.id, self.c.id, max_depth=1),
            (paths[0],),
        )

    def test_path_query_returns_empty_for_disconnected_or_insufficient_depth(self) -> None:
        self.graph.add_relationship(
            relationship("relationship-1", self.a.id, self.b.id, RelationshipType.DERIVES_FROM)
        )
        self.graph.add_relationship(
            relationship("relationship-2", self.b.id, self.c.id, RelationshipType.SUPPORTS)
        )
        self.assertEqual(self.graph.find_paths(self.a.id, self.d.id, max_depth=3), ())
        self.assertEqual(self.graph.find_paths(self.a.id, self.c.id, max_depth=1), ())

    def test_path_query_handles_cycles_and_validates_bounds(self) -> None:
        for edge in (
            relationship("relationship-1", self.a.id, self.b.id, RelationshipType.DERIVES_FROM),
            relationship("relationship-2", self.b.id, self.a.id, RelationshipType.REFERENCES),
            relationship("relationship-3", self.b.id, self.c.id, RelationshipType.SUPPORTS),
        ):
            self.graph.add_relationship(edge)
        paths = self.graph.find_paths(self.a.id, self.c.id, max_depth=5)
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].entity_ids, (self.a.id, self.b.id, self.c.id))
        with self.assertRaisesRegex(InvalidGraphQueryError, "negative"):
            self.graph.find_paths(self.a.id, self.c.id, max_depth=-1)

    def test_zero_depth_self_path_is_the_only_trivial_path(self) -> None:
        paths = self.graph.find_paths(self.a.id, self.a.id, max_depth=0)
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].entity_ids, (self.a.id,))
        self.assertEqual(paths[0].relationship_ids, ())

    def test_traceability_query_preserves_types_directions_and_excludes_other_edges(self) -> None:
        evidence = self.a
        hypothesis = self.b
        decision = self.c
        context = self.d
        unrelated = observation("entity-unrelated")
        self.graph.register_entity(unrelated)
        trace_edges = (
            relationship("relationship-1", evidence.id, hypothesis.id, RelationshipType.SUPPORTS),
            relationship("relationship-2", hypothesis.id, decision.id, RelationshipType.DECIDED_BY),
            relationship("relationship-3", hypothesis.id, context.id, RelationshipType.USES_CONTEXT),
        )
        non_trace_edge = relationship(
            "relationship-4", unrelated.id, hypothesis.id, RelationshipType.GENERATES
        )
        for edge in trace_edges + (non_trace_edge,):
            self.graph.add_relationship(edge)
        result = self.graph.get_traceability(hypothesis.id)
        self.assertEqual(
            tuple(str(entity.id) for entity in result.entities),
            ("entity-a", "entity-b", "entity-c", "entity-d"),
        )
        self.assertEqual(result.relationships, trace_edges)
        self.assertEqual(
            result.relationships[0].source_entity_id,
            evidence.id,
        )


class IntegrityAndArchitectureTests(unittest.TestCase):
    def test_healthy_graph_validates_and_corrupt_endpoint_is_detected(self) -> None:
        graph = InMemoryScientificResearchGraph()
        source = observation("source")
        target = observation("target")
        graph.register_entity(source)
        graph.register_entity(target)
        valid_edge = relationship(
            "relationship-valid", source.id, target.id, RelationshipType.SUPPORTS
        )
        graph.add_relationship(valid_edge)
        self.assertTrue(graph.validate_graph_integrity().is_valid)

        broken_edge = relationship(
            "relationship-broken",
            source.id,
            EntityId("missing"),
            RelationshipType.CONTRADICTS,
        )
        graph._relationships["relationship-broken"] = broken_edge
        report = graph.validate_graph_integrity()
        self.assertFalse(report.is_valid)
        self.assertIn("MISSING_TARGET_ENTITY", {issue.code for issue in report.issues})

    def test_implementation_satisfies_mvp_protocol(self) -> None:
        self.assertIsInstance(InMemoryScientificResearchGraph(), ScientificResearchGraph)

    def test_srg_source_has_no_prohibited_dependencies_or_program_leakage(self) -> None:
        source_root = Path(__file__).parents[1] / "src" / "asrp_scios" / "srg"
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in source_root.rglob("*.py")
        ).lower()
        forbidden = (
            "import sqlalchemy",
            "import networkx",
            "import neo4j",
            "import rdflib",
            "import fastapi",
            "import openai",
            "asrp_scios.kernel",
            "asrp_scios.eventing",
            "rm-x",
            "regenerative medicine",
        )
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
