"""Public domain event envelope, categories, and EVT-001 catalog.

Purpose:
    Expose immutable event semantics independently of event transport.
Responsibilities:
    Provide the full baseline catalog and aggregate-to-event mappings.
Key classes:
    ScientificEvent, EventDescriptor, EventCategory, EVENT_CATALOG.
Out-of-scope:
    Event bus changes, durable recording, replay, retry, and delivery semantics.
"""

from .base import EventCategory, EventDescriptor, ScientificEvent, validate_event_name
from .catalog import AGGREGATE_EVENT_TYPES, EVENT_CATALOG, get_event_descriptor

__all__ = [
    "AGGREGATE_EVENT_TYPES",
    "EVENT_CATALOG",
    "EventCategory",
    "EventDescriptor",
    "ScientificEvent",
    "get_event_descriptor",
    "validate_event_name",
]
