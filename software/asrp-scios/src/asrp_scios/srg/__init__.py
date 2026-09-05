"""Scientific Research Graph MVP public API.

Purpose:
    Expose the domain-independent Sprint-003 in-memory graph service.
Responsibilities:
    Re-export the graph protocol, implementation, results, directions, and errors.
Inputs:
    Sprint-002B scientific entities, relationships, identifiers, and query bounds.
Outputs:
    Deterministic graph queries, traceability subgraphs, and integrity reports.
Invariants:
    IDs remain unique, endpoints exist, and graph mutations never silently delete.
Dependencies:
    ASRP-SciOS domain model and Python standard library only.
Limitations:
    State is process-local and the Sprint-001 branch/history port is not adapted.
Non-goals:
    Persistence, graph databases, APIs, UI, LLMs, orchestration, and inference.
"""

from .errors import (
    DuplicateEntityError,
    DuplicateRelationshipError,
    EntityNotFoundError,
    InvalidGraphQueryError,
    ScientificResearchGraphError,
)
from .in_memory import (
    TRACEABILITY_RELATIONSHIP_TYPES,
    InMemoryScientificResearchGraph,
)
from .model import (
    GraphDirection,
    GraphIntegrityIssue,
    GraphIntegrityReport,
    GraphPath,
    TraceabilitySubgraph,
)
from .protocol import ScientificResearchGraph

__all__ = [
    "DuplicateEntityError",
    "DuplicateRelationshipError",
    "EntityNotFoundError",
    "GraphDirection",
    "GraphIntegrityIssue",
    "GraphIntegrityReport",
    "GraphPath",
    "InMemoryScientificResearchGraph",
    "InvalidGraphQueryError",
    "ScientificResearchGraph",
    "ScientificResearchGraphError",
    "TRACEABILITY_RELATIONSHIP_TYPES",
    "TraceabilitySubgraph",
]
