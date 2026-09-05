"""Discovery aggregate root.

Purpose:
    Represent a proposed scientific finding through explicit validation.
Responsibilities:
    Require evidence, a validation decision, scope, and accountable human review.
Key classes:
    Discovery.
Out-of-scope:
    Publication, patent workflows, automatic novelty claims, and persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from asrp_scios.contracts._validation import require_optional_non_empty
from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.lifecycle import LifecycleStatus
from asrp_scios.domain.value_objects import (
    AggregateId,
    EntityId,
    HumanReviewMetadata,
)

from .base import create_aggregate_event, freeze_entity_ids


@dataclass(frozen=True, slots=True, kw_only=True)
class Discovery(ScientificEntity):
    """AGG-001 discovery root with evidence-backed validation semantics."""

    id: AggregateId
    evidence_collection_ids: tuple[EntityId, ...] = ()
    validation_decision_ids: tuple[EntityId, ...] = ()
    validation_scope: str | None = None
    knowledge_item_ids: tuple[EntityId, ...] = ()
    human_review: HumanReviewMetadata | None = None

    def __post_init__(self) -> None:
        super(Discovery, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        for field_name in (
            "evidence_collection_ids",
            "validation_decision_ids",
            "knowledge_item_ids",
        ):
            object.__setattr__(
                self, field_name, freeze_entity_ids(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self,
            "validation_scope",
            require_optional_non_empty(self.validation_scope, "validation_scope"),
        )
        if self.human_review is not None and not isinstance(
            self.human_review, HumanReviewMetadata
        ):
            raise TypeError("human_review must be HumanReviewMetadata when provided")
        if self.status is LifecycleStatus.VALIDATED:
            if not self.evidence_collection_ids or not self.validation_decision_ids:
                raise ValueError(
                    "Discovery cannot validate without evidence and validation decisions"
                )
            if self.validation_scope is None:
                raise ValueError("validated Discovery requires a validation scope")
            if self.human_review is None or not self.human_review.is_complete:
                raise ValueError("validated Discovery requires completed human review")

    def validate(
        self,
        *,
        evidence_collection_ids: tuple[EntityId, ...],
        validation_decision_ids: tuple[EntityId, ...],
        validation_scope: str,
        human_review: HumanReviewMetadata,
        validated_at: datetime,
        validated_by: str,
    ) -> tuple[Discovery, ScientificEvent]:
        """Validate a discovery only within an explicit, reviewed scope."""
        evidence = freeze_entity_ids(evidence_collection_ids, "evidence_collection_ids")
        decisions = freeze_entity_ids(
            validation_decision_ids, "validation_decision_ids"
        )
        scope = require_optional_non_empty(validation_scope, "validation_scope")
        if not evidence or not decisions:
            raise ValueError(
                "Discovery cannot validate without evidence and validation decisions"
            )
        if scope is None:
            raise ValueError("validated Discovery requires a validation scope")
        if not isinstance(human_review, HumanReviewMetadata) or not human_review.is_complete:
            raise ValueError("validation requires completed human review")
        updated = replace(
            self,
            status=LifecycleStatus.VALIDATED,
            evidence_collection_ids=evidence,
            validation_decision_ids=decisions,
            validation_scope=scope,
            human_review=human_review,
            version=self.version.next_patch(),
            updated_at=validated_at,
        )
        event = create_aggregate_event(
            updated,
            "DiscoveryValidated",
            produced_by=validated_by,
            payload={
                "evidence_collection_ids": tuple(map(str, evidence)),
                "validation_decision_ids": tuple(map(str, decisions)),
                "validation_scope": scope,
            },
            occurred_at=validated_at,
            related_entity_ids=evidence + decisions,
            human_review=human_review,
        )
        return updated, event
