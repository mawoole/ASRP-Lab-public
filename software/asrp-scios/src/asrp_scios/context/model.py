"""Immutable Context Engineering request and result values.

Purpose:
    Represent bounded context requests, quality indicators, and selection rationale.
Responsibilities:
    Validate task orientation, deterministic bounds, immutable coverage, and IDs.
Inputs:
    Typed domain identifiers, canonical relationship filters, scores, and warnings.
Outputs:
    Frozen ContextRequest, ContextQualityResult, and selection explanation values.
Dependencies:
    ASRP-SciOS validation helpers, domain identifiers, and relationship vocabulary.
Limitations:
    Values do not query graphs, generate summaries, persist, or invoke providers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from asrp_scios.contracts._validation import freeze_strings, require_non_empty
from asrp_scios.domain.value_objects import EntityId, RelationshipType

from .errors import InvalidContextRequestError, InvalidContextSnapshotError


def _freeze_entity_ids(
    values: Sequence[EntityId],
    field_name: str,
    *,
    require_values: bool = False,
    sort_values: bool = False,
) -> tuple[EntityId, ...]:
    frozen = tuple(values)
    if not all(isinstance(value, EntityId) for value in frozen):
        raise TypeError(f"{field_name} must contain EntityId values")
    if require_values and not frozen:
        raise InvalidContextRequestError(f"{field_name} cannot be empty")
    keys = tuple(str(value) for value in frozen)
    if len(keys) != len(set(keys)):
        raise InvalidContextRequestError(f"{field_name} cannot contain duplicates")
    if sort_values:
        return tuple(sorted(frozen, key=str))
    return frozen


def _score(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return normalized


def _mapping_string_tuple(
    values: Mapping[str, object], field_name: str
) -> tuple[str, ...]:
    raw = values.get(field_name, ())
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise InvalidContextSnapshotError(f"{field_name} must be a sequence")
    try:
        return freeze_strings(tuple(raw), field_name)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise InvalidContextSnapshotError(str(error)) from error


def _mapping_entity_ids(
    values: Mapping[str, object], field_name: str
) -> tuple[EntityId, ...]:
    raw = _mapping_string_tuple(values, field_name)
    try:
        return tuple(EntityId(value) for value in raw)
    except (TypeError, ValueError) as error:
        raise InvalidContextSnapshotError(str(error)) from error


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextRequest:
    """A deterministic request for bounded, task-oriented scientific context."""

    request_id: EntityId
    purpose: str
    seed_entity_ids: tuple[EntityId, ...]
    generated_by: str
    task_id: EntityId | None = None
    mission_id: EntityId | None = None
    max_depth: int = 1
    max_entities: int = 20
    relationship_type_filters: tuple[RelationshipType, ...] = ()
    include_archived: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, EntityId):
            raise TypeError("request_id must be an EntityId")
        object.__setattr__(self, "purpose", require_non_empty(self.purpose, "purpose"))
        object.__setattr__(
            self, "generated_by", require_non_empty(self.generated_by, "generated_by")
        )
        for field_name in ("task_id", "mission_id"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, EntityId):
                raise TypeError(f"{field_name} must be an EntityId when provided")
        if self.task_id is None and self.mission_id is None:
            raise InvalidContextRequestError(
                "ContextRequest requires a task or mission reference"
            )
        seed_entity_ids = _freeze_entity_ids(
            self.seed_entity_ids,
            "seed_entity_ids",
            require_values=True,
            sort_values=True,
        )
        object.__setattr__(self, "seed_entity_ids", seed_entity_ids)
        if isinstance(self.max_depth, bool) or not isinstance(self.max_depth, int):
            raise InvalidContextRequestError("max_depth must be an integer")
        if self.max_depth < 0:
            raise InvalidContextRequestError("max_depth cannot be negative")
        if isinstance(self.max_entities, bool) or not isinstance(self.max_entities, int):
            raise InvalidContextRequestError("max_entities must be an integer")
        if self.max_entities <= 0:
            raise InvalidContextRequestError("max_entities must be positive")
        if self.max_entities < len(seed_entity_ids):
            raise InvalidContextRequestError(
                "max_entities cannot be smaller than the number of seed entities"
            )
        filters = tuple(self.relationship_type_filters)
        if not all(isinstance(value, RelationshipType) for value in filters):
            raise TypeError(
                "relationship_type_filters must contain RelationshipType values"
            )
        object.__setattr__(
            self,
            "relationship_type_filters",
            tuple(sorted(set(filters), key=lambda value: value.value)),
        )
        if not isinstance(self.include_archived, bool):
            raise TypeError("include_archived must be a bool")

    @property
    def task_reference(self) -> EntityId | None:
        """Map the request's canonical task ID to ContextSnapshot terminology."""
        return self.task_id

    @property
    def mission_reference(self) -> EntityId | None:
        """Map the request's canonical mission ID to ContextSnapshot terminology."""
        return self.mission_id


