"""Scientific Domain Model baseline for ASRP-SciOS.

Purpose:
    Expose the domain-independent ontology, aggregates, events, and capabilities.
Responsibilities:
    Provide stable package boundaries while keeping the microkernel unchanged.
Key classes:
    ScientificEntity, ScientificEvent, AggregateRoot, and CapabilityContract.
Out-of-scope:
    Persistence, APIs, UI, authorization, orchestration, and program-specific logic.
"""

from . import aggregates, capabilities, entities, events, lifecycle, relationships
from .aggregates import (
    AggregateRoot,
    ContextSnapshot,
    Discovery,
    EvidenceCollection,
    Hypothesis,
    ResearchCampaign,
    ResearchDecision,
    ResearchProgram,
    ScientificQuestion,
)
from .entities import (
    Evidence,
    Experiment,
    KnowledgeItem,
    Observation,
    Patent,
    Publication,
    ScientificEntity,
    ScientificProgram,
    Simulation,
    Unknown,
)
from .events import ScientificEvent
from .relationships import ScientificRelationship

__all__ = [
    "AggregateRoot",
    "ContextSnapshot",
    "Discovery",
    "Evidence",
    "EvidenceCollection",
    "Experiment",
    "Hypothesis",
    "KnowledgeItem",
    "Observation",
    "Patent",
    "Publication",
    "ResearchCampaign",
    "ResearchDecision",
    "ResearchProgram",
    "ScientificEntity",
    "ScientificEvent",
    "ScientificProgram",
    "ScientificQuestion",
    "ScientificRelationship",
    "Simulation",
    "Unknown",
    "aggregates",
    "capabilities",
    "entities",
    "events",
    "lifecycle",
    "relationships",
]
