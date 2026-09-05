"""Private validation and immutability helpers for scientific contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import math
from types import MappingProxyType
from typing import TypeAlias

ContractValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    | tuple["ContractValue", ...]
    | Mapping[str, "ContractValue"]
)


def require_non_empty(value: str, field_name: str) -> str:
    """Return a stripped non-empty string or raise a meaningful error."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def require_optional_non_empty(value: str | None, field_name: str) -> str | None:
    """Validate an optional identifier-like string."""
    if value is None:
        return None
    return require_non_empty(value, field_name)


def require_aware_datetime(value: datetime, field_name: str) -> datetime:
    """Require a timezone-aware datetime so records remain unambiguous."""
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def freeze_strings(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    """Validate and normalize an immutable collection of strings."""
    if not isinstance(values, tuple):
        values = tuple(values)
    return tuple(
        require_non_empty(value, f"{field_name}[{index}]")
        for index, value in enumerate(values)
    )


def freeze_mapping(values: Mapping[str, object] | None) -> Mapping[str, ContractValue]:
    """Return a deeply immutable, JSON-compatible mapping.

    Sets and arbitrary objects are rejected because their serialization and
    mutation semantics would make event and artefact records ambiguous.
    """
    if values is None:
        return MappingProxyType({})
    if not isinstance(values, Mapping):
        raise TypeError("contract data must be a mapping")

    frozen: dict[str, ContractValue] = {}
    for key, value in values.items():
        normalized_key = require_non_empty(key, "contract data key")
        frozen[normalized_key] = freeze_value(value)
    return MappingProxyType(frozen)


def freeze_value(value: object) -> ContractValue:
    """Deep-freeze one JSON-compatible contract value."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("floating-point contract values must be finite")
        return value
    if isinstance(value, Mapping):
        return freeze_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    raise TypeError(
        "contract values must be JSON-compatible scalars, mappings, or sequences"
    )

