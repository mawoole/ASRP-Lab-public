"""Domain-independent capability model from CAP-001.

Purpose:
    Expose stable capability and provider declarations to future kernel extensions.
Responsibilities:
    Re-export descriptors, vocabularies, field contracts, and the provider protocol.
Key classes:
    CapabilityDescriptor, CapabilityProviderDescriptor, CapabilityContract,
    CapabilityCategory, and CapabilityReadinessLevel.
Out-of-scope:
    Invocation, provider selection, orchestration, registries, and adapters.
"""

from .model import (
    CapabilityCategory,
    CapabilityDescriptor,
    CapabilityInput,
    CapabilityOutput,
    CapabilityProviderDescriptor,
    CapabilityReadinessLevel,
    ProviderType,
)
from .protocol import CapabilityContract

__all__ = [
    "CapabilityCategory",
    "CapabilityContract",
    "CapabilityDescriptor",
    "CapabilityInput",
    "CapabilityOutput",
    "CapabilityProviderDescriptor",
    "CapabilityReadinessLevel",
    "ProviderType",
]