@dataclass(frozen=True, slots=True)
class ContextQualityResult:
    """Deterministic graph-coverage indicators for one ContextSnapshot."""

    completeness_score: float
    seed_coverage: float
    relationship_coverage: float
    decision_coverage: float
    evidence_coverage: float
    unknown_coverage: float
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "completeness_score",
            "seed_coverage",
            "relationship_coverage",
            "decision_coverage",
            "evidence_coverage",
            "unknown_coverage",
        ):
            object.__setattr__(self, field_name, _score(getattr(self, field_name), field_name))
        object.__setattr__(
            self, "warnings", freeze_strings(self.warnings, "warnings")
        )
        object.__setattr__(
            self, "limitations", freeze_strings(self.limitations, "limitations")
        )

    def to_context_data(self) -> dict[str, object]:
        """Return a JSON-compatible representation for ContextSnapshot data."""
        return {
            "completeness_score": self.completeness_score,
            "seed_coverage": self.seed_coverage,
            "relationship_coverage": self.relationship_coverage,
            "decision_coverage": self.decision_coverage,
            "evidence_coverage": self.evidence_coverage,
            "unknown_coverage": self.unknown_coverage,
            "warnings": self.warnings,
            "limitations": self.limitations,
        }

    @classmethod
    def from_context_data(cls, values: Mapping[str, object]) -> ContextQualityResult:
        """Reconstruct quality indicators from frozen ContextSnapshot data."""
        if not isinstance(values, Mapping):
            raise InvalidContextSnapshotError("quality must be a mapping")
        try:
            return cls(
                completeness_score=values["completeness_score"],  # type: ignore[arg-type]
                seed_coverage=values["seed_coverage"],  # type: ignore[arg-type]
                relationship_coverage=values["relationship_coverage"],  # type: ignore[arg-type]
                decision_coverage=values["decision_coverage"],  # type: ignore[arg-type]
                evidence_coverage=values["evidence_coverage"],  # type: ignore[arg-type]
                unknown_coverage=values["unknown_coverage"],  # type: ignore[arg-type]
                warnings=_mapping_string_tuple(values, "warnings"),
                limitations=_mapping_string_tuple(values, "limitations"),
            )
        except KeyError as error:
            raise InvalidContextSnapshotError(
                f"quality is missing {error.args[0]}"
            ) from error


@dataclass(frozen=True, slots=True)
class ContextSelectionExplanation:
    """Auditable IDs and rules explaining deterministic context selection."""

    requested_seed_entity_ids: tuple[EntityId, ...]
    included_seed_entity_ids: tuple[EntityId, ...]
    missing_seed_entity_ids: tuple[EntityId, ...]
    expanded_entity_ids: tuple[EntityId, ...]
    selected_entity_ids: tuple[EntityId, ...]
    truncated_entity_ids: tuple[EntityId, ...]
    excluded_historical_entity_ids: tuple[EntityId, ...]
    selection_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "requested_seed_entity_ids",
            "included_seed_entity_ids",
            "missing_seed_entity_ids",
            "expanded_entity_ids",
            "selected_entity_ids",
            "truncated_entity_ids",
            "excluded_historical_entity_ids",
        ):
            object.__setattr__(
                self,
                field_name,
                _freeze_entity_ids(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "selection_rules",
            freeze_strings(self.selection_rules, "selection_rules"),
        )

    def to_context_data(self) -> dict[str, object]:
        """Return JSON-compatible selection evidence for ContextSnapshot data."""
        return {
            "requested_seed_entity_ids": tuple(map(str, self.requested_seed_entity_ids)),
            "included_seed_entity_ids": tuple(map(str, self.included_seed_entity_ids)),
            "missing_seed_entity_ids": tuple(map(str, self.missing_seed_entity_ids)),
            "expanded_entity_ids": tuple(map(str, self.expanded_entity_ids)),
            "selected_entity_ids": tuple(map(str, self.selected_entity_ids)),
            "truncated_entity_ids": tuple(map(str, self.truncated_entity_ids)),
            "excluded_historical_entity_ids": tuple(
                map(str, self.excluded_historical_entity_ids)
            ),
            "selection_rules": self.selection_rules,
        }

    @classmethod
    def from_context_data(
        cls, values: Mapping[str, object]
    ) -> ContextSelectionExplanation:
        """Reconstruct the explanation from frozen ContextSnapshot data."""
        if not isinstance(values, Mapping):
            raise InvalidContextSnapshotError("selection_explanation must be a mapping")
        return cls(
            requested_seed_entity_ids=_mapping_entity_ids(
                values, "requested_seed_entity_ids"
            ),
            included_seed_entity_ids=_mapping_entity_ids(
                values, "included_seed_entity_ids"
            ),
            missing_seed_entity_ids=_mapping_entity_ids(
                values, "missing_seed_entity_ids"
            ),
            expanded_entity_ids=_mapping_entity_ids(values, "expanded_entity_ids"),
            selected_entity_ids=_mapping_entity_ids(values, "selected_entity_ids"),
            truncated_entity_ids=_mapping_entity_ids(values, "truncated_entity_ids"),
            excluded_historical_entity_ids=_mapping_entity_ids(
                values, "excluded_historical_entity_ids"
            ),
            selection_rules=_mapping_string_tuple(values, "selection_rules"),
        )
