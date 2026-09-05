"""Structural capability contract from CAP-001.

Purpose:
    Define how providers expose validation and descriptive contract behavior.
Responsibilities:
    Specify input validation and output/limitation descriptions structurally.
Key classes:
    CapabilityContract.
Out-of-scope:
    Invocation, provider selection, routing, orchestration, and side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from .model import CapabilityDescriptor, CapabilityOutput


@runtime_checkable
class CapabilityContract(Protocol):
    """Implementation-neutral interface that a capability provider may expose."""

    @property
    def descriptor(self) -> CapabilityDescriptor:
        """Return the immutable capability declaration."""
        ...

    def validate_inputs(self, inputs: Mapping[str, object]) -> None:
        """Raise a validation error when inputs do not meet the declaration."""
        ...

    def describe_outputs(self) -> tuple[CapabilityOutput, ...]:
        """Describe possible outputs without executing the capability."""
        ...

    def describe_limitations(self) -> tuple[str, ...]:
        """Describe known limitations without selecting or invoking a provider."""
        ...
