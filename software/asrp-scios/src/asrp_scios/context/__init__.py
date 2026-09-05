"""Context Engineering MVP public API.

Purpose:
    Expose deterministic SRG-backed generation of the existing ContextSnapshot.
Responsibilities:
    Re-export request, policy, quality, explanation, generator, and error types.
Inputs:
    Task-oriented requests and a Sprint-003 ScientificResearchGraph implementation.
Outputs:
    Immutable ContextSnapshot aggregates with bounded context-selection evidence.
Dependencies:
    ASRP-SciOS domain model, SRG protocol, and Python standard library only.
Limitations:
    In-memory selection only; no LLM, embeddings, persistence, API, UI, or runtime.
"""

from .errors import (
    ContextEngineeringError,
    ContextGraphInconsistencyError,
    InvalidContextRequestError,
    InvalidContextSnapshotError,
)
from .generator import ContextSnapshotGenerator
from .model import (
    ContextQualityResult,
    ContextRequest,
    ContextSelectionExplanation,
)
from .policy import ContextSelectionPolicy

__all__ = [
    "ContextEngineeringError",
    "ContextGraphInconsistencyError",
    "ContextQualityResult",
    "ContextRequest",
    "ContextSelectionExplanation",
    "ContextSelectionPolicy",
    "ContextSnapshotGenerator",
    "InvalidContextRequestError",
    "InvalidContextSnapshotError",
]
