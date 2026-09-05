"""CAP-001 capability and provider descriptors.

Purpose:
    Describe domain-independent scientific capabilities without invoking them.
Responsibilities:
    Validate capability contracts, provider declarations, and readiness metadata.
Key classes:
    CapabilityDescriptor, CapabilityProviderDescriptor, CapabilityInput,
    CapabilityOutput, CapabilityCategory, and CapabilityReadinessLevel.
Out-of-scope:
    Provider selection, execution, routing, orchestration, and service discovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

from asrp_scios.contracts._validation import (
    freeze_strings,
    require_non_empty,
    require_optional_non_empty,
)
from asrp_scios.domain.value_objects import CapabilityId, ProviderId, Version


class CapabilityCategory(str, Enum):
    RESEARCH = "Research"
    KNOWLEDGE = "Knowledge"
    SCIENTIFIC_METHOD = "ScientificMethod"
    CONTEXT = "Context"
    GOVERNANCE = "Governance"
    EXECUTION = "Execution"
    PLATFORM = "Platform"
    PROGRAM_EXTENSION = "ProgramExtension"


class ProviderType(str, Enum):
    HUMAN_RESEARCHER = "HumanResearcher"
    SCIENTIFIC_COGNITIVE_SYSTEM = "ScientificCognitiveSystem"
    CORE_SERVICE = "CoreService"
    PLUGIN = "Plugin"
    EXTERNAL_ADAPTER = "ExternalAdapter"
    SIMULATION_ENGINE = "SimulationEngine"
    FUTURE_MODEL = "FutureModel"


class CapabilityReadinessLevel(IntEnum):
    CRL0 = 0
    CRL1 = 1
    CRL2 = 2
    CRL3 = 3
    CRL4 = 4
    CRL5 = 5
    CRL6 = 6
    CRL7 = 7
    CRL8 = 8
    CRL9 = 9

    @property
    def description(self) -> str:
        """Return the normative CAP-001 meaning of this readiness level."""
        return _READINESS_DESCRIPTIONS[self]


_READINESS_DESCRIPTIONS = {
    CapabilityReadinessLevel.CRL0: "Concept identified",
    CapabilityReadinessLevel.CRL1: "Capability defined",
    CapabilityReadinessLevel.CRL2: "Contract specified",
    CapabilityReadinessLevel.CRL3: "Prototype provider exists",
    CapabilityReadinessLevel.CRL4: "Tested in isolation",
    CapabilityReadinessLevel.CRL5: "Integrated into ASRP-Lab",
    CapabilityReadinessLevel.CRL6: "Used by a scientific program",
    CapabilityReadinessLevel.CRL7: "Measured benefit demonstrated",
    CapabilityReadinessLevel.CRL8: "Stable and documented",
    CapabilityReadinessLevel.CRL9: "Reusable across multiple scientific programs",
}


@dataclass(frozen=True, slots=True)
class CapabilityInput:
    """One declared input and its non-executable validation expectations."""

    name: str
    type_name: str
    required: bool = True
    validation_rule: str | None = None
    expected_provenance: str | None = None
    expected_context: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", require_non_empty(self.name, "name"))
        object.__setattr__(
            self, "type_name", require_non_empty(self.type_name, "type_name")
        )
        if not isinstance(self.required, bool):
            raise TypeError("required must be a boolean")
        for field_name in (
            "validation_rule",
            "expected_provenance",
            "expected_context",
        ):
            object.__setattr__(
                self,
                field_name,
                require_optional_non_empty(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class CapabilityOutput:
    """One declared output and its scientific metadata expectations."""

    name: str
    type_name: str
    confidence_required: bool = False
    provenance_required: bool = True
    traceability_required: bool = True
    limitations: tuple[str, ...] = ()
    related_events: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", require_non_empty(self.name, "name"))
        object.__setattr__(
            self, "type_name", require_non_empty(self.type_name, "type_name")
        )
        for field_name in (
            "confidence_required",
            "provenance_required",
            "traceability_required",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a boolean")
        object.__setattr__(
            self, "limitations", freeze_strings(self.limitations, "limitations")
        )
        object.__setattr__(
            self, "related_events", freeze_strings(self.related_events, "related_events")
        )


@dataclass(frozen=True, slots=True)
class CapabilityDescriptor:
    """Stable, implementation-neutral CAP-001 capability declaration."""

    capability_id: CapabilityId
    name: str
    version: Version
    category: CapabilityCategory
    description: str
    inputs: tuple[CapabilityInput, ...]
    outputs: tuple[CapabilityOutput, ...]
    provider_types: tuple[ProviderType, ...]
    readiness_level: CapabilityReadinessLevel = CapabilityReadinessLevel.CRL2
    required_context: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()
    quality_metrics: tuple[str, ...] = ()
    human_review_required: bool = False
    limitations: tuple[str, ...] = ()
    related_events: tuple[str, ...] = ()
    related_aggregates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, CapabilityId):
            raise TypeError("capability_id must be a CapabilityId")
        object.__setattr__(self, "name", require_non_empty(self.name, "name"))
        if not isinstance(self.version, Version):
            raise TypeError("version must be a Version")
        if not isinstance(self.category, CapabilityCategory):
            raise TypeError("category must be a CapabilityCategory")
        object.__setattr__(
            self, "description", require_non_empty(self.description, "description")
        )
        inputs = tuple(self.inputs)
        outputs = tuple(self.outputs)
        providers = tuple(self.provider_types)
        if not all(isinstance(value, CapabilityInput) for value in inputs):
            raise TypeError("inputs must contain CapabilityInput values")
        if not all(isinstance(value, CapabilityOutput) for value in outputs):
            raise TypeError("outputs must contain CapabilityOutput values")
        if not providers or not all(isinstance(value, ProviderType) for value in providers):
            raise ValueError("provider_types must contain at least one ProviderType")
        if len({value.name for value in inputs}) != len(inputs):
            raise ValueError("input names must be unique")
        if len({value.name for value in outputs}) != len(outputs):
            raise ValueError("output names must be unique")
        object.__setattr__(self, "inputs", inputs)
        object.__setattr__(self, "outputs", outputs)
        object.__setattr__(self, "provider_types", providers)
        if not isinstance(self.readiness_level, CapabilityReadinessLevel):
            raise TypeError("readiness_level must be a CapabilityReadinessLevel")
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be a boolean")
        for field_name in (
            "required_context",
            "required_permissions",
            "quality_metrics",
            "limitations",
            "related_events",
            "related_aggregates",
        ):
            object.__setattr__(
                self,
                field_name,
                freeze_strings(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class CapabilityProviderDescriptor:
    """A provider declaration with no selection or invocation behavior."""

    provider_id: ProviderId
    name: str
    provider_type: ProviderType
    version: Version
    supported_capabilities: tuple[CapabilityId, ...]
    readiness_level: CapabilityReadinessLevel
    status: str
    limitations: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, ProviderId):
            raise TypeError("provider_id must be a ProviderId")
        object.__setattr__(self, "name", require_non_empty(self.name, "name"))
        if not isinstance(self.provider_type, ProviderType):
            raise TypeError("provider_type must be a ProviderType")
        if not isinstance(self.version, Version):
            raise TypeError("version must be a Version")
        capabilities = tuple(self.supported_capabilities)
        if not capabilities or not all(
            isinstance(value, CapabilityId) for value in capabilities
        ):
            raise ValueError(
                "supported_capabilities must contain at least one CapabilityId"
            )
        object.__setattr__(self, "supported_capabilities", capabilities)
        if not isinstance(self.readiness_level, CapabilityReadinessLevel):
            raise TypeError("readiness_level must be a CapabilityReadinessLevel")
        object.__setattr__(self, "status", require_non_empty(self.status, "status"))
        for field_name in ("limitations", "required_permissions", "dependencies"):
            object.__setattr__(
                self,
                field_name,
                freeze_strings(getattr(self, field_name), field_name),
            )
