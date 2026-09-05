"""Scientific Cognitive System contracts from API-0001.

Purpose:
    Make Scientific Cognitive Systems replaceable behind one stable interface.
Responsibilities:
    Define system identity, mandatory inputs, explainable outputs, and metadata.
Inputs:
    Scientific questions, context, constraints, evidence, objectives, and unknowns.
Outputs:
    Traceable and human-reviewable scientific artefacts or recommendations.
Dependencies:
    Shared ASRP-SciOS contracts and the Python standard library.
Limitations:
    No model, agent, reasoning strategy, or provider integration is included.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from ._validation import (
    ContractValue,
    freeze_mapping,
    freeze_strings,
    require_aware_datetime,
    require_non_empty,
)
from .common import ConfidenceAssessment, Provenance, Traceability


@dataclass(frozen=True, slots=True)
class CognitiveSystemManifest:
    """Mandatory identity and capability declaration for a cognitive system."""

    identifier: str
    name: str
    version: str
    domain: str
    supported_capabilities: tuple[str, ...]
    dependencies: tuple[str, ...]
    supported_scientific_programs: tuple[str, ...]
    status: str

    def __post_init__(self) -> None:
        for field_name in ("identifier", "name", "version", "domain", "status"):
            object.__setattr__(
                self,
                field_name,
                require_non_empty(getattr(self, field_name), field_name),
            )
        for field_name in (
            "supported_capabilities",
            "dependencies",
            "supported_scientific_programs",
        ):
            object.__setattr__(
                self,
                field_name,
                freeze_strings(getattr(self, field_name), field_name),
            )
        if not self.supported_capabilities:
            raise ValueError("supported_capabilities must contain at least one capability")


@dataclass(frozen=True, slots=True)
class ScientificInput:
    """The mandatory, immutable input envelope accepted by every cognitive system."""

    scientific_questions: tuple[str, ...]
    scientific_context: Mapping[str, ContractValue]
    knowledge_references: tuple[str, ...]
    constraints: tuple[str, ...]
    objectives: tuple[str, ...]
    available_evidence: tuple[str, ...]
    unknowns: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "scientific_questions",
            "knowledge_references",
            "constraints",
            "objectives",
            "available_evidence",
            "unknowns",
        ):
            object.__setattr__(
                self,
                field_name,
                freeze_strings(getattr(self, field_name), field_name),
            )
        if not self.scientific_questions:
            raise ValueError("scientific_questions must contain at least one question")
        object.__setattr__(
            self, "scientific_context", freeze_mapping(self.scientific_context)
        )


@dataclass(frozen=True, slots=True)
class ScientificOutputMetadata:
    """Mandatory provenance and explainability metadata for one system output."""

    timestamp: datetime
    author: str
    provenance: Provenance
    confidence: ConfidenceAssessment
    traceability: Traceability
    dependencies: tuple[str, ...] = ()
    related_scientific_entities: tuple[str, ...] = ()
    requires_human_review: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "timestamp", require_aware_datetime(self.timestamp, "timestamp")
        )
        object.__setattr__(self, "author", require_non_empty(self.author, "author"))
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance record")
        if not isinstance(self.confidence, ConfidenceAssessment):
            raise TypeError("confidence must be a ConfidenceAssessment record")
        if not isinstance(self.traceability, Traceability):
            raise TypeError("traceability must be a Traceability record")
        object.__setattr__(
            self, "dependencies", freeze_strings(self.dependencies, "dependencies")
        )
        object.__setattr__(
            self,
            "related_scientific_entities",
            freeze_strings(
                self.related_scientific_entities, "related_scientific_entities"
            ),
        )
        if self.requires_human_review is not True:
            raise ValueError("scientific outputs must remain human-reviewable")


@dataclass(frozen=True, slots=True)
class ScientificOutput:
    """A typed scientific artefact or recommendation produced by a system."""

    output_type: str
    content: Mapping[str, ContractValue]
    metadata: ScientificOutputMetadata

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "output_type", require_non_empty(self.output_type, "output_type")
        )
        object.__setattr__(self, "content", freeze_mapping(self.content))
        if not isinstance(self.metadata, ScientificOutputMetadata):
            raise TypeError("metadata must be a ScientificOutputMetadata record")


@runtime_checkable
class ScientificCognitiveSystem(Protocol):
    """Replaceable API-0001 cognitive system interface."""

    @property
    def manifest(self) -> CognitiveSystemManifest:
        """Return the system identity and capabilities."""

    def process(self, scientific_input: ScientificInput) -> Sequence[ScientificOutput]:
        """Produce outputs and publish lifecycle/result events through the event bus."""

