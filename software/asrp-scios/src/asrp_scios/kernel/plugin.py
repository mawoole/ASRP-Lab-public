"""Microkernel plugin lifecycle contracts.

Purpose:
    Define the smallest stable interface needed to extend ASRP-SciOS.
Responsibilities:
    Identify plugins and provide lifecycle access to an injected event bus.
Inputs:
    Plugin manifests and a kernel context.
Outputs:
    Started and stopped domain-independent extensions.
Dependencies:
    The ASRP-SciOS event bus contract and Python standard library.
Limitations:
    Dependency resolution, dynamic loading, isolation, and remote plugins are
    outside Sprint-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from asrp_scios.contracts._validation import freeze_strings, require_non_empty
from asrp_scios.contracts.events import EventBus


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Stable identity and capability metadata for a kernel extension."""

    plugin_id: str
    name: str
    version: str
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("plugin_id", "name", "version"):
            object.__setattr__(
                self,
                field_name,
                require_non_empty(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "capabilities",
            freeze_strings(self.capabilities, "capabilities"),
        )


@dataclass(frozen=True, slots=True)
class KernelContext:
    """Minimal services supplied to plugins without exposing kernel internals."""

    event_bus: EventBus

    def __post_init__(self) -> None:
        if not isinstance(self.event_bus, EventBus):
            raise TypeError("event_bus must implement the EventBus contract")


@runtime_checkable
class Plugin(Protocol):
    """A replaceable ASRP-SciOS capability managed by the microkernel."""

    @property
    def manifest(self) -> PluginManifest:
        """Return immutable plugin identity and capability metadata."""

    def start(self, context: KernelContext) -> None:
        """Acquire resources and begin handling events."""

    def stop(self) -> None:
        """Release resources; repeated calls are not required."""

