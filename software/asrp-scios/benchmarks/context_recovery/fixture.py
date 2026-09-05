"""Deterministic synthetic Scientific Research Graph fixture for Sprint-005."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from asrp_scios.domain.aggregates import (
    ContextSnapshot,
    Hypothesis,
    ResearchCampaign,
    ResearchDecision,
    ScientificQuestion,
)
from asrp_scios.domain.entities import (
    Evidence,
    KnowledgeItem,
    ScientificEntity,
    ScientificProgram,
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
from asrp_scios.srg import InMemoryScientificResearchGraph, ScientificResearchGraph

from .model import BenchmarkScenario


FIXTURE_TIME = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class ContextRecoveryFixture:
    """Graph plus immutable inventory and scenarios for reproducible evaluation."""

    graph: ScientificResearchGraph
    entities: tuple[ScientificEntity, ...]
    relationships: tuple[ScientificRelationship, ...]
    scenarios: tuple[BenchmarkScenario, ...]
    fixed_time: datetime = FIXTURE_TIME

    def scenario(self, scenario_id: str) -> BenchmarkScenario:
        """Return a named scenario, failing explicitly for an unknown ID."""
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        raise KeyError(f"unknown benchmark scenario: {scenario_id}")


def _provenance(source: str = "Synthetic benchmark fixture") -> Provenance:
    return Provenance(
        creator="ASRP-Lab Sprint-005",
        created_at=FIXTURE_TIME,
        source=source,
        method="explicit deterministic construction",
        input_entities=("synthetic-context-recovery-dataset",),
        tool_or_system="ASRP-SciOS",
        review_status="SyntheticFixture",
        version_history=("Sprint-005",),
    )


def _traceability() -> Traceability:
    return Traceability(
        requirements=("Sprint-005/BENCHMARK_MVP_SPEC",),
        decisions=("SC-005-001", "SC-005-002", "SC-005-003"),
        specifications=(
            "Sprint-005/METRICS_SPEC",
            "Sprint-005/DATASET_AND_FIXTURE_SPEC",
        ),
        implementation_version="0.4.0",
    )


def _entity_fields(identifier: EntityId, status: object) -> dict[str, object]:
    return {
        "id": identifier,
        "title": f"Synthetic {identifier}",
        "description": "A domain-independent synthetic context recovery record.",
        "status": status,
        "version": Version(1),
        "created_at": FIXTURE_TIME,
        "updated_at": FIXTURE_TIME,
        "created_by": "ASRP-Lab Sprint-005",
        "provenance": _provenance(),
        "traceability": _traceability(),
        "tags": ("synthetic", "context-recovery"),
    }


def _confidence() -> Confidence:
    return Confidence(
        ConfidenceLevel.PLAUSIBLE,
        "The assertion is deliberately defined by the synthetic fixture.",
        FIXTURE_TIME,
        score=0.6,
    )


def _evidence(
    identifier: str, direction: EvidenceDirection, source_identifier: str
) -> Evidence:
    return Evidence(
        **_entity_fields(EntityId(identifier), EvidenceStatus.COLLECTED),
        evidence_type=EvidenceType.MEASUREMENT,
        direction=direction,
        source_reference=ScientificReference(
            EntityId(source_identifier), source="Synthetic measurement record"
        ),
        method="Controlled synthetic measurement",
        confidence=_confidence(),
        uncertainty="The fixture does not represent an empirical observation.",
        limitations=("Synthetic evidence has no external scientific validity.",),
    )


def _relationship(
    identifier: str,
    relationship_type: RelationshipType,
    source_id: EntityId,
    target_id: EntityId,
) -> ScientificRelationship:
    return ScientificRelationship(
        relationship_id=EntityId(identifier),
        relationship_type=relationship_type,
        source_entity_id=source_id,
        target_entity_id=target_id,
        confidence=_confidence(),
        provenance=_provenance("Synthetic relationship assertion"),
        traceability=_traceability(),
        created_at=FIXTURE_TIME,
        created_by="ASRP-Lab Sprint-005",
        rationale="The edge exercises deterministic context recovery behavior.",
    )


def build_context_recovery_fixture() -> ContextRecoveryFixture:
    """Build the same 18-entity, 22-edge synthetic SRG on every invocation."""
    program = ScientificProgram(
        **_entity_fields(EntityId("program.synthetic-context"), LifecycleStatus.ACTIVE),
        mission="Evaluate generic scientific context recovery behavior.",
        scientific_objectives=("Exercise deterministic graph selection.",),
    )
    campaign = ResearchCampaign(
        **_entity_fields(AggregateId("campaign.synthetic-context"), LifecycleStatus.ACTIVE),
        program_id=program.id,
    )
    question_a = ScientificQuestion(
        **_entity_fields(AggregateId("question.recovery-a"), LifecycleStatus.ACTIVE),
        statement="Which documented relation best explains synthetic observation A?",
        campaign_ids=(campaign.id,),
    )
    question_b = ScientificQuestion(
        **_entity_fields(AggregateId("question.recovery-b"), LifecycleStatus.ACTIVE),
        statement="Which boundary condition changes synthetic observation B?",
        campaign_ids=(campaign.id,),
    )
    hypothesis_a = Hypothesis(
        **_entity_fields(AggregateId("hypothesis.recovery-a"), HypothesisStatus.PROPOSED),
        statement="Synthetic relation A predicts the controlled outcome.",
        question_id=question_a.id,
    )
    hypothesis_b = Hypothesis(
        **_entity_fields(AggregateId("hypothesis.recovery-b"), HypothesisStatus.PROPOSED),
        statement="Synthetic alternative B predicts the controlled outcome.",
        question_id=question_a.id,
    )
    hypothesis_c = Hypothesis(
        **_entity_fields(AggregateId("hypothesis.recovery-c"), HypothesisStatus.PROPOSED),
        statement="A boundary condition changes synthetic observation B.",
        question_id=question_b.id,
    )
    evidence_support_a = _evidence(
        "evidence.support-a", EvidenceDirection.SUPPORTS, "source.synthetic-a"
    )
    evidence_contradict_a = _evidence(
        "evidence.contradict-a",
        EvidenceDirection.CONTRADICTS,
        "source.synthetic-b",
    )
    evidence_support_b = _evidence(
        "evidence.support-b", EvidenceDirection.SUPPORTS, "source.synthetic-c"
    )
    evidence_qualify_c = _evidence(
        "evidence.qualify-c", EvidenceDirection.QUALIFIES, "source.synthetic-d"
    )
    decision_a = ResearchDecision(
        **_entity_fields(
            AggregateId("decision.recovery-a"), ResearchDecisionStatus.PROPOSED
        ),
        decision_type=DecisionType.SCIENTIFIC,
        evidence_collection_ids=(evidence_support_a.id, evidence_contradict_a.id),
        affected_entity_ids=(hypothesis_a.id,),
        limitations=("This synthetic decision has not undergone human review.",),
    )
    decision_b = ResearchDecision(
        **_entity_fields(
            AggregateId("decision.recovery-b"), ResearchDecisionStatus.PROPOSED
        ),
        decision_type=DecisionType.METHODOLOGICAL,
        evidence_collection_ids=(evidence_support_b.id,),
        affected_entity_ids=(hypothesis_b.id, hypothesis_c.id),
    )
    unknown_a = Unknown(
        **_entity_fields(EntityId("unknown.recovery-a"), LifecycleStatus.ACTIVE),
        importance="The synthetic measurement boundary may affect interpretation.",
        affected_hypothesis_ids=(hypothesis_a.id,),
        proposed_investigations=("Repeat the synthetic measurement at the boundary.",),
    )
    unknown_b = Unknown(
        **_entity_fields(EntityId("unknown.recovery-b"), LifecycleStatus.ACTIVE),
        importance="The second boundary condition remains unspecified.",
        affected_hypothesis_ids=(hypothesis_c.id,),
        proposed_investigations=("Specify the second synthetic boundary condition.",),
    )
    knowledge_a = KnowledgeItem(
        **_entity_fields(EntityId("knowledge.recovery-a"), LifecycleStatus.ACTIVE),
        evidence_collection_ids=(evidence_support_a.id,),
        validation_decision_ids=(decision_a.id,),
    )
    knowledge_b = KnowledgeItem(
        **_entity_fields(EntityId("knowledge.recovery-b"), LifecycleStatus.ACTIVE),
        evidence_collection_ids=(evidence_support_b.id,),
        validation_decision_ids=(decision_b.id,),
    )
    prior_context = ContextSnapshot(
        **_entity_fields(AggregateId("context.synthetic-prior"), LifecycleStatus.ACTIVE),
        task_reference=EntityId("benchmark-task:prior-review"),
        context_data={
            "scope": "Prior synthetic review",
            "limitations": ("Synthetic context only.",),
        },
        scientific_entity_ids=(hypothesis_a.id, evidence_support_a.id, decision_a.id),
    )

    entities: tuple[ScientificEntity, ...] = tuple(
        sorted(
            (
                program,
                campaign,
                question_a,
                question_b,
                hypothesis_a,
                hypothesis_b,
                hypothesis_c,
                evidence_support_a,
                evidence_contradict_a,
                evidence_support_b,
                evidence_qualify_c,
                decision_a,
                decision_b,
                unknown_a,
                unknown_b,
                knowledge_a,
                knowledge_b,
                prior_context,
            ),
            key=lambda value: str(value.id),
        )
    )
    relationships = tuple(
        sorted(
            (
                _relationship("rel.01", RelationshipType.BELONGS_TO, campaign.id, program.id),
                _relationship("rel.02", RelationshipType.BELONGS_TO, question_a.id, campaign.id),
                _relationship("rel.03", RelationshipType.BELONGS_TO, question_b.id, campaign.id),
                _relationship("rel.04", RelationshipType.GENERATES, question_a.id, hypothesis_a.id),
                _relationship("rel.05", RelationshipType.GENERATES, question_a.id, hypothesis_b.id),
                _relationship("rel.06", RelationshipType.GENERATES, question_b.id, hypothesis_c.id),
                _relationship("rel.07", RelationshipType.SUPPORTS, evidence_support_a.id, hypothesis_a.id),
                _relationship("rel.08", RelationshipType.CONTRADICTS, evidence_contradict_a.id, hypothesis_a.id),
                _relationship("rel.09", RelationshipType.SUPPORTS, evidence_support_b.id, hypothesis_b.id),
                _relationship("rel.10", RelationshipType.REFINES, evidence_qualify_c.id, hypothesis_c.id),
                _relationship("rel.11", RelationshipType.DECIDED_BY, hypothesis_a.id, decision_a.id),
                _relationship("rel.12", RelationshipType.DECIDED_BY, hypothesis_b.id, decision_b.id),
                _relationship("rel.13", RelationshipType.DEPENDS_ON, unknown_a.id, hypothesis_a.id),
                _relationship("rel.14", RelationshipType.DEPENDS_ON, unknown_b.id, question_b.id),
                _relationship("rel.15", RelationshipType.DERIVES_FROM, knowledge_a.id, evidence_support_a.id),
                _relationship("rel.16", RelationshipType.DERIVES_FROM, knowledge_b.id, evidence_support_b.id),
                _relationship("rel.17", RelationshipType.REFERENCES, decision_a.id, evidence_support_a.id),
                _relationship("rel.18", RelationshipType.REFERENCES, decision_a.id, evidence_contradict_a.id),
                _relationship("rel.19", RelationshipType.USES_CONTEXT, decision_a.id, prior_context.id),
                _relationship("rel.20", RelationshipType.REFERENCES, decision_b.id, evidence_support_b.id),
                _relationship("rel.21", RelationshipType.DEPENDS_ON, hypothesis_c.id, knowledge_b.id),
                _relationship("rel.22", RelationshipType.VALIDATES, knowledge_a.id, hypothesis_a.id),
            ),
            key=lambda value: str(value.relationship_id),
        )
    )

    graph = InMemoryScientificResearchGraph()
    for entity in entities:
        graph.register_entity(entity)
    for relationship in relationships:
        graph.add_relationship(relationship)

    scenarios = (
        BenchmarkScenario(
            scenario_id="hypothesis_review_recovery",
            scenario_name="Hypothesis Review Recovery",
            purpose="Recover the question, evidence, decision, and unknowns needed to review a hypothesis.",
            seed_entity_ids=(hypothesis_a.id,),
            expected_entity_types=(
                "ScientificQuestion",
                "Evidence",
                "ResearchDecision",
                "Unknown",
            ),
        ),
        BenchmarkScenario(
            scenario_id="decision_trace_recovery",
            scenario_name="Decision Trace Recovery",
            purpose="Recover evidence, hypothesis, question, knowledge, and prior context behind a decision.",
            seed_entity_ids=(decision_a.id,),
            expected_entity_types=(
                "Evidence",
                "Hypothesis",
                "ScientificQuestion",
                "KnowledgeItem",
                "ContextSnapshot",
            ),
        ),
        BenchmarkScenario(
            scenario_id="evidence_audit_recovery",
            scenario_name="Evidence Audit Recovery",
            purpose="Recover hypothesis, decision, direction, provenance, and related knowledge for an evidence audit.",
            seed_entity_ids=(evidence_support_a.id,),
            expected_entity_types=(
                "Hypothesis",
                "ResearchDecision",
                "ScientificQuestion",
                "KnowledgeItem",
            ),
        ),
    )
    return ContextRecoveryFixture(
        graph=graph,
        entities=entities,
        relationships=relationships,
        scenarios=scenarios,
    )

