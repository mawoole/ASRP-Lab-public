"""Tests for RFC-0002 and API-0001 scientific contracts."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
import unittest

from asrp_scios.contracts import (
    CognitiveSystemManifest,
    ConfidenceAssessment,
    MethodologicalAssessment,
    MethodologicalReviewRequest,
    Provenance,
    QualityGateResult,
    ScientificCognitiveSystem,
    ScientificInput,
    ScientificMethodEngine,
    ScientificOutput,
    ScientificOutputMetadata,
    Traceability,
)


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


def traceability() -> Traceability:
    return Traceability(
        requirements=("Sprint-001",),
        decisions=("ADR-0001", "ADR-0002"),
        specifications=("ARC-001", "RFC-0002", "API-0001"),
        implementation_version="0.1.0",
    )


def confidence() -> ConfidenceAssessment:
    return ConfidenceAssessment(
        score=0.7,
        rationale="The declared evidence supports this assessment.",
        assessed_at=NOW,
        assumptions=("Evidence references are accessible",),
        limitations=("No replication result is available",),
    )


class StructuralMethodEngine:
    def evaluate(
        self, request: MethodologicalReviewRequest
    ) -> MethodologicalAssessment:
        return MethodologicalAssessment(
            activity_id=request.activity_id,
            reviewer="structural-engine",
            generated_at=NOW,
            gate_results=(),
            recommendations=(),
            traceability=request.traceability,
        )


class StructuralCognitiveSystem:
    manifest = CognitiveSystemManifest(
        identifier="test-system",
        name="Test System",
        version="1.0.0",
        domain="domain-independent",
        supported_capabilities=("review",),
        dependencies=(),
        supported_scientific_programs=(),
        status="test",
    )

    def process(self, scientific_input: ScientificInput) -> Sequence[ScientificOutput]:
        return ()


class ScientificContractTests(unittest.TestCase):
    def test_method_assessment_cannot_disable_human_review(self) -> None:
        with self.assertRaisesRegex(ValueError, "human review"):
            MethodologicalAssessment(
                activity_id="activity-1",
                reviewer="method-engine",
                generated_at=NOW,
                gate_results=(),
                recommendations=(),
                traceability=traceability(),
                requires_human_review=False,
            )

    def test_quality_gate_preserves_explainability_fields(self) -> None:
        result = QualityGateResult(
            gate_id="falsifiability",
            passed=True,
            rationale="A contradictory observation is specified.",
            confidence=confidence(),
            supporting_evidence=("evidence-1",),
            assumptions=("Measurement is calibrated",),
            limitations=("Single instrument",),
        )

        self.assertEqual(result.confidence.score, 0.7)
        self.assertEqual(result.limitations, ("Single instrument",))

    def test_cognitive_input_requires_a_scientific_question(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one question"):
            ScientificInput(
                scientific_questions=(),
                scientific_context={},
                knowledge_references=(),
                constraints=(),
                objectives=(),
                available_evidence=(),
                unknowns=(),
            )

    def test_scientific_output_is_traceable_and_human_reviewable(self) -> None:
        metadata = ScientificOutputMetadata(
            timestamp=NOW,
            author="test-system",
            provenance=Provenance(
                creator="test-system", created_at=NOW, source="system-output"
            ),
            confidence=confidence(),
            traceability=traceability(),
            related_scientific_entities=("hypothesis-1",),
        )
        output = ScientificOutput(
            output_type="Recommendation",
            content={"recommendation": "Request independent replication"},
            metadata=metadata,
        )

        self.assertTrue(output.metadata.requires_human_review)
        self.assertEqual(
            output.metadata.related_scientific_entities, ("hypothesis-1",)
        )

    def test_engine_interfaces_are_structurally_replaceable(self) -> None:
        self.assertIsInstance(StructuralMethodEngine(), ScientificMethodEngine)
        self.assertIsInstance(StructuralCognitiveSystem(), ScientificCognitiveSystem)


if __name__ == "__main__":
    unittest.main()

