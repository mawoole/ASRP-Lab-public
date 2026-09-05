"""ContextSnapshot aggregate root.

Purpose:
    Capture immutable scientific context for later reconstruction and audit.
Responsibilities:
    Freeze context data and bind it to at least one task or mission reference.
Key classes:
    ContextSnapshot.
Out-of-scope:
    Storage, restoration orchestration, user sessions, and snapshot scheduling.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime

from asrp_scios.contracts._validation import ContractValue, freeze_mapping
from asrp_scios.domain.entities import ScientificEntity
from asrp_scios.domain.events import ScientificEvent
from asrp_scios.domain.lifecycle import LifecycleStatus
from asrp_scios.domain.value_objects import AggregateId, EntityId

from .base import create_aggregate_event, freeze_entity_ids


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextSnapshot(ScientificEntity):
    """AGG-001 immutable context record referenced by scientific events."""

    id: AggregateId
    mission_reference: EntityId | None = None
    task_reference: EntityId | None = None
    context_data: Mapping[str, ContractValue] = field(default_factory=dict, hash=False)
    scientific_entity_ids: tuple[EntityId, ...] = ()

    def __post_init__(self) -> None:
        super(ContextSnapshot, self).__post_init__()
        if not isinstance(self.id, AggregateId):
            raise TypeError("id must be an AggregateId")
        for field_name in ("mission_reference", "task_reference"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, EntityId):
                raise TypeError(f"{field_name} must be an EntityId when provided")
        if self.mission_reference is None and self.task_reference is None:
            raise ValueError("ContextSnapshot requires a task or mission reference")
        object.__setattr__(self, "context_data", freeze_mapping(self.context_data))
        object.__setattr__(
            self,
            "scientific_entity_ids",
            freeze_entity_ids(self.scientific_entity_ids, "scientific_entity_ids"),
        )

    def archive(
        self, *, archived_at: datetime, archived_by: str
    ) -> tuple[ContextSnapshot, ScientificEvent]:
        """Return a separately versioned archived snapshot; never mutate the source."""
        updated = replace(
            self,
            status=LifecycleStatus.ARCHIVED,
            version=self.version.next_patch(),
            updated_at=archived_at,
        )
        event = create_aggregate_event(
            updated,
            "ContextSnapshotArchived",
            produced_by=archived_by,
            payload={
                "mission_reference": (
                    str(self.mission_reference) if self.mission_reference else None
                ),
                "task_reference": str(self.task_reference) if self.task_reference else None,
            },
            occurred_at=archived_at,
            related_entity_ids=self.scientific_entity_ids,
            context_snapshot_id=self.id,
        )
        return updated, event
