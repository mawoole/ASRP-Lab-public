"""Integration test for plugin lifecycle over the injected event bus contract."""

import unittest

from asrp_scios.contracts import ScientificEvent, Traceability
from asrp_scios.eventing import InMemoryEventBus
from asrp_scios.kernel import Kernel, KernelContext, PluginManifest


class EventRecordingPlugin:
    manifest = PluginManifest(
        plugin_id="event-recorder",
        name="Event Recorder",
        version="1.0.0",
        capabilities=("record-test-events",),
    )

    def __init__(self) -> None:
        self.observed: list[ScientificEvent] = []
        self._subscription = None

    def start(self, context: KernelContext) -> None:
        self._subscription = context.event_bus.subscribe(
            "EvidenceAdded", self.observed.append
        )

    def stop(self) -> None:
        if self._subscription is not None:
            self._subscription.cancel()


class KernelEventIntegrationTests(unittest.TestCase):
    def test_plugin_communicates_through_injected_event_bus(self) -> None:
        bus = InMemoryEventBus()
        kernel = Kernel(bus)
        plugin = EventRecordingPlugin()
        kernel.register(plugin)
        kernel.start()
        evidence_added = ScientificEvent.create(
            event_type="EvidenceAdded",
            source="integration-test",
            traceability=Traceability(
                requirements=("Sprint-001",),
                decisions=("ADR-0002",),
                specifications=("ARC-001", "RFC-0001"),
                implementation_version="0.1.0",
            ),
            payload={"evidence_id": "evidence-1"},
        )

        bus.publish(evidence_added)
        kernel.stop()
        bus.publish(evidence_added)

        self.assertEqual(plugin.observed, [evidence_added])


if __name__ == "__main__":
    unittest.main()

