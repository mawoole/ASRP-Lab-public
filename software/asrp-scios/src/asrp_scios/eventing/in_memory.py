"""In-memory reference implementation of the event bus contract.

Purpose:
    Support deterministic local execution and tests without infrastructure.
Responsibilities:
    Register handlers, deliver matching immutable events in subscription order,
    and cancel subscriptions safely.
Inputs:
    ``ScientificEvent`` instances and synchronous event handlers.
Outputs:
    Immediate in-process handler invocations.
Dependencies:
    ASRP-SciOS event contracts and Python synchronization primitives.
Limitations:
    Events are not persisted, retried, replayed, or distributed. Handler errors
    fail fast and are propagated to the publisher.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from threading import Lock, RLock
from collections.abc import Callable

from asrp_scios.contracts.events import (
    EventHandler,
    ScientificEvent,
    Subscription,
)
from asrp_scios.contracts._validation import require_non_empty


@dataclass(frozen=True, slots=True)
class _Subscriber:
    token: int
    event_type: str | None
    handler: EventHandler


class _InMemorySubscription(Subscription):
    def __init__(self, cancel_callback: Callable[[], None]) -> None:
        self._cancel_callback = cancel_callback
        self._cancelled = False
        self._lock = Lock()

    def cancel(self) -> None:
        with self._lock:
            if self._cancelled:
                return
            self._cancelled = True
        self._cancel_callback()


class InMemoryEventBus:
    """A thread-safe, synchronous, and non-durable event bus adapter."""

    def __init__(self) -> None:
        self._subscribers: dict[int, _Subscriber] = {}
        self._tokens = count(1)
        self._lock = RLock()

    def subscribe(
        self, event_type: str | None, handler: EventHandler
    ) -> Subscription:
        """Subscribe in registration order; ``None`` observes every event type."""
        if event_type is not None:
            event_type = require_non_empty(event_type, "event_type")
        if not callable(handler):
            raise TypeError("handler must be callable")

        with self._lock:
            token = next(self._tokens)
            self._subscribers[token] = _Subscriber(token, event_type, handler)

        return _InMemorySubscription(lambda: self._cancel(token))

    def publish(self, event: ScientificEvent) -> None:
        """Deliver from a snapshot and propagate the first handler failure."""
        if not isinstance(event, ScientificEvent):
            raise TypeError("event must be a ScientificEvent")
        with self._lock:
            subscribers = tuple(self._subscribers.values())

        for subscriber in subscribers:
            if subscriber.event_type is None or subscriber.event_type == event.event_type:
                subscriber.handler(event)

    def _cancel(self, token: int) -> None:
        with self._lock:
            self._subscribers.pop(token, None)

