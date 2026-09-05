"""Typed identifiers for the scientific domain.

Purpose:
    Prevent accidental interchange of entity, aggregate, event, capability,
    and provider identities.
Responsibilities:
    Validate stable, non-empty identifiers and generate globally unique event IDs.
Key classes:
    EntityId, AggregateId, EventId, CapabilityId, ProviderId.
Out-of-scope:
    Database keys, identity-provider integration, and allocation services.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Self
from uuid import uuid4


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


@dataclass(frozen=True, slots=True)
class _Identifier:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("identifier must be a non-empty string")
        normalized = self.value.strip()
        if not _IDENTIFIER_PATTERN.fullmatch(normalized):
            raise ValueError(
                "identifier may contain only letters, numbers, '.', '_', ':', and '-'"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EntityId(_Identifier):
    """Stable identity of a scientific entity."""


@dataclass(frozen=True, slots=True)
class AggregateId(EntityId):
    """Stable identity of an aggregate root."""


@dataclass(frozen=True, slots=True)
class EventId(_Identifier):
    """Globally unique identity of a domain event."""

    @classmethod
    def generate(cls) -> Self:
        """Create a UUID-backed event identity."""
        return cls(str(uuid4()))


@dataclass(frozen=True, slots=True)
class CapabilityId(_Identifier):
    """Stable, version-independent identity of a capability contract."""


@dataclass(frozen=True, slots=True)
class ProviderId(_Identifier):
    """Stable identity of a declared capability provider."""

