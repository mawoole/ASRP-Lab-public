"""Immutable scientific event and event bus contracts.

Purpose:
    Provide the stable communication boundary required by event-driven ASRP-SciOS.
Responsibilities:
    Define immutable event envelopes, subscriptions, handlers, and bus behavior.
Inputs:
    Traceable event metadata and JSON-compatible payloads.
Outputs:
    Scientific events delivered to matching handlers.
Dependencies:
    Shared ASRP-SciOS contracts and the Python standard library.
Limitations:
    Delivery durability, retries, ordering across processes, and persistence are
    responsibilities of replaceable event bus adapters.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, Self, runtime_checkable
from uuid import UUID, uuid4

from ._validation import (
    ContractValue,
    freeze_mapping,
    require_aware_datetime,
    require_non_empty,
    require_optional_non_empty,
)
from .common import Traceability


@dataclass(frozen=True, slots=True)
class ScientificEvent:
    """An immutable and traceable change in the scientific process."""

    event_id: str
    event_type: str
    occurred_at: datetime
    source: str
    traceability: Traceability
    payload: Mapping[str, ContractValue] = field(
        default_factory=lambda: freeze_mapping(None), hash=False
    )
    correlation_id: str | None = None
    causation_id: str | None = None

    def __post_init__(self) -> None:
        normalized_id = require_non_empty(self.event_id, "event_id")
        try:
            UUID(normalized_id)
        except ValueError as error:
            raise ValueError("event_id must be a valid UUID") from error
        object.__setattr__(self, "event_id", normalized_id)
        object.__setattr__(
            self, "event_type", require_non_empty(self.event_type, "event_type")
        )
        object.__setattr__(
            self,
            "occurred_at",
            require_aware_datetime(self.occurred_at, "occurred_at"),
        )
        object.__setattr__(self, "source", require_non_empty(self.source, "source"))
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")
        object.__setattr__(self, "payload", freeze_mapping(self.payload))
        object.__setattr__(
            self,
            "correlation_id",
            require_optional_non_empty(self.correlation_id, "correlation_id"),
        )
        object.__setattr__(
            self,
            "causation_id",
            require_optional_non_empty(self.causation_id, "causation_id"),
        )

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        source: str,
        traceability: Traceability,
        payload: Mapping[str, object] | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> Self:
        """Create an event with a UTC timestamp and generated UUID."""
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            source=source,
            traceability=traceability,
            payload=freeze_mapping(payload),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


EventHandler = Callable[[ScientificEvent], None]


@runtime_checkable
class Subscription(Protocol):
    """A cancellable event subscription; cancellation must be idempotent."""

    def cancel(self) -> None:
        """Stop receiving events after the current dispatch, if any."""


@runtime_checkable
class EventBus(Protocol):
    """Replaceable event transport used by the kernel and plugins."""

    def subscribe(
        self, event_type: str | None, handler: EventHandler
    ) -> Subscription:
        """Subscribe to one event type, or all types when ``event_type`` is None."""

    def publish(self, event: ScientificEvent) -> None:
        """Deliver an event and surface delivery errors to the publisher."""

