"""Shared aggregate-root protocol and event-construction helpers.

Purpose:
    Define the domain-facing aggregate boundary required by AGG-001.
Responsibilities:
    Describe aggregate roots and construct immutable EVT-001 facts after changes.
Key classes:
    AggregateRoot.
Out-of-scope:
    Repositories, units of work, event buses, persistence, and orchestration.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, runtime_checkable

from asrp_scios.domain.events import ScientificEvent, get_event_descriptor
from asrp_scios.domain.value_objects import (
    AggregateId,
    EntityId,
    HumanReviewMetadata,
    Provenance,
    Traceability,
    Version,
)


@runtime_checkable
class AggregateRoot(Protocol):
    """Structural contract implemented by every scientific aggregate root."""

    id: AggregateId
    version: Version
    provenance: Provenance
    traceability: Traceability


def freeze_entity_ids(
    values: tuple[EntityId, ...], field_name: str
) -> tuple[EntityId, ...]:
    """Validate an immutable collection of cross-aggregate references."""
    frozen = tuple(values)
    if not all(isinstance(value, EntityId) for value in frozen):
        raise TypeError(f"{field_name} must contain EntityId values")
    return frozen


def create_aggregate_event(
    aggregate: AggregateRoot,
    event_type: str,
    *,
    produced_by: str,
    payload: Mapping[str, object],
    occurred_at: datetime,
    related_entity_ids: tuple[EntityId, ...] = (),
    human_review: HumanReviewMetadata | None = None,
    scientific_program_id: EntityId | None = None,
    research_campaign_id: EntityId | None = None,
    context_snapshot_id: EntityId | None = None,
) -> ScientificEvent:
    """Create a catalogued event for a completed aggregate transition."""
    descriptor = get_event_descriptor(event_type)
    if descriptor.aggregate_type != type(aggregate).__name__:
        raise ValueError(
            f"{event_type} belongs to {descriptor.aggregate_type}, not "
            f"{type(aggregate).__name__}"
        )
    return ScientificEvent.create(
        descriptor,
        produced_by=produced_by,
        aggregate_id=aggregate.id,
        provenance=aggregate.provenance,
        traceability=aggregate.traceability,
        payload=payload,
        occurred_at=occurred_at,
        related_entity_ids=related_entity_ids,
        human_review=human_review,
        scientific_program_id=scientific_program_id,
        research_campaign_id=research_campaign_id,
        context_snapshot_id=context_snapshot_id,
    )
