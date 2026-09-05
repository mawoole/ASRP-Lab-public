"""Immutable EVT-001 event envelope and descriptors.

Purpose:
    Represent meaningful scientific and platform facts without delivery infrastructure.
Responsibilities:
    Validate event names, categories, versions, provenance, traceability, and payloads.
Key classes:
    ScientificEvent, EventDescriptor, and EventCategory.
Out-of-scope:
    Event buses, storage, replay, retries, delivery guarantees, and projections.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Self

from asrp_scios.contracts._validation import (
    ContractValue,
    freeze_mapping,
    require_aware_datetime,
    require_non_empty,
)
from asrp_scios.domain.value_objects import (
    AggregateId,
    EntityId,
    EventId,
    HumanReviewMetadata,
    Provenance,
    Traceability,
    Version,
)


class EventCategory(str, Enum):
    RESEARCH = "Research"
    SCIENTIFIC_METHOD = "ScientificMethod"
    KNOWLEDGE = "Knowledge"
    GOVERNANCE = "Governance"
    EXECUTION = "Execution"
    PLATFORM = "Platform"
    INTEGRATION = "Integration"


_EVENT_NAME_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_PAST_TENSE_SUFFIXES = (
    "Accepted",
    "Added",
    "Approved",
    "Archived",
    "Assigned",
    "Blocked",
    "Branched",
    "Cancelled",
    "Changed",
    "Classified",
    "Closed",
    "Collected",
    "Completed",
    "Created",
    "Decreased",
    "Declared",
    "Deprecated",
    "Drafted",
    "Executed",
    "Failed",
    "Filed",
    "Generated",
    "Increased",
    "Invalidated",
    "Investigated",
    "Linked",
    "Merged",
    "Planned",
    "Proposed",
    "Published",
    "Recorded",
    "Refined",
    "Registered",
    "Rejected",
    "Requested",
    "Required",
    "Resolved",
    "Reversed",
    "Reviewed",
    "Started",
    "Stopped",
    "Superseded",
    "Updated",
    "Validated",
)


def validate_event_name(value: str) -> str:
    """Validate the canonical ``<DomainObject><PastTenseAction>`` convention."""
    normalized = require_non_empty(value, "event_type")
    if not _EVENT_NAME_PATTERN.fullmatch(normalized):
        raise ValueError("event_type must use PascalCase without separators")
    has_past_tense_action = normalized.endswith(_PAST_TENSE_SUFFIXES) or any(
        re.search(rf"{suffix}(?=[A-Z])", normalized)
        for suffix in _PAST_TENSE_SUFFIXES
    )
    if not has_past_tense_action:
        raise ValueError(
            f"event_type must describe a canonical past-tense fact: {normalized}"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class EventDescriptor:
    """A stable event type, family, source aggregate, and schema version."""

    event_type: str
    category: EventCategory
    aggregate_type: str
    version: Version = Version(1, 0, 0)
    human_review_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_type", validate_event_name(self.event_type))
        if not isinstance(self.category, EventCategory):
            raise TypeError("category must be an EventCategory")
        object.__setattr__(
            self,
            "aggregate_type",
            require_non_empty(self.aggregate_type, "aggregate_type"),
        )
        if not isinstance(self.version, Version):
            raise TypeError("version must be a Version")
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be a boolean")


@dataclass(frozen=True, slots=True, kw_only=True)
class ScientificEvent:
    """An immutable EVT-001 fact with the complete domain envelope."""

    event_id: EventId
    event_type: str
    event_category: EventCategory
    event_version: Version
    occurred_at: datetime
    produced_by: str
    aggregate_id: AggregateId
    aggregate_type: str
    provenance: Provenance
    traceability: Traceability
    payload: Mapping[str, ContractValue] = field(hash=False)
    recorded_at: datetime | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    scientific_program_id: EntityId | None = None
    research_campaign_id: EntityId | None = None
    context_snapshot_id: EntityId | None = None
    related_entity_ids: tuple[EntityId, ...] = ()
    human_review: HumanReviewMetadata | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, EventId):
            raise TypeError("event_id must be an EventId")
        object.__setattr__(self, "event_type", validate_event_name(self.event_type))
        if not isinstance(self.event_category, EventCategory):
            raise TypeError("event_category must be an EventCategory")
        if not isinstance(self.event_version, Version):
            raise TypeError("event_version must be a Version")
        object.__setattr__(
            self,
            "occurred_at",
            require_aware_datetime(self.occurred_at, "occurred_at"),
        )
        object.__setattr__(
            self, "produced_by", require_non_empty(self.produced_by, "produced_by")
        )
        if not isinstance(self.aggregate_id, AggregateId):
            raise TypeError("aggregate_id must be an AggregateId")
        object.__setattr__(
            self,
            "aggregate_type",
            require_non_empty(self.aggregate_type, "aggregate_type"),
        )
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance record")
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")
        object.__setattr__(self, "payload", freeze_mapping(self.payload))
        if self.recorded_at is not None:
            object.__setattr__(
                self,
                "recorded_at",
                require_aware_datetime(self.recorded_at, "recorded_at"),
            )
        for field_name in ("correlation_id", "causation_id"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self, field_name, require_non_empty(value, field_name)
                )
        for field_name in (
            "scientific_program_id",
            "research_campaign_id",
            "context_snapshot_id",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, EntityId):
                raise TypeError(f"{field_name} must be an EntityId when provided")
        related = tuple(self.related_entity_ids)
        if not all(isinstance(value, EntityId) for value in related):
            raise TypeError("related_entity_ids must contain EntityId values")
        object.__setattr__(self, "related_entity_ids", related)
        if self.human_review is not None and not isinstance(
            self.human_review, HumanReviewMetadata
        ):
            raise TypeError("human_review must be HumanReviewMetadata when provided")

    @classmethod
    def create(
        cls,
        descriptor: EventDescriptor,
        *,
        produced_by: str,
        aggregate_id: AggregateId,
        provenance: Provenance,
        traceability: Traceability,
        payload: Mapping[str, object],
        occurred_at: datetime | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        scientific_program_id: EntityId | None = None,
        research_campaign_id: EntityId | None = None,
        context_snapshot_id: EntityId | None = None,
        related_entity_ids: tuple[EntityId, ...] = (),
        human_review: HumanReviewMetadata | None = None,
    ) -> Self:
        """Create a validated event from a catalog descriptor."""
        if not isinstance(descriptor, EventDescriptor):
            raise TypeError("descriptor must be an EventDescriptor")
        if descriptor.human_review_required and (
            human_review is None or not human_review.is_complete
        ):
            raise ValueError(
                f"{descriptor.event_type} requires completed human review metadata"
            )
        event_time = occurred_at or datetime.now(timezone.utc)
        return cls(
            event_id=EventId.generate(),
            event_type=descriptor.event_type,
            event_category=descriptor.category,
            event_version=descriptor.version,
            occurred_at=event_time,
            recorded_at=event_time,
            produced_by=produced_by,
            aggregate_id=aggregate_id,
            aggregate_type=descriptor.aggregate_type,
            correlation_id=correlation_id,
            causation_id=causation_id,
            scientific_program_id=scientific_program_id,
            research_campaign_id=research_campaign_id,
            context_snapshot_id=context_snapshot_id,
            provenance=provenance,
            traceability=traceability,
            related_entity_ids=related_entity_ids,
            human_review=human_review,
            payload=freeze_mapping(payload),
        )
