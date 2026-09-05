"""Minimal ASRP-SciOS microkernel runtime.

Purpose:
    Manage domain-independent plugin registration and lifecycle.
Responsibilities:
    Enforce unique plugin identity, deterministic startup, reverse shutdown,
    failure visibility, and event bus dependency injection.
Inputs:
    An event bus implementation and plugins conforming to the plugin contract.
Outputs:
    A running set of independently replaceable extensions.
Dependencies:
    Kernel plugin contracts and the event bus abstraction.
Limitations:
    No discovery, hot reload, dependency graph, workflow, persistence, or
    process isolation is provided in Sprint-001.
"""

from __future__ import annotations

from enum import Enum

from asrp_scios.contracts.events import EventBus

from .plugin import KernelContext, Plugin, PluginManifest


class KernelState(Enum):
    """Observable lifecycle states for the microkernel."""

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class KernelError(RuntimeError):
    """Base class for meaningful microkernel failures."""


class KernelStateError(KernelError):
    """Raised when an operation is invalid in the current lifecycle state."""


class DuplicatePluginError(KernelError):
    """Raised when two plugins declare the same stable identifier."""


class PluginStartError(KernelError):
    """Raised when startup fails after previously started plugins are rolled back."""

    def __init__(
        self,
        plugin_id: str,
        rollback_failures: tuple[tuple[str, Exception], ...] = (),
    ) -> None:
        self.plugin_id = plugin_id
        self.rollback_failures = rollback_failures
        suffix = ""
        if rollback_failures:
            failed_ids = ", ".join(item[0] for item in rollback_failures)
            suffix = f"; rollback also failed for: {failed_ids}"
        super().__init__(f"plugin '{plugin_id}' failed to start{suffix}")


class PluginStopError(KernelError):
    """Raised after shutdown attempts every plugin and one or more stops fail."""

    def __init__(self, failures: tuple[tuple[str, Exception], ...]) -> None:
        self.failures = failures
        failed_ids = ", ".join(item[0] for item in failures)
        super().__init__(f"plugins failed to stop: {failed_ids}")


class Kernel:
    """A small lifecycle kernel whose only service dependency is ``EventBus``."""

    def __init__(self, event_bus: EventBus) -> None:
        if not isinstance(event_bus, EventBus):
            raise TypeError("event_bus must implement the EventBus contract")
        self._context = KernelContext(event_bus=event_bus)
        self._plugins: dict[str, Plugin] = {}
        self._state = KernelState.CREATED

    @property
    def state(self) -> KernelState:
        """Return the current lifecycle state."""
        return self._state

    @property
    def registered_plugins(self) -> tuple[PluginManifest, ...]:
        """Return manifests in deterministic registration order."""
        return tuple(plugin.manifest for plugin in self._plugins.values())

    def register(self, plugin: Plugin) -> None:
        """Register one plugin before startup without importing domain behavior."""
        if self._state is not KernelState.CREATED:
            raise KernelStateError("plugins can only be registered before kernel startup")
        if not isinstance(plugin, Plugin):
            raise TypeError("plugin must implement the Plugin contract")
        manifest = plugin.manifest
        if not isinstance(manifest, PluginManifest):
            raise TypeError("plugin manifest must be a PluginManifest")
        if manifest.plugin_id in self._plugins:
            raise DuplicatePluginError(
                f"plugin '{manifest.plugin_id}' is already registered"
            )
        self._plugins[manifest.plugin_id] = plugin

    def start(self) -> None:
        """Start plugins in registration order and roll back on failure."""
        if self._state is not KernelState.CREATED:
            raise KernelStateError("kernel can only be started once from created state")
        self._state = KernelState.STARTING
        started: list[Plugin] = []
        current_plugin_id = "<unknown>"
        try:
            for plugin in self._plugins.values():
                current_plugin_id = plugin.manifest.plugin_id
                plugin.start(self._context)
                started.append(plugin)
        except Exception as error:
            rollback_failures: list[tuple[str, Exception]] = []
            for plugin in reversed(started):
                try:
                    plugin.stop()
                except Exception as rollback_error:
                    rollback_failures.append(
                        (plugin.manifest.plugin_id, rollback_error)
                    )
            self._state = KernelState.FAILED
            raise PluginStartError(
                current_plugin_id, tuple(rollback_failures)
            ) from error
        self._state = KernelState.RUNNING

    def stop(self) -> None:
        """Attempt reverse-order shutdown and report every plugin failure."""
        if self._state is not KernelState.RUNNING:
            raise KernelStateError("kernel can only be stopped from running state")
        self._state = KernelState.STOPPING
        failures: list[tuple[str, Exception]] = []
        for plugin in reversed(tuple(self._plugins.values())):
            try:
                plugin.stop()
            except Exception as error:
                failures.append((plugin.manifest.plugin_id, error))

        if failures:
            self._state = KernelState.FAILED
            raise PluginStopError(tuple(failures))
        self._state = KernelState.STOPPED

