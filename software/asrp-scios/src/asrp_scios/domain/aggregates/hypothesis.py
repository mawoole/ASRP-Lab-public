"""Hypothesis aggregate root.

Purpose:
    Model a falsifiable scientific claim and its evidence-backed lifecycle.
Responsibilities:
    Enforce testability declarations, evidence references, confidence, and review.
Key classes:
    Hypothesis.
Out-of-scope:
    Hypothesis generation, experiment execution, ranking, and persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from asrp_scios.contracts._validation import require_non_empty, require_optional_non_empty
from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.lifecycle import HypothesisStatus
from asrp_scios.domain.value_objects import (
    AggregateId,
    Confidence,
    EntityId,
    HumanReviewMetadata,
)

from .base import create_aggregate_event, freeze_entity_ids


@dataclass(frozen=True, slots=True, kw_only=True)
class Hypothesis(ScientificEntity):
    """AGG-001 hypothesis root with explicit testability and falsifiability."""

    id: AggregateId
    statement: str
    question_id: EntityId
    testability_statement: str | None = None
    falsification_criteria: tuple[str, ...] = ()
    evidence_collection_ids: tuple[EntityId, ...] = ()
    decision_ids: tuple[EntityId, ...] = ()
    confidence: Confidence | None = None
    human_review: HumanReviewMetadata | None = None

    def __post_init__(self) -> None:
        super(Hypothesis, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        object.__setattr__(self, "statement", require_non_empty(self.statement, "statement"))
        if not isinstance(self.question_id, EntityId):
            raise TypeError("question_id must be an EntityId")
        object.__setattr__(
            self,
            "testability_statement",
            require_optional_non_empty(self.testability_statement, "testability_statement"),
        )
        criteria = tuple(
            require_non_empty(value, f"falsification_criteria[{index}]")
            for index, value in enumerate(self.falsification_criteria)
        )
        object.__setattr__(self, "falsification_criteria", criteria)
        for field_name in ("evidence_collection_ids", "decision_ids"):
            object.__setattr__(
                self, field_name, freeze_entity_ids(getattr(self, field_name), field_name)
            )
        if self.confidence is not None and not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be Confidence when provided")
        if self.human_review is not None and not isinstance(
            self.human_review, HumanReviewMetadata
        ):
            raise TypeError("human_review must be HumanReviewMetadata when provided")
        post_declaration_states = {
            HypothesisStatus.TESTABLE,
            HypothesisStatus.TESTING,
            HypothesisStatus.SUPPORTED,
            HypothesisStatus.CONTRADICTED,
            HypothesisStatus.VALIDATED,
            HypothesisStatus.REJECTED,
        }
        if self.status in post_declaration_states and self.testability_statement is None:
            raise ValueError(
                "Hypothesis cannot become testable without a testability statement"
            )
        if self.status is HypothesisStatus.VALIDATED:
            if not self.evidence_collection_ids or not self.decision_ids:
                raise ValueError("validated Hypothesis requires evidence and a decision")
            if self.human_review is None or not self.human_review.is_complete:
                raise ValueError("validated Hypothesis requires completed human review")

    def declare_testable(
        self,
        testability_statement: str,
        *,
        declared_at: datetime,
        declared_by: str,
        falsification_criteria: tuple[str, ...] = (),
    ) -> tuple[Hypothesis, ScientificEvent]:
        """Declare how this hypothesis can be tested and potentially falsified."""
        statement = require_non_empty(testability_statement, "testability_statement")
        criteria = tuple(
            require_non_empty(value, f"falsification_criteria[{index}]")
            for index, value in enumerate(falsification_criteria)
        )
        updated = replace(
            self,
            status=HypothesisStatus.TESTABLE,
            testability_statement=statement,
            falsification_criteria=criteria,
            version=self.version.next_patch(),
            updated_at=declared_at,
        )
        event = create_aggregate_event(
            updated,
            "HypothesisDeclaredTestable",
            produced_by=declared_by,
            payload={
                "testability_statement": statement,
                "falsification_criteria": criteria,
            },
            occurred_at=declared_at,
            related_entity_ids=(self.question_id,),
        )
        return updated, event

    def validate(
        self,
        *,
        evidence_collection_ids: tuple[EntityId, ...],
        decision_ids: tuple[EntityId, ...],
        confidence: Confidence,
        human_review: HumanReviewMetadata,
        validated_at: datetime,
        validated_by: str,
    ) -> tuple[Hypothesis, ScientificEvent]:
        """Validate the claim with evidence, decision, confidence, and review."""
        evidence = freeze_entity_ids(evidence_collection_ids, "evidence_collection_ids")
        decisions = freeze_entity_ids(decision_ids, "decision_ids")
        if not evidence or not decisions:
            raise ValueError("validated Hypothesis requires evidence and a decision")
        if not isinstance(confidence, Confidence):
            raise TypeError("confidence must be Confidence")
        if not isinstance(human_review, HumanReviewMetadata) or not human_review.is_complete:
            raise ValueError("validation requires completed human review")
        updated = replace(
            self,
            status=HypothesisStatus.VALIDATED,
            evidence_collection_ids=evidence,
            decision_ids=decisions,
            confidence=confidence,
            human_review=human_review,
            version=self.version.next_patch(),
            updated_at=validated_at,
        )
        event = create_aggregate_event(
            updated,
            "HypothesisValidated",
            produced_by=validated_by,
            payload={
                "evidence_collection_ids": tuple(map(str, evidence)),
                "decision_ids": tuple(map(str, decisions)),
                "confidence_level": confidence.level.value,
            },
            occurred_at=validated_at,
            related_entity_ids=evidence + decisions,
            human_review=human_review,
        )
        return updated, event
