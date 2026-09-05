"""Tests for the in-memory event bus adapter."""

import unittest

from asrp_scios.contracts import EventBus, ScientificEvent, Traceability
from asrp_scios.eventing import InMemoryEventBus


def event(event_type: str = "HypothesisCreated") -> ScientificEvent:
    return ScientificEvent.create(
        event_type=event_type,
        source="test.publisher",
        traceability=Traceability(
            requirements=("Sprint-001",),
            decisions=("ADR-0002",),
            specifications=("ARC-001",),
            implementation_version="0.1.0",
        ),
    )


class InMemoryEventBusTests(unittest.TestCase):
    def test_implements_event_bus_contract(self) -> None:
        self.assertIsInstance(InMemoryEventBus(), EventBus)

    def test_delivers_matching_and_wildcard_handlers_in_registration_order(self) -> None:
        bus = InMemoryEventBus()
        observed: list[str] = []
        bus.subscribe(None, lambda _: observed.append("all-first"))
        bus.subscribe("HypothesisCreated", lambda _: observed.append("matching"))
        bus.subscribe("EvidenceAdded", lambda _: observed.append("different"))
        bus.subscribe(None, lambda _: observed.append("all-last"))

        bus.publish(event())

        self.assertEqual(observed, ["all-first", "matching", "all-last"])

    def test_cancel_is_idempotent(self) -> None:
        bus = InMemoryEventBus()
        observed: list[ScientificEvent] = []
        subscription = bus.subscribe(None, observed.append)

        subscription.cancel()
        subscription.cancel()
        bus.publish(event())

        self.assertEqual(observed, [])

    def test_handler_errors_are_not_silently_ignored(self) -> None:
        bus = InMemoryEventBus()
        observed: list[str] = []

        def fail(_: ScientificEvent) -> None:
            raise RuntimeError("delivery failed")

        bus.subscribe(None, fail)
        bus.subscribe(None, lambda _: observed.append("not called"))

        with self.assertRaisesRegex(RuntimeError, "delivery failed"):
            bus.publish(event())
        self.assertEqual(observed, [])

    def test_rejects_invalid_inputs(self) -> None:
        bus = InMemoryEventBus()
        with self.assertRaises(ValueError):
            bus.subscribe(" ", lambda _: None)
        with self.assertRaises(TypeError):
            bus.publish("not an event")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

