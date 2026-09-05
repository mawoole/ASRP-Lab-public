"""Canonical lifecycle and review states from ONT-001 and UML-001.

Purpose:
    Provide explicit states for general entities and specialized scientific lifecycles.
Responsibilities:
    Define closed vocabularies without implementing workflow orchestration.
Key classes:
    LifecycleStatus, HypothesisStatus, EvidenceStatus, ResearchDecisionStatus,
    ReproducibilityStatus, and ReviewStatus.
Out-of-scope:
    Persistence, transition scheduling, and cross-aggregate workflows.
"""

from enum import Enum


class LifecycleStatus(str, Enum):
    DRAFT = "Draft"
    PROPOSED = "Proposed"
    UNDER_REVIEW = "UnderReview"
    ACTIVE = "Active"
    SUPPORTED = "Supported"
    CONTRADICTED = "Contradicted"
    VALIDATED = "Validated"
    SUPERSEDED = "Superseded"
    DEPRECATED = "Deprecated"
    ARCHIVED = "Archived"
    REJECTED = "Rejected"


class HypothesisStatus(str, Enum):
    DRAFT = "Draft"
    PROPOSED = "Proposed"
    UNDER_REVIEW = "UnderReview"
    TESTABLE = "Testable"
    TESTING = "Testing"
    SUPPORTED = "Supported"
    CONTRADICTED = "Contradicted"
    VALIDATED = "Validated"
    REJECTED = "Rejected"
    SUPERSEDED = "Superseded"
    ARCHIVED = "Archived"


class EvidenceStatus(str, Enum):
    COLLECTED = "Collected"
    QUALIFIED = "Qualified"
    UNDER_REVIEW = "UnderReview"
    ACCEPTED = "Accepted"
    CONTRADICTED = "Contradicted"
    INVALIDATED = "Invalidated"
    ARCHIVED = "Archived"


class ResearchDecisionStatus(str, Enum):
    DRAFT = "Draft"
    PROPOSED = "Proposed"
    UNDER_REVIEW = "UnderReview"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    SUPERSEDED = "Superseded"
    REVERSED = "Reversed"
    ARCHIVED = "Archived"


class ReproducibilityStatus(str, Enum):
    NOT_ASSESSED = "NotAssessed"
    PLANNED = "Planned"
    ATTEMPTED = "Attempted"
    REPRODUCED = "Reproduced"
    NOT_REPRODUCED = "NotReproduced"
    PARTIALLY_REPRODUCED = "PartiallyReproduced"


class ReviewStatus(str, Enum):
    NOT_REQUESTED = "NotRequested"
    REQUIRED = "Required"
    PENDING = "Pending"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


ScientificStatus = (
    LifecycleStatus | HypothesisStatus | EvidenceStatus | ResearchDecisionStatus
)

