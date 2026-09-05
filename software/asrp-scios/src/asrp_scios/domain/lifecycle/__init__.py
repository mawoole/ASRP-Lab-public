"""Public lifecycle vocabulary for the Scientific Domain Model.

Purpose:
    Expose canonical general and specialized scientific status enums.
Responsibilities:
    Provide stable imports for lifecycle-aware entities and aggregates.
Key classes:
    LifecycleStatus, HypothesisStatus, EvidenceStatus, ResearchDecisionStatus.
Out-of-scope:
    Workflow engines and automatic state-transition orchestration.
"""

from .statuses import (
    EvidenceStatus,
    HypothesisStatus,
    LifecycleStatus,
    ReproducibilityStatus,
    ResearchDecisionStatus,
    ReviewStatus,
    ScientificStatus,
)

__all__ = [
    "EvidenceStatus",
    "HypothesisStatus",
    "LifecycleStatus",
    "ReproducibilityStatus",
    "ResearchDecisionStatus",
    "ReviewStatus",
    "ScientificStatus",
]
