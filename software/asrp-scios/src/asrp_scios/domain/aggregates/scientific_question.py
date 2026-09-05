"""ScientificQuestion aggregate root.

Purpose:
    Preserve the exact research question and its traceable resolution.
Responsibilities:
    Validate the question statement and require decision or knowledge on resolution.
Key classes:
    ScientificQuestion.
Out-of-scope:
    Hypothesis generation algorithms, search, persistence, and campaign workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from asrp_scios.contracts._validation import require_non_empty
from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.lifecycle import LifecycleStatus
from asrp_scios.domain.value_objects import AggregateId, EntityId

from .base import create_aggregate_event, freeze_entity_ids


@dataclass(frozen=True, slots=True, kw_only=True)
class ScientificQuestion(ScientificEntity):
    """AGG-001 question root with explicit downstream references."""

    id: AggregateId
    statement: str
    campaign_ids: tuple[EntityId, ...] = ()
    hypothesis_ids: tuple[EntityId, ...] = ()
    resolution_decision_id: EntityId | None = None
    knowledge_item_ids: tuple[EntityId, ...] = ()

    def __post_init__(self) -> None:
        super(ScientificQuestion, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        object.__setattr__(self, "statement", require_non_empty(self.statement, "statement"))
        for field_name in ("campaign_ids", "hypothesis_ids", "knowledge_item_ids"):
            object.__setattr__(
                self, field_name, freeze_entity_ids(getattr(self, field_name), field_name)
            )
        if self.resolution_decision_id is not None and not isinstance(
            self.resolution_decision_id, EntityId
        ):
            raise TypeError("resolution_decision_id must be an EntityId")
        if self.status is LifecycleStatus.VALIDATED and not (
            self.resolution_decision_id or self.knowledge_item_ids
        ):
            raise ValueError(
                "resolved ScientificQuestion requires a decision or knowledge reference"
            )

    def resolve(
        self,
        *,
        resolved_at: datetime,
        resolved_by: str,
        decision_id: EntityId | None = None,
        knowledge_item_ids: tuple[EntityId, ...] = (),
    ) -> tuple[ScientificQuestion, ScientificEvent]:
        """Return a decision- or knowledge-backed resolved question."""
        items = freeze_entity_ids(knowledge_item_ids, "knowledge_item_ids")
        if decision_id is not None and not isinstance(decision_id, EntityId):
            raise TypeError("decision_id must be an EntityId")
        if decision_id is None and not items:
            raise ValueError("question resolution requires a decision or knowledge")
        updated = replace(
            self,
            status=LifecycleStatus.VALIDATED,
            resolution_decision_id=decision_id,
            knowledge_item_ids=items,
            version=self.version.next_patch(),
            updated_at=resolved_at,
        )
        references = ((decision_id,) if decision_id else ()) + items
        event = create_aggregate_event(
            updated,
            "ScientificQuestionResolved",
            produced_by=resolved_by,
            payload={
                "decision_id": str(decision_id) if decision_id else None,
                "knowledge_item_ids": tuple(map(str, items)),
            },
            occurred_at=resolved_at,
            related_entity_ids=references,
        )
        return updated, event
