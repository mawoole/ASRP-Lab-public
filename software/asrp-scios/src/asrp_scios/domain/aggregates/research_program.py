"""ResearchProgram aggregate root.

Purpose:
    Govern a long-lived scientific mission while preserving ontology identity.
Responsibilities:
    Hold mission/objectives and immutable references to campaigns and decisions.
Key classes:
    ResearchProgram.
Out-of-scope:
    Portfolio scheduling, funding, persistence, and campaign orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from asrp_scios.contracts._validation import require_non_empty
from asrp_scios.domain.entities import ScientificProgram
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.value_objects import AggregateId, EntityId

from .base import create_aggregate_event, freeze_entity_ids


@dataclass(frozen=True, slots=True, kw_only=True)
class ResearchProgram(ScientificProgram):
    """AGG-001 root and direct aggregate specialization of ScientificProgram."""

    id: AggregateId
    campaign_ids: tuple[EntityId, ...] = ()
    decision_ids: tuple[EntityId, ...] = ()

    def __post_init__(self) -> None:
        super(ResearchProgram, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        object.__setattr__(
            self, "campaign_ids", freeze_entity_ids(self.campaign_ids, "campaign_ids")
        )
        object.__setattr__(
            self, "decision_ids", freeze_entity_ids(self.decision_ids, "decision_ids")
        )

    def update_mission(
        self, mission: str, *, changed_at: datetime, changed_by: str
    ) -> tuple[ResearchProgram, ScientificEvent]:
        """Return a new program and fact for a meaningful mission change."""
        normalized = require_non_empty(mission, "mission")
        if normalized == self.mission:
            raise ValueError("mission update must change the current mission")
        updated = replace(
            self,
            mission=normalized,
            version=self.version.next_patch(),
            updated_at=changed_at,
        )
        event = create_aggregate_event(
            updated,
            "ResearchProgramMissionUpdated",
            produced_by=changed_by,
            payload={"previous_mission": self.mission, "mission": normalized},
            occurred_at=changed_at,
            scientific_program_id=updated.id,
        )
        return updated, event
