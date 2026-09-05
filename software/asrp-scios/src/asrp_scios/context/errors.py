"""Context Engineering MVP errors.

Purpose:
    Provide explicit failures for invalid context requests and snapshots.
Responsibilities:
    Distinguish request validation, graph inconsistency, and snapshot validation.
Inputs:
    Human-readable descriptions of rejected Context Engineering operations.
Outputs:
    Stable exception types for callers and tests.
Dependencies:
    Python standard library only.
Limitations:
    Errors contain no transport status, retry, authorization, or persistence data.
"""


class ContextEngineeringError(Exception):
    """Base class for Context Engineering MVP failures."""


class InvalidContextRequestError(ContextEngineeringError, ValueError):
    """Raised when a context request violates deterministic selection bounds."""


class ContextGraphInconsistencyError(ContextEngineeringError):
    """Raised when an SRG query returns an internally inconsistent graph view."""


class InvalidContextSnapshotError(ContextEngineeringError, ValueError):
    """Raised when a generated snapshot violates the Sprint-004 projection rules."""
