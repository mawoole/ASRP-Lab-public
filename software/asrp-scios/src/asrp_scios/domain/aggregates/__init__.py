"""Scientific aggregate roots defined by AGG-001.

Purpose:
    Expose the domain mutation boundaries for core scientific lifecycles.
Responsibilities:
    Provide canonical aggregate imports and the shared structural protocol.
Key classes:
    ResearchProgram, ResearchCampaign, ScientificQuestion, Hypothesis,
    EvidenceCollection, ResearchDecision, Discovery, and ContextSnapshot.
Out-of-scope:
    Repositories, persistence, transactions, orchestration, and application services.
"""

from .base import AggregateRoot
from .context_snapshot import ContextSnapshot
from .discovery import Discovery
from .evidence_collection import EvidenceCollection
from .hypothesis import Hypothesis
from .research_campaign import ResearchCampaign
from .research_decision import ResearchDecision
from .research_program import ResearchProgram
from .scientific_question import ScientificQuestion

__all__ = [
    "AggregateRoot",
    "ContextSnapshot",
    "Discovery",
    "EvidenceCollection",
    "Hypothesis",
    "ResearchCampaign",
    "ResearchDecision",
    "ResearchProgram",
    "ScientificQuestion",
]
