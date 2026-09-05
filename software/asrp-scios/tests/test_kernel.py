"""Tests for deterministic microkernel plugin lifecycle behavior."""

from __future__ import annotations

import unittest

from asrp_scios.eventing import InMemoryEventBus
from asrp_scios.kernel import (
    DuplicatePluginError,
    Kernel,
    KernelContext,
    KernelState,
    KernelStateError,
    PluginManifest,
    PluginStartError,
    PluginStopError,
)


class RecordingPlugin:
    def __init__(
        self,
        plugin_id: str,
        calls: list[str],
        *,
        fail_start: bool = False,
        fail_stop: bool = False,
    ) -> None:
        self.manifest = PluginManifest(
            plugin_id=plugin_id,
            name=plugin_id,
            version="1.0.0",
            capabilities=("test",),
        )
        self._calls = calls
        self._fail_start = fail_start
        self._fail_stop = fail_stop
        self.context: KernelContext | None = None

    def start(self, context: KernelContext) -> None:
        self.context = context
        self._calls.append(f"start:{self.manifest.plugin_id}")
        if self._fail_start:
            raise RuntimeError("start failure")

    def stop(self) -> None:
        self._calls.append(f"stop:{self.manifest.plugin_id}")
        if self._fail_stop:
            raise RuntimeError("stop failure")


class KernelTests(unittest.TestCase):
    def test_starts_in_registration_order_and_stops_in_reverse(self) -> None:
        bus = InMemoryEventBus()
        kernel = Kernel(bus)
        calls: list[str] = []
        first = RecordingPlugin("first", calls)
        second = RecordingPlugin("second", calls)
        kernel.register(first)
        kernel.register(second)

        kernel.start()
        self.assertEqual(kernel.state, KernelState.RUNNING)
        self.assertIs(first.context.event_bus, bus)  # type: ignore[union-attr]
        kernel.stop()

        self.assertEqual(kernel.state, KernelState.STOPPED)
        self.assertEqual(
            calls,
            ["start:first", "start:second", "stop:second", "stop:first"],
        )

    def test_rejects_duplicate_plugin_identity(self) -> None:
        kernel = Kernel(InMemoryEventBus())
        kernel.register(RecordingPlugin("duplicate", []))

        with self.assertRaises(DuplicatePluginError):
            kernel.register(RecordingPlugin("duplicate", []))

    def test_start_failure_rolls_back_started_plugins(self) -> None:
        kernel = Kernel(InMemoryEventBus())
        calls: list[str] = []
        kernel.register(RecordingPlugin("started", calls))
        kernel.register(RecordingPlugin("failing", calls, fail_start=True))

        with self.assertRaises(PluginStartError) as raised:
            kernel.start()

        self.assertEqual(raised.exception.plugin_id, "failing")
        self.assertEqual(kernel.state, KernelState.FAILED)
        self.assertEqual(calls, ["start:started", "start:failing", "stop:started"])

    def test_stop_attempts_every_plugin_before_reporting_failures(self) -> None:
        kernel = Kernel(InMemoryEventBus())
        calls: list[str] = []
        kernel.register(RecordingPlugin("first", calls))
        kernel.register(RecordingPlugin("failing", calls, fail_stop=True))
        kernel.start()

        with self.assertRaises(PluginStopError) as raised:
            kernel.stop()

        self.assertEqual(kernel.state, KernelState.FAILED)
        self.assertEqual(raised.exception.failures[0][0], "failing")
        self.assertEqual(calls[-2:], ["stop:failing", "stop:first"])

    def test_registration_is_closed_after_startup(self) -> None:
        kernel = Kernel(InMemoryEventBus())
        kernel.start()

        with self.assertRaises(KernelStateError):
            kernel.register(RecordingPlugin("late", []))
        kernel.stop()


if __name__ == "__main__":
    unittest.main()

