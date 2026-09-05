"""Sprint-002B acceptance tests for the Scientific Domain Model baseline."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import unittest

import asrp_scios.domain as domain
from asrp_scios.domain.aggregates import (
    ContextSnapshot,
    Discovery,
    EvidenceCollection,
    Hypothesis,
    ResearchCampaign,
    ResearchDecision,
    ResearchProgram,
    ScientificQuestion,
)
from asrp_scios.domain.capabilities import (
    CapabilityCategory,
    CapabilityContract,
    CapabilityDescriptor,
    CapabilityInput,
    CapabilityOutput,
    CapabilityProviderDescriptor,
    CapabilityReadinessLevel,
    ProviderType,
)
from asrp_scios.domain.entities import (
    Evidence,
    Experiment,
    KnowledgeItem,
    Observation,
    Patent,
    Publication,
    ScientificEntity,
    ScientificProgram,
    Simulation,
    Unknown,
)
from asrp_scios.domain.events import (
    AGGREGATE_EVENT_TYPES,
    EVENT_CATALOG,
    EventCategory,
    validate_event_name,
)
from asrp_scios.domain.lifecycle import (
    EvidenceStatus,
    HypothesisStatus,
    LifecycleStatus,
    ResearchDecisionStatus,
    ReviewStatus,
)
from asrp_scios.domain.value_objects import (
    AggregateId,
    CapabilityId,
    Confidence,
    ConfidenceLevel,
    DecisionType,
    EntityId,
    EvidenceDirection,
    EvidenceType,
    HumanReviewMetadata,
    Provenance,
    ProviderId,
    ScientificReference,
    Traceability,
    Version,
)


NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


def provenance() -> Provenance:
    return Provenance(
        creator="researcher-1",
        created_at=NOW,
        source="controlled-observation",
        method="documented-method",
        input_entities=("question-1",),
        tool_or_system="laboratory-system",
        review_status="Pending",
        version_history=("1.0.0",),
    )


def traceability() -> Traceability:
    return Traceability(
        requirements=("ONT-001", "AGG-001"),
        decisions=("ADR-0001",),
        specifications=("EVT-001",),
        implementation_version="0.2.0",
    )


def entity_fields(identifier: EntityId, status: object) -> dict[str, object]:
    return {
        "id": identifier,
        "title": "Scientific object",
        "description": "Domain-independent scientific description.",
        "status": status,
        "version": Version(1, 0, 0),
        "created_at": NOW,
        "updated_at": NOW,
        "created_by": "researcher-1",
        "provenance": provenance(),
        "traceability": traceability(),
    }


def accepted_review() -> HumanReviewMetadata:
    return HumanReviewMetadata(
        reviewer_id="reviewer-1",
        status=ReviewStatus.ACCEPTED,
        reviewed_at=NOW,
        rationale="The evidence and limitations were independently reviewed.",
        decision_reference="decision-1",
    )


def evidence() -> Evidence:
    return Evidence(
        **entity_fields(EntityId("evidence-1"), EvidenceStatus.COLLECTED),
        evidence_type=EvidenceType.EXPERIMENTAL,
        direction=EvidenceDirection.SUPPORTS,
        source_reference=ScientificReference(
            EntityId("observation-1"), Version(1), source="instrument record"
        ),
        method="Controlled measurement",
        confidence=Confidence(
            ConfidenceLevel.PLAUSIBLE,
            "Initial measurement is internally consistent.",
            NOW,
            score=0.6,
        ),
    )


class ScientificDomainModelTests(unittest.TestCase):
    def test_canonical_core_concepts_are_public(self) -> None:
        required = {
            "ScientificEntity",
            "ScientificProgram",
            "ResearchCampaign",
            "ScientificQuestion",
            "Observation",
            "Hypothesis",
            "Experiment",
            "Simulation",
            "Evidence",
            "Unknown",
            "ResearchDecision",
            "KnowledgeItem",
            "Discovery",
            "Publication",
            "Patent",
            "ContextSnapshot",
            "ScientificRelationship",
            "ScientificEvent",
        }
        self.assertTrue(required.issubset(set(domain.__all__)))

    def test_scientific_entity_is_abstract(self) -> None:
        with self.assertRaises(TypeError):
            ScientificEntity(
                **entity_fields(EntityId("entity-1"), LifecycleStatus.DRAFT)
            )

    def test_nonaggregate_entities_construct_with_canonical_names(self) -> None:
        program = ScientificProgram(
            **entity_fields(EntityId("scientific-program-1"), LifecycleStatus.ACTIVE),
            mission="Study a reproducible scientific phenomenon.",
        )
        observation = Observation(
            **entity_fields(EntityId("observation-1"), LifecycleStatus.ACTIVE),
            observed_at=NOW,
            observation_source="Calibrated instrument",
        )
        experiment = Experiment(
            **entity_fields(EntityId("experiment-1"), LifecycleStatus.ACTIVE),
            hypothesis_ids=(EntityId("hypothesis-1"),),
            method="Controlled comparison",
        )
        simulation = Simulation(
            **entity_fields(EntityId("simulation-1"), LifecycleStatus.ACTIVE),
            hypothesis_ids=(EntityId("hypothesis-1"),),
            model_description="A documented numerical model.",
        )
        unknown = Unknown(
            **entity_fields(EntityId("unknown-1"), LifecycleStatus.ACTIVE),
            importance="May change the interpretation of the result.",
        )
        knowledge = KnowledgeItem(
            **entity_fields(EntityId("knowledge-1"), LifecycleStatus.VALIDATED),
            evidence_collection_ids=(EntityId("collection-1"),),
            validation_decision_ids=(EntityId("decision-1"),),
        )
        reference = ScientificReference(
            EntityId("discovery-1"), Version(1), citation="Stable reference"
        )
        publication = Publication(
            **entity_fields(EntityId("publication-1"), LifecycleStatus.ACTIVE),
            discovery_ids=(EntityId("discovery-1"),),
            reference=reference,
        )
        patent = Patent(
            **entity_fields(EntityId("patent-1"), LifecycleStatus.ACTIVE),
            discovery_ids=(EntityId("discovery-1"),),
            reference=reference,
        )
        self.assertEqual(
            {
                value.entity_type
                for value in (
                    program,
                    observation,
                    experiment,
                    simulation,
                    evidence(),
                    unknown,
                    knowledge,
                    publication,
                    patent,
                )
            },
            {
                "ScientificProgram",
                "Observation",
                "Experiment",
                "Simulation",
                "Evidence",
                "Unknown",
                "KnowledgeItem",
                "Publication",
                "Patent",
            },
        )

    def test_hypothesis_cannot_be_testable_without_statement(self) -> None:
        with self.assertRaisesRegex(ValueError, "testability statement"):
            Hypothesis(
                **entity_fields(AggregateId("hypothesis-1"), HypothesisStatus.TESTABLE),
                statement="A measurable relation exists.",
                question_id=EntityId("question-1"),
            )

    def test_hypothesis_transition_returns_new_root_and_domain_event(self) -> None:
        hypothesis = Hypothesis(
            **entity_fields(AggregateId("hypothesis-1"), HypothesisStatus.PROPOSED),
            statement="A measurable relation exists.",
            question_id=EntityId("question-1"),
        )
        updated, event = hypothesis.declare_testable(
            "Compare the measured outcome with a predeclared threshold.",
            declared_at=NOW,
            declared_by="researcher-1",
            falsification_criteria=("Outcome remains below the threshold.",),
        )
        self.assertIs(hypothesis.status, HypothesisStatus.PROPOSED)
        self.assertIs(updated.status, HypothesisStatus.TESTABLE)
        self.assertEqual(event.event_type, "HypothesisDeclaredTestable")
        self.assertIs(event.event_category, EventCategory.SCIENTIFIC_METHOD)
        self.assertEqual(event.aggregate_id, hypothesis.id)
        self.assertEqual(event.aggregate_type, "Hypothesis")
        self.assertEqual(event.provenance, hypothesis.provenance)
        self.assertEqual(event.traceability, hypothesis.traceability)
        with self.assertRaises(FrozenInstanceError):
            event.event_type = "HypothesisRefined"  # type: ignore[misc]

    def test_research_decision_cannot_be_accepted_without_rationale(self) -> None:
        with self.assertRaises(ValueError):
            ResearchDecision(
                **entity_fields(
                    AggregateId("decision-1"), ResearchDecisionStatus.ACCEPTED
                ),
                decision_type=DecisionType.PROGRAM,
                rationale="",
                human_review=accepted_review(),
            )

    def test_discovery_cannot_validate_without_evidence_and_decision(self) -> None:
        with self.assertRaisesRegex(ValueError, "evidence and validation decisions"):
            Discovery(
                **entity_fields(AggregateId("discovery-1"), LifecycleStatus.VALIDATED),
                validation_scope="Observed operating conditions only.",
                human_review=accepted_review(),
            )

    def test_context_snapshot_is_deeply_immutable(self) -> None:
        snapshot = ContextSnapshot(
            **entity_fields(AggregateId("context-1"), LifecycleStatus.ACTIVE),
            task_reference=EntityId("task-1"),
            context_data={"parameters": {"temperature": 20}, "steps": ["measure"]},
        )
        with self.assertRaises(FrozenInstanceError):
            snapshot.title = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            snapshot.context_data["parameters"] = {}  # type: ignore[index]
        with self.assertRaises(TypeError):
            snapshot.context_data["parameters"]["temperature"] = 21  # type: ignore[index]

    def test_evidence_collection_preserves_provenance_and_direction(self) -> None:
        item = evidence()
        collection = EvidenceCollection(
            **entity_fields(AggregateId("collection-1"), EvidenceStatus.COLLECTED),
            target_entity_id=EntityId("hypothesis-1"),
            evidence_items=(item,),
        )
        self.assertEqual(collection.evidence_items[0].provenance, provenance())
        self.assertIs(
            collection.evidence_items[0].direction, EvidenceDirection.SUPPORTS
        )

    def test_research_program_is_scientific_program_specialization(self) -> None:
        program = ResearchProgram(
            **entity_fields(AggregateId("program-1"), LifecycleStatus.ACTIVE),
            mission="Investigate a domain-independent scientific question.",
        )
        self.assertEqual(program.entity_type, "ResearchProgram")
        self.assertEqual(program.id, AggregateId("program-1"))

    def test_all_aggregate_roots_construct_with_cross_aggregate_ids(self) -> None:
        campaign = ResearchCampaign(
            **entity_fields(AggregateId("campaign-1"), LifecycleStatus.ACTIVE),
            program_id=EntityId("program-1"),
        )
        question = ScientificQuestion(
            **entity_fields(AggregateId("question-1"), LifecycleStatus.ACTIVE),
            statement="Which measurable relation best explains the observation?",
            campaign_ids=(campaign.id,),
        )
        decision = ResearchDecision(
            **entity_fields(
                AggregateId("decision-1"), ResearchDecisionStatus.PROPOSED
            ),
            decision_type=DecisionType.SCIENTIFIC,
        )
        discovery = Discovery(
            **entity_fields(AggregateId("discovery-1"), LifecycleStatus.PROPOSED)
        )
        snapshot = ContextSnapshot(
            **entity_fields(AggregateId("snapshot-1"), LifecycleStatus.ACTIVE),
            mission_reference=EntityId("mission-1"),
            context_data={"scope": "baseline"},
        )
        collection = EvidenceCollection(
            **entity_fields(AggregateId("collection-1"), EvidenceStatus.COLLECTED),
            target_entity_id=question.id,
        )
        self.assertEqual(
            {
                value.entity_type
                for value in (
                    campaign,
                    question,
                    Hypothesis(
                        **entity_fields(
                            AggregateId("hypothesis-1"), HypothesisStatus.PROPOSED
                        ),
                        statement="A measurable relation exists.",
                        question_id=question.id,
                    ),
                    collection,
                    decision,
                    discovery,
                    snapshot,
                )
            },
            {
                "ResearchCampaign",
                "ScientificQuestion",
                "Hypothesis",
                "EvidenceCollection",
                "ResearchDecision",
                "Discovery",
                "ContextSnapshot",
            },
        )

    def test_event_catalog_maps_every_required_aggregate(self) -> None:
        required_aggregates = {
            "ResearchProgram",
            "ResearchCampaign",
            "ScientificQuestion",
            "Hypothesis",
            "EvidenceCollection",
            "ResearchDecision",
            "Discovery",
            "ContextSnapshot",
        }
        self.assertTrue(required_aggregates.issubset(AGGREGATE_EVENT_TYPES))
        self.assertGreaterEqual(len(EVENT_CATALOG), 80)
        self.assertEqual(validate_event_name("EvidenceLinkedToDiscovery"), "EvidenceLinkedToDiscovery")
        with self.assertRaises(ValueError):
            validate_event_name("hypothesis.created")
        with self.assertRaises(ValueError):
            validate_event_name("HypothesisCreate")


class CapabilityModelTests(unittest.TestCase):
    def test_descriptor_requires_typed_provider_declarations(self) -> None:
        descriptor = CapabilityDescriptor(
            capability_id=CapabilityId("cap.testability-assessment"),
            name="TestabilityAssessment",
            version=Version(1),
            category=CapabilityCategory.SCIENTIFIC_METHOD,
            description="Assess whether a claim exposes measurable tests.",
            inputs=(CapabilityInput("hypothesis", "Hypothesis"),),
            outputs=(
                CapabilityOutput(
                    "assessment", "ScientificReview", confidence_required=True
                ),
            ),
            provider_types=(
                ProviderType.HUMAN_RESEARCHER,
                ProviderType.SCIENTIFIC_COGNITIVE_SYSTEM,
            ),
            readiness_level=CapabilityReadinessLevel.CRL2,
            human_review_required=True,
        )
        self.assertEqual(descriptor.readiness_level.description, "Contract specified")
        self.assertEqual(descriptor.inputs[0].name, "hypothesis")
        provider = CapabilityProviderDescriptor(
            provider_id=ProviderId("provider.review-board"),
            name="Independent Review Board",
            provider_type=ProviderType.HUMAN_RESEARCHER,
            version=Version(1),
            supported_capabilities=(descriptor.capability_id,),
            readiness_level=CapabilityReadinessLevel.CRL3,
            status="Available",
        )
        self.assertEqual(provider.supported_capabilities, (descriptor.capability_id,))
        with self.assertRaises(ValueError):
            CapabilityDescriptor(
                capability_id=CapabilityId("cap.invalid"),
                name="InvalidCapability",
                version=Version(1),
                category=CapabilityCategory.RESEARCH,
                description="Missing providers.",
                inputs=(),
                outputs=(),
                provider_types=(),
            )

    def test_capability_contract_is_structural_and_has_no_invoke_method(self) -> None:
        self.assertTrue(getattr(CapabilityContract, "_is_runtime_protocol", False))
        self.assertFalse(hasattr(CapabilityContract, "invoke"))


class DomainIndependenceTests(unittest.TestCase):
    def test_domain_source_contains_no_program_specific_leakage(self) -> None:
        source_root = (
            Path(__file__).parents[1] / "src" / "asrp_scios" / "domain"
        )
        forbidden = ("RM-X", "regenerative medicine", "oncology", "climate program")
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in source_root.rglob("*.py")
        ).lower()
        for term in forbidden:
            self.assertNotIn(term.lower(), source)

    def test_domain_has_no_infrastructure_or_kernel_dependencies(self) -> None:
        source_root = Path(__file__).parents[1] / "src" / "asrp_scios"
        domain_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (source_root / "domain").rglob("*.py")
        ).lower()
        forbidden_imports = (
            "import sqlalchemy",
            "import django",
            "import fastapi",
            "import openai",
            "import requests",
            "import psycopg",
            "asrp_scios.eventing",
            "asrp_scios.kernel",
        )
        for term in forbidden_imports:
            self.assertNotIn(term, domain_source)
        kernel_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (source_root / "kernel").rglob("*.py")
        )
        self.assertNotIn("asrp_scios.domain", kernel_source)


if __name__ == "__main__":
    unittest.main()
