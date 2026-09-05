"""Replaceable eventing adapters for ASRP-SciOS.

Purpose:
    Expose infrastructure implementations of the stable event bus contract.
Responsibilities:
    Provide the Sprint-001 in-memory adapter.
Inputs:
    Immutable scientific events and subscriptions.
Outputs:
    In-process event delivery.
Dependencies:
    ``asrp_scios.contracts`` and the Python standard library.
Limitations:
    Durable or distributed adapters are intentionally deferred.
"""

from .in_memory import InMemoryEventBus

__all__ = ["InMemoryEventBus"]

