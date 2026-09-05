"""Non-aggregate scientific entities from ONT-001 and UML-001.

Purpose:
    Represent concrete ontology concepts whose aggregate lifecycles are deferred.
Responsibilities:
    Validate scientific-program, observation, execution artefact, evidence,
    unknown, knowledge, publication, and patent semantics.
Key classes:
    ScientificProgram, Observation, Experiment, Simulation, Evidence, Unknown,
    KnowledgeItem, Publication, and Patent.
Out-of-scope:
    Experiment execution, simulation engines, publication workflows, patents,
    and persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from asrp_scios.contracts._validation import (
    freeze_strings,
    require_aware_datetime,
    require_non_empty,
)
from asrp_scios.domain.lifecycle import LifecycleStatus, ReproducibilityStatus
from asrp_scios.domain.value_objects import (
    Confidence,
    EntityId,
    EvidenceDirection,
    EvidenceType,
    ScientificReference,
)

from .base import ScientificEntity


def _freeze_entity_ids(values: tuple[EntityId, ...], field_name: str) -> tuple[EntityId, ...]:
    frozen = tuple(values)
    if not all(isinstance(value, EntityId) for value in frozen):
        raise TypeError(f"{field_name} must contain EntityId values")
    return frozen


@dataclass(frozen=True, slots=True, kw_only=True)
class ScientificProgram(ScientificEntity):
    """Ontology-level long-term scientific program."""

    mission: str
    scientific_objectives: tuple[str, ...] = ()
    program_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super(ScientificProgram, self).__post_init__()
        mission = self.mission.strip() if isinstance(self.mission, str) else ""
        objectives = freeze_strings(
            self.scientific_objectives, "scientific_objectives"
        )
        if not mission and not objectives:
            raise ValueError("ScientificProgram requires a mission or objective")
        object.__setattr__(self, "mission", mission)
        object.__setattr__(self, "scientific_objectives", objectives)
        object.__setattr__(
            self,
            "program_constraints",
            freeze_strings(self.program_constraints, "program_constraints"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Observation(ScientificEntity):
    """A measurable fact or recorded phenomenon."""

    observed_at: datetime
    observation_source: str

    def __post_init__(self) -> None:
        super(Observation, self).__post_init__()
        object.__setattr__(
            self,
            "observed_at",
            require_aware_datetime(self.observed_at, "observed_at"),
        )
        object.__setattr__(
            self,
            "observation_source",
            require_non_empty(self.observation_source, "observation_source"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Experiment(ScientificEntity):
    """A controlled procedure intended to evaluate hypotheses."""

    hypothesis_ids: tuple[EntityId, ...]
    method: str

    def __post_init__(self) -> None:
        super(Experiment, self).__post_init__()
        object.__setattr__(
            self,
            "hypothesis_ids",
            _freeze_entity_ids(self.hypothesis_ids, "hypothesis_ids"),
        )
        if not self.hypothesis_ids:
            raise ValueError("Experiment requires at least one hypothesis reference")
        object.__setattr__(self, "method", require_non_empty(self.method, "method"))


@dataclass(frozen=True, slots=True, kw_only=True)
class Simulation(ScientificEntity):
    """A computational representation used to investigate hypotheses."""

    hypothesis_ids: tuple[EntityId, ...]
    model_description: str

    def __post_init__(self) -> None:
        super(Simulation, self).__post_init__()
        object.__setattr__(
            self,
            "hypothesis_ids",
            _freeze_entity_ids(self.hypothesis_ids, "hypothesis_ids"),
        )
        if not self.hypothesis_ids:
            raise ValueError("Simulation requires at least one hypothesis reference")
        object.__setattr__(
            self,
            "model_description",
            require_non_empty(self.model_description, "model_description"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Evidence(ScientificEntity):
    """First-class information supporting or challenging a scientific claim."""

    evidence_type: EvidenceType
    direction: EvidenceDirection
    source_reference: ScientificReference
    method: str
    confidence: Confidence
    uncertainty: str | None = None
    reproducibility_status: ReproducibilityStatus = ReproducibilityStatus.NOT_ASSESSED
    related_entity_ids: tuple[EntityId, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super(Evidence, self).__post_init__()
        if not isinstance(self.evidence_type, EvidenceType):
            raise TypeError("evidence_type must be an EvidenceType")
        if not isinstance(self.direction, EvidenceDirection):
            raise TypeError("direction must be an EvidenceDirection")
        if not isinstance(self.source_reference, ScientificReference):
            raise TypeError("source_reference must be a ScientificReference")
        object.__setattr__(self, "method", require_non_empty(self.method, "method"))
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence")
        if self.uncertainty is not None:
            object.__setattr__(
                self,
                "uncertainty",
                require_non_empty(self.uncertainty, "uncertainty"),
            )
        if not isinstance(self.reproducibility_status, ReproducibilityStatus):
            raise TypeError(
                "reproducibility_status must be a ReproducibilityStatus"
            )
        object.__setattr__(
            self,
            "related_entity_ids",
            _freeze_entity_ids(self.related_entity_ids, "related_entity_ids"),
        )
        object.__setattr__(
            self, "limitations", freeze_strings(self.limitations, "limitations")
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Unknown(ScientificEntity):
    """A first-class unresolved scientific uncertainty."""

    importance: str
    affected_hypothesis_ids: tuple[EntityId, ...] = ()
    proposed_investigations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super(Unknown, self).__post_init__()
        object.__setattr__(
            self, "importance", require_non_empty(self.importance, "importance")
        )
        object.__setattr__(
            self,
            "affected_hypothesis_ids",
            _freeze_entity_ids(
                self.affected_hypothesis_ids, "affected_hypothesis_ids"
            ),
        )
        object.__setattr__(
            self,
            "proposed_investigations",
            freeze_strings(self.proposed_investigations, "proposed_investigations"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class KnowledgeItem(ScientificEntity):
    """Validated reusable scientific information."""

    evidence_collection_ids: tuple[EntityId, ...] = ()
    validation_decision_ids: tuple[EntityId, ...] = ()

    def __post_init__(self) -> None:
        super(KnowledgeItem, self).__post_init__()
        object.__setattr__(
            self,
            "evidence_collection_ids",
            _freeze_entity_ids(
                self.evidence_collection_ids, "evidence_collection_ids"
            ),
        )
        object.__setattr__(
            self,
            "validation_decision_ids",
            _freeze_entity_ids(
                self.validation_decision_ids, "validation_decision_ids"
            ),
        )
        if self.status is LifecycleStatus.VALIDATED and not self.evidence_collection_ids:
            raise ValueError("validated KnowledgeItem requires evidence")


@dataclass(frozen=True, slots=True, kw_only=True)
class Publication(ScientificEntity):
    """Scientific dissemination artefact linked to discovery history."""

    discovery_ids: tuple[EntityId, ...]
    reference: ScientificReference

    def __post_init__(self) -> None:
        super(Publication, self).__post_init__()
        object.__setattr__(
            self,
            "discovery_ids",
            _freeze_entity_ids(self.discovery_ids, "discovery_ids"),
        )
        if not self.discovery_ids:
            raise ValueError("Publication requires at least one discovery reference")
        if not isinstance(self.reference, ScientificReference):
            raise TypeError("reference must be a ScientificReference")


@dataclass(frozen=True, slots=True, kw_only=True)
class Patent(ScientificEntity):
    """Protected innovation artefact linked to evidence and research history."""

    discovery_ids: tuple[EntityId, ...]
    reference: ScientificReference

    def __post_init__(self) -> None:
        super(Patent, self).__post_init__()
        object.__setattr__(
            self,
            "discovery_ids",
            _freeze_entity_ids(self.discovery_ids, "discovery_ids"),
        )
        if not self.discovery_ids:
            raise ValueError("Patent requires at least one discovery reference")
        if not isinstance(self.reference, ScientificReference):
            raise TypeError("reference must be a ScientificReference")

