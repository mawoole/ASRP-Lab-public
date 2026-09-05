"""ResearchCampaign aggregate root.

Purpose:
    Bound a coordinated scientific effort within exactly one research program.
Responsibilities:
    Track question/hypothesis/evidence references and enforce decision-backed closure.
Key classes:
    ResearchCampaign.
Out-of-scope:
    Task scheduling, workflow execution, persistence, and resource allocation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.lifecycle import LifecycleStatus
from asrp_scios.domain.value_objects import AggregateId, EntityId

from .base import create_aggregate_event, freeze_entity_ids


@dataclass(frozen=True, slots=True, kw_only=True)
class ResearchCampaign(ScientificEntity):
    """AGG-001 campaign root belonging to exactly one program."""

    id: AggregateId
    program_id: EntityId
    question_ids: tuple[EntityId, ...] = ()
    hypothesis_ids: tuple[EntityId, ...] = ()
    evidence_collection_ids: tuple[EntityId, ...] = ()
    closure_decision_id: EntityId | None = None

    def __post_init__(self) -> None:
        super(ResearchCampaign, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        if not isinstance(self.program_id, EntityId):
            raise TypeError("program_id must be an EntityId")
        for field_name in (
            "question_ids",
            "hypothesis_ids",
            "evidence_collection_ids",
        ):
            object.__setattr__(
                self, field_name, freeze_entity_ids(getattr(self, field_name), field_name)
            )
        if self.closure_decision_id is not None and not isinstance(
            self.closure_decision_id, EntityId
        ):
            raise TypeError("closure_decision_id must be an EntityId")
        if self.status is LifecycleStatus.ARCHIVED and self.closure_decision_id is None:
            raise ValueError("closed or archived campaign requires a closure decision")

    def close(
        self, decision_id: EntityId, *, closed_at: datetime, closed_by: str
    ) -> tuple[ResearchCampaign, ScientificEvent]:
        """Close this campaign only with an explicit governance decision."""
        if not isinstance(decision_id, EntityId):
            raise TypeError("decision_id must be an EntityId")
        updated = replace(
            self,
            status=LifecycleStatus.ARCHIVED,
            closure_decision_id=decision_id,
            version=self.version.next_patch(),
            updated_at=closed_at,
        )
        event = create_aggregate_event(
            updated,
            "ResearchCampaignClosed",
            produced_by=closed_by,
            payload={"closure_decision_id": str(decision_id)},
            occurred_at=closed_at,
            related_entity_ids=(decision_id,),
            scientific_program_id=self.program_id,
            research_campaign_id=self.id,
        )
        return updated, event
