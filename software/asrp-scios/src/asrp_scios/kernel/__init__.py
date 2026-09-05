"""Public microkernel API for ASRP-SciOS.

Purpose:
    Expose the stable plugin lifecycle and minimal kernel runtime.
Responsibilities:
    Re-export manifests, context, states, runtime, and meaningful failures.
Inputs:
    An injected event bus and domain-independent plugins.
Outputs:
    Deterministic plugin lifecycle management.
Dependencies:
    ``asrp_scios.contracts`` and the Python standard library.
Limitations:
    Infrastructure orchestration and scientific workflows remain plugins or
    future services, never kernel responsibilities.
"""

from .plugin import KernelContext, Plugin, PluginManifest
from .runtime import (
    DuplicatePluginError,
    Kernel,
    KernelError,
    KernelState,
    KernelStateError,
    PluginStartError,
    PluginStopError,
)

__all__ = [
    "DuplicatePluginError",
    "Kernel",
    "KernelContext",
    "KernelError",
    "KernelState",
    "KernelStateError",
    "Plugin",
    "PluginManifest",
    "PluginStartError",
    "PluginStopError",
]
