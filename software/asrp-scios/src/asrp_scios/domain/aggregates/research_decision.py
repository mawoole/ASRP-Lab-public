"""ResearchDecision aggregate root.

Purpose:
    Make consequential scientific and governance choices explicit and traceable.
Responsibilities:
    Preserve alternatives, rationale, evidence, limitations, and human review.
Key classes:
    ResearchDecision.
Out-of-scope:
    Authorization, voting, policy engines, persistence, and automatic decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from asrp_scios.contracts._validation import freeze_strings, require_optional_non_empty
from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.lifecycle import ResearchDecisionStatus
from asrp_scios.domain.value_objects import (
    AggregateId,
    DecisionType,
    EntityId,
    HumanReviewMetadata,
)

from .base import create_aggregate_event, freeze_entity_ids


@dataclass(frozen=True, slots=True, kw_only=True)
class ResearchDecision(ScientificEntity):
    """AGG-001 decision root with evidence and responsibility metadata."""

    id: AggregateId
    decision_type: DecisionType
    rationale: str | None = None
    alternatives: tuple[str, ...] = ()
    evidence_collection_ids: tuple[EntityId, ...] = ()
    limitations: tuple[str, ...] = ()
    affected_entity_ids: tuple[EntityId, ...] = ()
    human_review: HumanReviewMetadata | None = None

    def __post_init__(self) -> None:
        super(ResearchDecision, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        if not isinstance(self.decision_type, DecisionType):
            raise TypeError("decision_type must be a DecisionType")
        object.__setattr__(
            self, "rationale", require_optional_non_empty(self.rationale, "rationale")
        )
        object.__setattr__(self, "alternatives", freeze_strings(self.alternatives, "alternatives"))
        object.__setattr__(self, "limitations", freeze_strings(self.limitations, "limitations"))
        for field_name in ("evidence_collection_ids", "affected_entity_ids"):
            object.__setattr__(
                self, field_name, freeze_entity_ids(getattr(self, field_name), field_name)
            )
        if self.human_review is not None and not isinstance(
            self.human_review, HumanReviewMetadata
        ):
            raise TypeError("human_review must be HumanReviewMetadata when provided")
        if self.status is ResearchDecisionStatus.ACCEPTED:
            if self.rationale is None:
                raise ValueError("ResearchDecision cannot be accepted without rationale")
            if self.decision_type is DecisionType.SCIENTIFIC and not self.evidence_collection_ids:
                raise ValueError("accepted scientific decision requires evidence")
            if self.human_review is None or not self.human_review.is_complete:
                raise ValueError("accepted ResearchDecision requires completed human review")

    def accept(
        self,
        *,
        rationale: str,
        accepted_at: datetime,
        accepted_by: str,
        human_review: HumanReviewMetadata,
        evidence_collection_ids: tuple[EntityId, ...] | None = None,
    ) -> tuple[ResearchDecision, ScientificEvent]:
        """Accept the decision with accountable rationale and required evidence."""
        normalized_rationale = require_optional_non_empty(rationale, "rationale")
        if normalized_rationale is None:
            raise ValueError("ResearchDecision cannot be accepted without rationale")
        evidence = (
            self.evidence_collection_ids
            if evidence_collection_ids is None
            else freeze_entity_ids(evidence_collection_ids, "evidence_collection_ids")
        )
        if self.decision_type is DecisionType.SCIENTIFIC and not evidence:
            raise ValueError("accepted scientific decision requires evidence")
        if not isinstance(human_review, HumanReviewMetadata) or not human_review.is_complete:
            raise ValueError("acceptance requires completed human review")
        updated = replace(
            self,
            status=ResearchDecisionStatus.ACCEPTED,
            rationale=normalized_rationale,
            evidence_collection_ids=evidence,
            human_review=human_review,
            version=self.version.next_patch(),
            updated_at=accepted_at,
        )
        event = create_aggregate_event(
            updated,
            "ResearchDecisionAccepted",
            produced_by=accepted_by,
            payload={
                "decision_type": self.decision_type.value,
                "rationale": normalized_rationale,
                "evidence_collection_ids": tuple(map(str, evidence)),
            },
            occurred_at=accepted_at,
            related_entity_ids=evidence + self.affected_entity_ids,
            human_review=human_review,
        )
        return updated, event
