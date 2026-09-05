"""Concrete non-aggregate scientific entities.

Purpose:
    Expose the ontology-level ScientificEntity base and deferred aggregate concepts.
Responsibilities:
    Provide canonical entity imports while aggregate roots remain in their package.
Key classes:
    ScientificEntity, ScientificProgram, Observation, Experiment, Simulation,
    Evidence, Unknown, KnowledgeItem, Publication, and Patent.
Out-of-scope:
    Aggregate operations, persistence, execution engines, and program extensions.
"""

from .base import ScientificEntity
from .models import (
    Evidence,
    Experiment,
    KnowledgeItem,
    Observation,
    Patent,
    Publication,
    ScientificProgram,
    Simulation,
    Unknown,
)

__all__ = [
    "Evidence",
    "Experiment",
    "KnowledgeItem",
    "Observation",
    "Patent",
    "Publication",
    "ScientificEntity",
    "ScientificProgram",
    "Simulation",
    "Unknown",
]

