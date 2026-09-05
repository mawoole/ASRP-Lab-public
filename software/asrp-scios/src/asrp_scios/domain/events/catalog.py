"""EVT-001 event catalog and aggregate mappings.

Purpose:
    Declare the approved baseline event types without implementing delivery.
Responsibilities:
    Group immutable event descriptors by family and source aggregate/entity.
Key classes:
    EVENT_CATALOG and AGGREGATE_EVENT_TYPES descriptor mappings.
Out-of-scope:
    Brokers, event stores, subscriptions, replay, and program-specific events.
"""

from __future__ import annotations

from collections import defaultdict
from types import MappingProxyType

from .base import EventCategory, EventDescriptor


_EVENT_GROUPS: tuple[tuple[EventCategory, str, tuple[str, ...]], ...] = (
    (
        EventCategory.RESEARCH,
        "ResearchProgram",
        (
            "ResearchProgramCreated",
            "ResearchProgramMissionUpdated",
            "ResearchProgramArchived",
            "ProgramDecisionRecorded",
        ),
    ),
    (
        EventCategory.RESEARCH,
        "ResearchCampaign",
        (
            "ResearchCampaignCreated",
            "ScientificQuestionLinked",
            "HypothesisLinkedToCampaign",
            "EvidenceCollectionLinked",
            "ResearchCampaignClosed",
        ),
    ),
    (
        EventCategory.RESEARCH,
        "ScientificQuestion",
        (
            "ScientificQuestionCreated",
            "ScientificQuestionRefined",
            "HypothesisGeneratedFromQuestion",
            "ScientificQuestionResolved",
            "ScientificQuestionArchived",
        ),
    ),
    (
        EventCategory.RESEARCH,
        "Discovery",
        (
            "DiscoveryProposed",
            "EvidenceLinkedToDiscovery",
            "DiscoveryValidationDecisionLinked",
            "DiscoveryValidated",
            "DiscoverySuperseded",
            "DiscoveryArchived",
            "KnowledgePublished",
        ),
    ),
    (
        EventCategory.SCIENTIFIC_METHOD,
        "Hypothesis",
        (
            "HypothesisProposed",
            "HypothesisRefined",
            "HypothesisDeclaredTestable",
            "HypothesisFalsificationCriteriaDeclared",
            "EvidenceLinkedToHypothesis",
            "HypothesisConfidenceUpdated",
            "HypothesisBranched",
            "HypothesisRejected",
            "HypothesisValidated",
            "HypothesisSuperseded",
        ),
    ),
    (
        EventCategory.SCIENTIFIC_METHOD,
        "EvidenceCollection",
        (
            "EvidenceCollectionCreated",
            "EvidenceItemAdded",
            "EvidenceDirectionClassified",
            "EvidenceQualityUpdated",
            "NegativeEvidenceRecorded",
            "ReproducibilityStatusUpdated",
        ),
    ),
    (
        EventCategory.SCIENTIFIC_METHOD,
        "ScientificReview",
        (
            "ScientificReviewRequested",
            "ScientificReviewStarted",
            "ScientificReviewCompleted",
            "HumanReviewRequired",
            "HumanReviewCompleted",
        ),
    ),
    (
        EventCategory.SCIENTIFIC_METHOD,
        "Unknown",
        (
            "UnknownRecorded",
            "UnknownLinkedToQuestion",
            "UnknownInvestigated",
            "UnknownResolved",
            "UnknownArchived",
        ),
    ),
    (
        EventCategory.SCIENTIFIC_METHOD,
        "ConfidenceAssessment",
        (
            "ConfidenceAssessmentCreated",
            "ConfidenceAssessmentUpdated",
            "ConfidenceIncreased",
            "ConfidenceDecreased",
            "ConfidenceRejected",
        ),
    ),
    (
        EventCategory.KNOWLEDGE,
        "ScientificResearchGraph",
        (
            "ScientificEntityRegistered",
            "ScientificRelationshipCreated",
            "ScientificRelationshipInvalidated",
            "ScientificEntitySuperseded",
            "ScientificEntityArchived",
            "ResearchBranchCreated",
            "ResearchBranchMerged",
        ),
    ),
    (
        EventCategory.KNOWLEDGE,
        "KnowledgeItem",
        (
            "KnowledgeItemCreated",
            "KnowledgeItemValidated",
            "KnowledgeItemSuperseded",
            "KnowledgeItemArchived",
        ),
    ),
    (
        EventCategory.KNOWLEDGE,
        "ContextSnapshot",
        (
            "ContextSnapshotCreated",
            "ContextSnapshotArchived",
            "ContextRecoveryRequested",
            "ContextRecoveryCompleted",
        ),
    ),
    (
        EventCategory.KNOWLEDGE,
        "Provenance",
        (
            "ProvenanceRecorded",
            "ProvenanceUpdated",
            "TraceabilityLinkCreated",
            "TraceabilityLinkInvalidated",
        ),
    ),
    (
        EventCategory.GOVERNANCE,
        "ResearchDecision",
        (
            "ResearchDecisionDrafted",
            "DecisionAlternativeAdded",
            "EvidenceLinkedToDecision",
            "ResearchDecisionAccepted",
            "ResearchDecisionRejected",
            "ResearchDecisionSuperseded",
            "ResearchDecisionReversed",
        ),
    ),
    (
        EventCategory.GOVERNANCE,
        "ADR",
        ("ADRCreated", "ADRAccepted", "ADRSuperseded", "ADRDeprecated", "ADRArchived"),
    ),
    (
        EventCategory.GOVERNANCE,
        "RFC",
        ("RFCCreated", "RFCReviewed", "RFCAccepted", "RFCSuperseded", "RFCArchived"),
    ),
    (
        EventCategory.GOVERNANCE,
        "Standard",
        (
            "StandardCreated",
            "StandardApproved",
            "StandardUpdated",
            "StandardDeprecated",
            "StandardArchived",
        ),
    ),
    (
        EventCategory.GOVERNANCE,
        "BlueprintSection",
        (
            "BlueprintSectionCreated",
            "BlueprintSectionReviewed",
            "BlueprintSectionApproved",
            "BlueprintSectionSuperseded",
        ),
    ),
    (
        EventCategory.EXECUTION,
        "Mission",
        (
            "MissionCreated",
            "MissionStarted",
            "MissionCompleted",
            "MissionFailed",
            "MissionCancelled",
        ),
    ),
    (
        EventCategory.EXECUTION,
        "Workflow",
        (
            "WorkflowCreated",
            "WorkflowStarted",
            "WorkflowStepStarted",
            "WorkflowStepCompleted",
            "WorkflowCompleted",
            "WorkflowFailed",
        ),
    ),
    (
        EventCategory.EXECUTION,
        "Task",
        (
            "TaskCreated",
            "TaskAssigned",
            "TaskStarted",
            "TaskCompleted",
            "TaskFailed",
            "TaskBlocked",
        ),
    ),
    (
        EventCategory.PLATFORM,
        "Kernel",
        ("KernelStarted", "KernelStopped"),
    ),
    (
        EventCategory.PLATFORM,
        "Plugin",
        ("PluginRegistered", "PluginStarted", "PluginStopped", "PluginFailed"),
    ),
    (
        EventCategory.PLATFORM,
        "Adapter",
        ("AdapterRegistered",),
    ),
    (
        EventCategory.PLATFORM,
        "Service",
        ("ServiceHealthChanged",),
    ),
)


