"""Sprint-004 acceptance tests for the Context Engineering MVP."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path
import unittest

from asrp_scios.context import (
    ContextQualityResult,
    ContextRequest,
    ContextSelectionPolicy,
    ContextSnapshotGenerator,
    InvalidContextRequestError,
    InvalidContextSnapshotError,
)
from asrp_scios.domain.aggregates import (
    Hypothesis,
    ResearchDecision,
    ScientificQuestion,
)
from asrp_scios.domain.entities import (
    Evidence,
    KnowledgeItem,
    Observation,
    Unknown,
)
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
from asrp_scios.srg import InMemoryScientificResearchGraph


NOW = datetime(2026, 8, 7, 16, 0, tzinfo=timezone.utc)


def provenance() -> Provenance:
    return Provenance(
        creator="researcher-1",
        created_at=NOW,
        source="Sprint-004 controlled fixture",
        method="explicit test construction",
        input_entities=("question-1",),
    )


def traceability() -> Traceability:
    return Traceability(
        requirements=("ONT-001", "CAP-001"),
        decisions=("ADR-0002",),
        specifications=("Sprint-004",),
        implementation_version="0.4.0",
    )


def entity_fields(
    identifier: EntityId, status: object = LifecycleStatus.ACTIVE
) -> dict[str, object]:
    return {
        "id": identifier,
        "title": f"Entity {identifier}",
        "description": "A domain-independent Context Engineering fixture.",
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


def question(identifier: str = "question-1") -> ScientificQuestion:
    return ScientificQuestion(
        **entity_fields(AggregateId(identifier)),
        statement="Which measurable relation explains the observation?",
    )


def hypothesis(identifier: str = "hypothesis-1") -> Hypothesis:
    return Hypothesis(
        **entity_fields(AggregateId(identifier), HypothesisStatus.PROPOSED),
        statement="A measurable relation exists.",
        question_id=EntityId("question-1"),
    )


def evidence(identifier: str = "evidence-1", *, archived: bool = False) -> Evidence:
    return Evidence(
        **entity_fields(
            EntityId(identifier),
            EvidenceStatus.ARCHIVED if archived else EvidenceStatus.COLLECTED,
        ),
        evidence_type=EvidenceType.EXPERIMENTAL,
        direction=EvidenceDirection.SUPPORTS,
        source_reference=ScientificReference(EntityId("observation-source")),
        method="Controlled measurement",
        confidence=Confidence(
            ConfidenceLevel.PLAUSIBLE,
            "The measurement is internally consistent.",
            NOW,
            score=0.6,
        ),
        limitations=("The sample size is bounded.",),
    )


def unknown(identifier: str = "unknown-1") -> Unknown:
    return Unknown(
        **entity_fields(EntityId(identifier)),
        importance="This uncertainty may affect interpretation.",
        proposed_investigations=("Repeat the controlled measurement.",),
    )


def decision(identifier: str = "decision-1") -> ResearchDecision:
    return ResearchDecision(
        **entity_fields(
            AggregateId(identifier), ResearchDecisionStatus.PROPOSED
        ),
        decision_type=DecisionType.SCIENTIFIC,
        limitations=("The decision remains under review.",),
    )


def knowledge(identifier: str = "knowledge-1") -> KnowledgeItem:
    return KnowledgeItem(**entity_fields(EntityId(identifier)))


def relationship(
    identifier: str,
    source_id: EntityId,
    target_id: EntityId,
    relationship_type: RelationshipType,
    *,
    archived: bool = False,
) -> ScientificRelationship:
    return ScientificRelationship(
        relationship_id=EntityId(identifier),
        relationship_type=relationship_type,
        source_entity_id=source_id,
        target_entity_id=target_id,
        confidence=Confidence(
            ConfidenceLevel.PLAUSIBLE,
            "The source explicitly records the relationship.",
            NOW,
            score=0.6,
        ),
        provenance=provenance(),
        traceability=traceability(),
        created_at=NOW,
        created_by="researcher-1",
        rationale="The relationship is explicit in the scientific record.",
        status=LifecycleStatus.ARCHIVED if archived else LifecycleStatus.ACTIVE,
    )


def request(
    *seed_ids: str,
    max_depth: int = 2,
    max_entities: int = 20,
    filters: tuple[RelationshipType, ...] = (),
    include_archived: bool = False,
) -> ContextRequest:
    return ContextRequest(
        request_id=EntityId("request-1"),
        task_id=EntityId("task-1"),
        purpose="Resume a traceable scientific review.",
        seed_entity_ids=tuple(EntityId(value) for value in seed_ids),
        max_depth=max_depth,
        max_entities=max_entities,
        relationship_type_filters=filters,
        include_archived=include_archived,
        generated_by="codex",
    )


def graph_with(
    entities: tuple[object, ...], relationships: tuple[ScientificRelationship, ...]
) -> InMemoryScientificResearchGraph:
    graph = InMemoryScientificResearchGraph()
    for entity in entities:
        graph.register_entity(entity)  # type: ignore[arg-type]
    for edge in relationships:
        graph.add_relationship(edge)
    return graph


class ContextRequestTests(unittest.TestCase):
    def test_request_is_task_oriented_and_normalizes_deterministic_inputs(self) -> None:
        value = ContextRequest(
            request_id=EntityId("request-1"),
            mission_id=EntityId("mission-1"),
            purpose="  Recover scientific context.  ",
            seed_entity_ids=(EntityId("seed-b"), EntityId("seed-a")),
            generated_by="  codex  ",
            relationship_type_filters=(
                RelationshipType.SUPPORTS,
                RelationshipType.DECIDED_BY,
                RelationshipType.SUPPORTS,
            ),
        )
        self.assertEqual(tuple(map(str, value.seed_entity_ids)), ("seed-a", "seed-b"))
        self.assertEqual(
            value.relationship_type_filters,
            (RelationshipType.DECIDED_BY, RelationshipType.SUPPORTS),
        )
        self.assertEqual(value.purpose, "Recover scientific context.")

    def test_request_rejects_empty_seeds_and_invalid_bounds(self) -> None:
        with self.assertRaisesRegex(InvalidContextRequestError, "cannot be empty"):
            request()
        with self.assertRaisesRegex(InvalidContextRequestError, "max_depth"):
            request("seed-1", max_depth=-1)
        with self.assertRaisesRegex(InvalidContextRequestError, "max_entities"):
            request("seed-1", "seed-2", max_entities=1)
        with self.assertRaisesRegex(InvalidContextRequestError, "task or mission"):
            ContextRequest(
                request_id=EntityId("request-1"),
                purpose="Recover context.",
                seed_entity_ids=(EntityId("seed-1"),),
                generated_by="codex",
            )


class ContextGenerationTests(unittest.TestCase):
    def test_generation_uses_existing_snapshot_and_preserves_traceability(self) -> None:
        q, h, e, d, u = question(), hypothesis(), evidence(), decision(), unknown()
        edges = (
            relationship("r-generate", q.id, h.id, RelationshipType.GENERATES),
            relationship("r-support", e.id, h.id, RelationshipType.SUPPORTS),
            relationship("r-decision", h.id, d.id, RelationshipType.DECIDED_BY),
            relationship("r-unknown", u.id, q.id, RelationshipType.DEPENDS_ON),
        )
        graph = graph_with((u, d, e, h, q), edges)
        generator = ContextSnapshotGenerator(clock=lambda: NOW)

        snapshot = generator.generate_context_snapshot(request("question-1"), graph)

        self.assertEqual(snapshot.entity_type, "ContextSnapshot")
        self.assertEqual(snapshot.task_reference, EntityId("task-1"))
        self.assertEqual(snapshot.context_data["key_questions"], ("question-1",))
        self.assertEqual(snapshot.context_data["key_hypotheses"], ("hypothesis-1",))
        self.assertEqual(snapshot.context_data["key_evidence"], ("evidence-1",))
        self.assertEqual(snapshot.context_data["key_decisions"], ("decision-1",))
        self.assertEqual(snapshot.context_data["key_unknowns"], ("unknown-1",))
        self.assertEqual(
            snapshot.context_data["next_actions"],
            ("Repeat the controlled measurement.",),
        )
        self.assertIn("The sample size is bounded.", snapshot.context_data["limitations"])
        self.assertEqual(snapshot.provenance.source, "Scientific Research Graph")
        self.assertEqual(snapshot.traceability.implementation_version, "0.4.0")
        selected = snapshot.context_data["selected_entities"]
        evidence_row = next(
            value for value in selected if value["entity_id"] == "evidence-1"
        )
        self.assertEqual(
            evidence_row["provenance"]["source"], "Sprint-004 controlled fixture"
        )

    def test_missing_seeds_are_explicit_and_reduce_seed_coverage(self) -> None:
        graph = graph_with((question(),), ())
        generator = ContextSnapshotGenerator(clock=lambda: NOW)
        value = request("question-1", "question-missing")
        snapshot = generator.generate_context_snapshot(value, graph)
        quality = generator.compute_context_quality(snapshot, value)
        explanation = generator.explain_context_selection(snapshot)
        self.assertEqual(quality.seed_coverage, 0.5)
        self.assertIn("question-missing", quality.warnings[0])
        self.assertEqual(
            explanation.missing_seed_entity_ids, (EntityId("question-missing"),)
        )

    def test_max_depth_bounds_expansion(self) -> None:
        q, h, e = question(), hypothesis(), evidence()
        graph = graph_with(
            (q, h, e),
            (
                relationship("r-1", q.id, h.id, RelationshipType.GENERATES),
                relationship("r-2", e.id, h.id, RelationshipType.SUPPORTS),
            ),
        )
        generator = ContextSnapshotGenerator(clock=lambda: NOW)
        depth_one = generator.select_relevant_entities(
            request("question-1", max_depth=1), graph
        )
        depth_two = generator.select_relevant_entities(
            request("question-1", max_depth=2), graph
        )
        self.assertEqual(tuple(str(value.id) for value in depth_one), (
            "question-1",
            "hypothesis-1",
        ))
        self.assertEqual(
            tuple(str(value.id) for value in depth_two),
            ("question-1", "evidence-1", "hypothesis-1"),
        )

    def test_max_entities_applies_type_priority_before_identity(self) -> None:
        q, d, e, u = question(), decision("decision-z"), evidence("evidence-z"), unknown()
        extra = observation("observation-a")
        edges = (
            relationship("r-1", q.id, d.id, RelationshipType.DECIDED_BY),
            relationship("r-2", e.id, q.id, RelationshipType.SUPPORTS),
            relationship("r-3", u.id, q.id, RelationshipType.DEPENDS_ON),
            relationship("r-4", extra.id, q.id, RelationshipType.REFERENCES),
        )
        graph = graph_with((extra, u, e, d, q), edges)
        selected = ContextSnapshotGenerator().select_relevant_entities(
            request("question-1", max_depth=1, max_entities=3), graph
        )
        self.assertEqual(
            tuple(str(value.id) for value in selected),
            ("question-1", "decision-z", "evidence-z"),
        )

    def test_equal_priority_entities_use_stable_identity(self) -> None:
        q, evidence_b, evidence_a = question(), evidence("evidence-b"), evidence(
            "evidence-a"
        )
        graph = graph_with(
            (evidence_b, q, evidence_a),
            (
                relationship("r-b", evidence_b.id, q.id, RelationshipType.SUPPORTS),
                relationship("r-a", evidence_a.id, q.id, RelationshipType.SUPPORTS),
            ),
        )
        selected = ContextSnapshotGenerator().select_relevant_entities(
            request("question-1", max_depth=1, max_entities=2), graph
        )
        self.assertEqual(
            tuple(str(value.id) for value in selected),
            ("question-1", "evidence-a"),
        )

    def test_relationships_are_priority_ordered_and_endpoint_closed(self) -> None:
        q, h, e, d = question(), hypothesis(), evidence(), decision()
        excluded = observation("observation-excluded")
        graph = graph_with(
            (excluded, d, e, h, q),
            (
                relationship("r-z", h.id, d.id, RelationshipType.DECIDED_BY),
                relationship("r-y", e.id, h.id, RelationshipType.SUPPORTS),
                relationship("r-a", q.id, h.id, RelationshipType.GENERATES),
                relationship("r-out", excluded.id, e.id, RelationshipType.OBSERVES),
            ),
        )
        value = request("question-1", max_depth=2, max_entities=4)
        relationships = ContextSnapshotGenerator().select_relevant_relationships(
            value, graph
        )
        self.assertEqual(
            tuple(edge.relationship_type for edge in relationships),
            (
                RelationshipType.DECIDED_BY,
                RelationshipType.SUPPORTS,
                RelationshipType.GENERATES,
            ),
        )
        selected_ids = {
            str(value.id)
            for value in ContextSnapshotGenerator().select_relevant_entities(
                value, graph
            )
        }
        self.assertTrue(
            all(
                str(edge.source_entity_id) in selected_ids
                and str(edge.target_entity_id) in selected_ids
                for edge in relationships
            )
        )

    def test_relationship_filter_limits_expansion_and_closure(self) -> None:
        q, e, u = question(), evidence(), unknown()
        graph = graph_with(
            (u, e, q),
            (
                relationship("r-support", e.id, q.id, RelationshipType.SUPPORTS),
                relationship("r-depends", u.id, q.id, RelationshipType.DEPENDS_ON),
            ),
        )
        value = request(
            "question-1", max_depth=1, filters=(RelationshipType.SUPPORTS,)
        )
        generator = ContextSnapshotGenerator()
        self.assertEqual(
            tuple(str(item.id) for item in generator.select_relevant_entities(value, graph)),
            ("question-1", "evidence-1"),
        )
        self.assertEqual(
            tuple(
                item.relationship_type
                for item in generator.select_relevant_relationships(value, graph)
            ),
            (RelationshipType.SUPPORTS,),
        )

    def test_historical_entities_require_request_or_traceability(self) -> None:
        q = question()
        archived_observation = observation("observation-archived", archived=True)
        archived_evidence = evidence("evidence-archived", archived=True)
        graph = graph_with(
            (archived_observation, archived_evidence, q),
            (
                relationship(
                    "r-belongs",
                    archived_observation.id,
                    q.id,
                    RelationshipType.BELONGS_TO,
                ),
                relationship(
                    "r-support",
                    archived_evidence.id,
                    q.id,
                    RelationshipType.SUPPORTS,
                ),
            ),
        )
        generator = ContextSnapshotGenerator()
        default_ids = tuple(
            str(value.id)
            for value in generator.select_relevant_entities(
                request("question-1", max_depth=1), graph
            )
        )
        explicit_ids = tuple(
            str(value.id)
            for value in generator.select_relevant_entities(
                request("question-1", max_depth=1, include_archived=True), graph
            )
        )
        self.assertEqual(default_ids, ("question-1", "evidence-archived"))
        self.assertEqual(
            explicit_ids,
            ("question-1", "evidence-archived", "observation-archived"),
        )

    def test_fixed_clock_makes_complete_output_deterministic(self) -> None:
        q, e, d = question(), evidence(), decision()
        edges = (
            relationship("r-2", e.id, q.id, RelationshipType.SUPPORTS),
            relationship("r-1", q.id, d.id, RelationshipType.DECIDED_BY),
        )
        first_graph = graph_with((e, q, d), edges)
        second_graph = graph_with((d, q, e), tuple(reversed(edges)))
        generator = ContextSnapshotGenerator(clock=lambda: NOW)
        value = request("question-1", max_depth=1)
        self.assertEqual(
            generator.generate_context_snapshot(value, first_graph),
            generator.generate_context_snapshot(value, second_graph),
        )


class ContextQualityAndValidationTests(unittest.TestCase):
    def test_complete_reachable_context_scores_one(self) -> None:
        q, h, e, d, u = question(), hypothesis(), evidence(), decision(), unknown()
        graph = graph_with(
            (q, h, e, d, u),
            (
                relationship("r-1", q.id, h.id, RelationshipType.GENERATES),
                relationship("r-2", e.id, h.id, RelationshipType.SUPPORTS),
                relationship("r-3", h.id, d.id, RelationshipType.DECIDED_BY),
                relationship("r-4", u.id, q.id, RelationshipType.DEPENDS_ON),
            ),
        )
        value = request("question-1", max_depth=2)
        generator = ContextSnapshotGenerator(clock=lambda: NOW)
        snapshot = generator.generate_context_snapshot(value, graph)
        quality = generator.compute_context_quality(snapshot, value)
        self.assertEqual(
            quality,
            ContextQualityResult.from_context_data(snapshot.context_data["quality"]),
        )
        self.assertEqual(quality.completeness_score, 1.0)
        self.assertEqual(quality.warnings, ())

    def test_isolated_seed_has_explicit_quality_warnings(self) -> None:
        graph = graph_with((question(),), ())
        value = request("question-1", max_depth=0)
        generator = ContextSnapshotGenerator(clock=lambda: NOW)
        quality = generator.compute_context_quality(
            generator.generate_context_snapshot(value, graph), value
        )
        self.assertEqual(quality.completeness_score, 0.3)
        self.assertTrue(any("max_depth is zero" in item for item in quality.warnings))
        self.assertTrue(any("No relationships" in item for item in quality.warnings))
        self.assertTrue(any("No Evidence" in item for item in quality.warnings))
        self.assertTrue(any("No ResearchDecision" in item for item in quality.warnings))

    def test_truncation_reduces_coverage_and_is_explained(self) -> None:
        q, d, e, u = question(), decision(), evidence(), unknown()
        graph = graph_with(
            (q, d, e, u),
            (
                relationship("r-1", q.id, d.id, RelationshipType.DECIDED_BY),
                relationship("r-2", e.id, q.id, RelationshipType.SUPPORTS),
                relationship("r-3", u.id, q.id, RelationshipType.DEPENDS_ON),
            ),
        )
        value = request("question-1", max_depth=1, max_entities=2)
        generator = ContextSnapshotGenerator(clock=lambda: NOW)
        snapshot = generator.generate_context_snapshot(value, graph)
        quality = generator.compute_context_quality(snapshot, value)
        explanation = generator.explain_context_selection(snapshot)
        self.assertLess(quality.completeness_score, 1.0)
        self.assertEqual(
            explanation.truncated_entity_ids,
            (EntityId("evidence-1"), EntityId("unknown-1")),
        )
        self.assertTrue(any("truncated 2" in item for item in quality.warnings))

    def test_snapshot_is_deeply_immutable_and_validates_relationship_closure(self) -> None:
        q, e = question(), evidence()
        graph = graph_with(
            (q, e),
            (relationship("r-1", e.id, q.id, RelationshipType.SUPPORTS),),
        )
        generator = ContextSnapshotGenerator(clock=lambda: NOW)
        snapshot = generator.generate_context_snapshot(
            request("question-1", max_depth=1), graph
        )
        with self.assertRaises(FrozenInstanceError):
            snapshot.title = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            snapshot.context_data["quality"] = {}  # type: ignore[index]

        invalid_data = dict(snapshot.context_data)
        invalid_data["selected_relationships"] = (
            {
                "relationship_id": "relationship-invalid",
                "relationship_type": "supports",
                "source_entity_id": "question-1",
                "target_entity_id": "entity-not-selected",
            },
        )
        invalid = replace(
            snapshot,
            context_data=invalid_data,
            relationships=(EntityId("relationship-invalid"),),
        )
        with self.assertRaisesRegex(InvalidContextSnapshotError, "endpoint"):
            generator.validate_context_snapshot(invalid)

    def test_policy_exposes_canonical_priorities(self) -> None:
        policy = ContextSelectionPolicy()
        self.assertEqual(policy.entity_type_priority[:3], (
            "ResearchDecision",
            "Evidence",
            "Unknown",
        ))
        self.assertEqual(
            policy.relationship_type_priority[:3],
            (
                RelationshipType.DECIDED_BY,
                RelationshipType.SUPPORTS,
                RelationshipType.CONTRADICTS,
            ),
        )


class ContextArchitectureBoundaryTests(unittest.TestCase):
    def test_context_source_has_no_prohibited_dependencies_or_program_leakage(self) -> None:
        source_root = (
            Path(__file__).parents[1] / "src" / "asrp_scios" / "context"
        )
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in source_root.rglob("*.py")
        ).lower()
        forbidden = (
            "import openai",
            "import sqlalchemy",
            "import requests",
            "import fastapi",
            "import django",
            "import networkx",
            "import neo4j",
            "import chromadb",
            "asrp_scios.kernel",
            "asrp_scios.eventing",
            "rm-x",
            "regenerative medicine",
        )
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
