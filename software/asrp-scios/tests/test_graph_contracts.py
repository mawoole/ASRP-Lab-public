"""Tests for RFC-0001 graph records and structural interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import unittest

from asrp_scios.contracts import (
    ConfidenceAssessment,
    GraphQuery,
    GraphRecord,
    Provenance,
    ResearchBranch,
    ScientificEntity,
    ScientificRelationship,
    ScientificResearchGraph,
    Traceability,
)


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


def traceability() -> Traceability:
    return Traceability(
        requirements=("Sprint-001",),
        decisions=("ADR-0002",),
        specifications=("ARC-000", "ARC-001", "RFC-0001"),
        implementation_version="0.1.0",
    )


def provenance() -> Provenance:
    return Provenance(creator="researcher-1", created_at=NOW, source="laboratory")


def confidence() -> ConfidenceAssessment:
    return ConfidenceAssessment(
        score=0.4,
        rationale="Initial evidence is incomplete.",
        assessed_at=NOW,
        limitations=("Not independently reproduced",),
    )


class StructuralGraph:
    def record_entity(self, entity: ScientificEntity, *, branch_id: str) -> None:
        return None

    def record_relationship(
        self, relationship: ScientificRelationship, *, branch_id: str
    ) -> None:
        return None

    def get_entity(
        self,
        entity_id: str,
        *,
        version: int | None = None,
        branch_id: str | None = None,
    ) -> ScientificEntity | None:
        return None

    def query(self, query: GraphQuery) -> Sequence[GraphRecord]:
        return ()

    def create_branch(self, branch: ResearchBranch) -> None:
        return None

    def merge_branch(
        self, *, source_branch_id: str, target_branch_id: str, traceability: Traceability
    ) -> None:
        return None


class GraphContractTests(unittest.TestCase):
    def test_entity_is_versioned_and_deeply_immutable(self) -> None:
        content = {"statement": "A testable claim", "labels": ["candidate"]}
        entity = ScientificEntity(
            entity_id="hypothesis-1",
            entity_type="Hypothesis",
            version=1,
            content=content,
            provenance=provenance(),
            confidence=confidence(),
            traceability=traceability(),
        )
        content["labels"].append("mutated")  # type: ignore[union-attr]

        self.assertEqual(entity.content["labels"], ("candidate",))
        with self.assertRaises(TypeError):
            entity.content["statement"] = "changed"  # type: ignore[index]

    def test_entity_requires_positive_immutable_version(self) -> None:
        with self.assertRaises(ValueError):
            ScientificEntity(
                entity_id="unknown-1",
                entity_type="Unknown",
                version=0,
                content={"description": "Unresolved"},
                provenance=provenance(),
                confidence=confidence(),
                traceability=traceability(),
            )

    def test_confidence_is_bounded_and_justified(self) -> None:
        with self.assertRaises(ValueError):
            ConfidenceAssessment(score=1.1, rationale="Too high", assessed_at=NOW)
        with self.assertRaises(ValueError):
            ConfidenceAssessment(score=0.2, rationale=" ", assessed_at=NOW)

    def test_branch_and_query_are_database_independent(self) -> None:
        branch = ResearchBranch(
            branch_id="branch-alternative",
            name="Alternative hypothesis",
            created_at=NOW,
            parent_branch_id="main",
        )
        query = GraphQuery(
            start_entity_id="hypothesis-1",
            relationship_types=("supports", "contradicts"),
            branch_id=branch.branch_id,
            include_history=True,
        )

        self.assertEqual(query.relationship_types, ("supports", "contradicts"))
        self.assertTrue(query.include_history)

    def test_graph_implementations_are_structurally_replaceable(self) -> None:
        self.assertIsInstance(StructuralGraph(), ScientificResearchGraph)


if __name__ == "__main__":
    unittest.main()