_HUMAN_REVIEW_EVENTS = {
    "DiscoveryValidated",
    "HypothesisRejected",
    "HypothesisValidated",
    "HumanReviewCompleted",
    "ResearchDecisionAccepted",
    "ResearchDecisionRejected",
}

_catalog: dict[str, EventDescriptor] = {}
_aggregate_events: defaultdict[str, list[str]] = defaultdict(list)
for category, aggregate_type, event_types in _EVENT_GROUPS:
    for event_type in event_types:
        if event_type in _catalog:
            raise RuntimeError(f"duplicate event descriptor: {event_type}")
        _catalog[event_type] = EventDescriptor(
            event_type=event_type,
            category=category,
            aggregate_type=aggregate_type,
            human_review_required=event_type in _HUMAN_REVIEW_EVENTS,
        )
        _aggregate_events[aggregate_type].append(event_type)

EVENT_CATALOG = MappingProxyType(_catalog)
AGGREGATE_EVENT_TYPES = MappingProxyType(
    {name: tuple(event_types) for name, event_types in _aggregate_events.items()}
)


def get_event_descriptor(event_type: str) -> EventDescriptor:
    """Return one approved descriptor or raise a domain-level validation error."""
    try:
        return EVENT_CATALOG[event_type]
    except KeyError as error:
        raise ValueError(f"unknown EVT-001 event type: {event_type}") from error

