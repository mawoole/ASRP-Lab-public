"""Technology-independent version value object.

Purpose:
    Represent entity, event, and capability versions consistently.
Responsibilities:
    Validate semantic version components, parse canonical text, and advance versions.
Key classes:
    Version.
Out-of-scope:
    Compatibility negotiation, migration, and release automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True, order=True)
class Version:
    """A compact semantic version with one to three non-negative components."""

    major: int
    minor: int = 0
    patch: int = 0

    def __post_init__(self) -> None:
        for field_name in ("major", "minor", "patch"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse ``major``, ``major.minor``, or ``major.minor.patch`` text."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("version must be a non-empty string")
        parts = value.strip().split(".")
        if not 1 <= len(parts) <= 3 or not all(part.isdigit() for part in parts):
            raise ValueError("version must contain one to three numeric components")
        components = [int(part) for part in parts]
        components.extend([0] * (3 - len(components)))
        return cls(*components)

    def next_patch(self) -> Self:
        """Return the next immutable entity revision."""
        return type(self)(self.major, self.minor, self.patch + 1)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

