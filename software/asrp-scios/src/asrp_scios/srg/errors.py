"""Scientific Research Graph domain errors.

Purpose:
    Provide explicit failures for invalid in-memory graph operations.
Responsibilities:
    Distinguish duplicate identities, missing endpoints, and invalid queries.
Inputs:
    Human-readable descriptions of rejected SRG operations.
Outputs:
    Stable exception types for callers and tests.
Invariants:
    Invalid graph mutations fail before changing graph state.
Dependencies:
    Python standard library only.
Limitations:
    Errors contain no transport status codes or persistence details.
Non-goals:
    API error mapping, retry policy, logging, and authorization.
"""


class ScientificResearchGraphError(Exception):
    """Base class for explicit SRG service failures."""


class DuplicateEntityError(ScientificResearchGraphError):
    """Raised when an entity ID is already registered."""


class DuplicateRelationshipError(ScientificResearchGraphError):
    """Raised when a relationship ID is already registered."""


class EntityNotFoundError(ScientificResearchGraphError):
    """Raised when an operation requires an unregistered entity."""


class InvalidGraphQueryError(ScientificResearchGraphError):
    """Raised when graph query parameters are inconsistent or invalid."""
