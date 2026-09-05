"""SRG-backed ContextSnapshot generation service.

Purpose:
    Select bounded scientific context and generate the existing ContextSnapshot.
Responsibilities:
    Expand seeds, apply canonical priorities, close relationships, assess graph
    coverage, preserve provenance/traceability, validate, and explain selection.
Inputs:
    ContextRequest values and a Sprint-003 ScientificResearchGraph implementation.
Outputs:
    Immutable domain ContextSnapshot, ContextQualityResult, and explanation values.
Dependencies:
    ASRP-SciOS domain model, SRG protocol, and Python standard library only.
Limitations:
    Process-local deterministic selection; no interpretation, LLM, or persistence.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from asrp_scios.contracts._validation import require_aware_datetime
from asrp_scios.domain.aggregates import (
    ContextSnapshot,
    Discovery,
    Hypothesis,
    ResearchCampaign,
    ResearchDecision,
    ScientificQuestion,
)
from asrp_scios.domain.entities import (
    Evidence,
    KnowledgeItem,
    ScientificEntity,
    ScientificProgram,
    Unknown,
)
from asrp_scios.domain.lifecycle import LifecycleStatus
from asrp_scios.domain.relationships import ScientificRelationship
from asrp_scios.domain.value_objects import (
    AggregateId,
    EntityId,
    Provenance,
    RelationshipType,
    Traceability,
    Version,
)
from asrp_scios.srg import GraphDirection, ScientificResearchGraph

from .errors import ContextGraphInconsistencyError, InvalidContextSnapshotError
from .model import (
    ContextQualityResult,
    ContextRequest,
    ContextSelectionExplanation,
)
from .policy import ContextSelectionPolicy


_SELECTION_RULES = (
    "Available seed entities are included before expanded entities.",
    "Expansion is bounded by max_depth and max_entities.",
    "Non-seed entities use canonical type priority and then stable identity.",
    "Relationships require both selected endpoints and use canonical priority.",
    "Archived or deprecated records require an explicit request or traceability link.",
)


@dataclass(frozen=True, slots=True)
class _Selection:
    included_seed_entities: tuple[ScientificEntity, ...]
    missing_seed_entity_ids: tuple[EntityId, ...]
    candidate_entities: tuple[ScientificEntity, ...]
    selected_entities: tuple[ScientificEntity, ...]
    candidate_relationships: tuple[ScientificRelationship, ...]
    selected_relationships: tuple[ScientificRelationship, ...]
    truncated_entities: tuple[ScientificEntity, ...]
    excluded_historical_entity_ids: tuple[EntityId, ...]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _coverage(selected: int, available: int) -> float:
    if available <= 0:
        return 0.0
    return round(selected / available, 6)


def _provenance_data(provenance: Provenance) -> dict[str, object]:
    return {
        "creator": provenance.creator,
        "created_at": provenance.created_at.isoformat(),
        "source": provenance.source,
        "related_evidence": provenance.related_evidence,
        "review_history": provenance.review_history,
        "dependencies": provenance.dependencies,
        "method": provenance.method,
        "input_entities": provenance.input_entities,
        "transformation_process": provenance.transformation_process,
        "tool_or_system": provenance.tool_or_system,
        "review_status": provenance.review_status,
        "version_history": provenance.version_history,
    }


def _traceability_data(traceability: Traceability) -> dict[str, object]:
    return {
        "requirements": traceability.requirements,
        "decisions": traceability.decisions,
        "specifications": traceability.specifications,
        "implementation_version": traceability.implementation_version,
        "scientific_program": traceability.scientific_program,
    }


def _entity_data(entity: ScientificEntity) -> dict[str, object]:
    return {
        "entity_id": str(entity.id),
        "entity_type": entity.entity_type,
        "title": entity.title,
        "description": entity.description,
        "status": entity.status.value,
        "version": str(entity.version),
        "provenance": _provenance_data(entity.provenance),
        "traceability": _traceability_data(entity.traceability),
    }


def _relationship_data(
    relationship: ScientificRelationship,
) -> dict[str, object]:
    return {
        "relationship_id": str(relationship.relationship_id),
        "relationship_type": relationship.relationship_type.value,
        "source_entity_id": str(relationship.source_entity_id),
        "target_entity_id": str(relationship.target_entity_id),
        "status": relationship.status.value,
        "rationale": relationship.rationale,
        "confidence": {
            "level": relationship.confidence.level.value,
            "rationale": relationship.confidence.rationale,
            "assessed_at": relationship.confidence.assessed_at.isoformat(),
            "evidence_references": tuple(
                map(str, relationship.confidence.evidence_references)
            ),
            "score": relationship.confidence.score,
        },
        "created_at": relationship.created_at.isoformat(),
        "created_by": relationship.created_by,
        "provenance": _provenance_data(relationship.provenance),
        "traceability": _traceability_data(relationship.traceability),
    }


class ContextSnapshotGenerator:
    """Generate minimal immutable ContextSnapshot projections from an SRG."""

    __slots__ = ("_clock", "_policy")

    def __init__(
        self,
        policy: ContextSelectionPolicy | None = None,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        if policy is not None and not isinstance(policy, ContextSelectionPolicy):
            raise TypeError("policy must be a ContextSelectionPolicy")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._policy = policy or ContextSelectionPolicy()
        self._clock = clock

    @property
    def policy(self) -> ContextSelectionPolicy:
        """Return the immutable selection policy used by this generator."""
        return self._policy

    def select_relevant_entities(
        self, request: ContextRequest, srg: ScientificResearchGraph
    ) -> tuple[ScientificEntity, ...]:
        """Return bounded selected entities in deterministic priority order."""
        return self._select(request, srg).selected_entities

    def select_relevant_relationships(
        self, request: ContextRequest, srg: ScientificResearchGraph
    ) -> tuple[ScientificRelationship, ...]:
        """Return relationship closure for the deterministically selected entities."""
        return self._select(request, srg).selected_relationships

    def generate_context_snapshot(
        self, request: ContextRequest, srg: ScientificResearchGraph
    ) -> ContextSnapshot:
        """Generate and validate an existing domain ContextSnapshot aggregate."""
        selection = self._select(request, srg)
        explanation = self._explain(request, selection)
        quality = self._quality(request, selection, explanation)
        generated_at = require_aware_datetime(self._clock(), "generated_at")
        selected_entities = selection.selected_entities
        selected_relationships = selection.selected_relationships

        context_data: dict[str, object] = {
            "request_id": str(request.request_id),
            "task_id": str(request.task_id) if request.task_id else None,
            "mission_id": str(request.mission_id) if request.mission_id else None,
            "purpose": request.purpose,
            "generated_at": generated_at.isoformat(),
            "generated_by": request.generated_by,
            "seed_entity_ids": tuple(map(str, request.seed_entity_ids)),
            "max_depth": request.max_depth,
            "max_entities": request.max_entities,
            "relationship_type_filters": tuple(
                value.value for value in request.relationship_type_filters
            ),
            "include_archived": request.include_archived,
            "selected_entity_ids": tuple(str(value.id) for value in selected_entities),
            "selected_entities": tuple(_entity_data(value) for value in selected_entities),
            "selected_relationships": tuple(
                _relationship_data(value) for value in selected_relationships
            ),
            "key_questions": self._ids_of_type(selected_entities, ScientificQuestion),
            "key_hypotheses": self._ids_of_type(selected_entities, Hypothesis),
            "key_evidence": self._ids_of_type(selected_entities, Evidence),
            "key_decisions": self._ids_of_type(selected_entities, ResearchDecision),
            "key_unknowns": self._ids_of_type(selected_entities, Unknown),
            "key_knowledge": self._ids_of_type(selected_entities, KnowledgeItem),
            "scientific_programs": self._ids_of_type(
                selected_entities, ScientificProgram
            ),
            "research_campaigns": self._ids_of_type(
                selected_entities, ResearchCampaign
            ),
            "discoveries": self._ids_of_type(selected_entities, Discovery),
            "limitations": self._domain_limitations(selected_entities)
            + quality.limitations,
            "next_actions": self._next_actions(selected_entities),
            "open_items": self._ids_of_type(selected_entities, Unknown),
            "quality": quality.to_context_data(),
            "selection_explanation": explanation.to_context_data(),
            "selection_metrics": self._selection_metrics(selection, request),
        }
        support_reference = request.task_reference or request.mission_reference
        snapshot = ContextSnapshot(
            id=AggregateId(f"context:{request.request_id}"),
            title=f"Context snapshot for {support_reference}",
            description=request.purpose,
            status=LifecycleStatus.ACTIVE,
            version=Version(1),
            created_at=generated_at,
            updated_at=generated_at,
            created_by=request.generated_by,
            provenance=Provenance(
                creator=request.generated_by,
                created_at=generated_at,
                source="Scientific Research Graph",
                related_evidence=self._ids_of_type(selected_entities, Evidence),
                dependencies=tuple(
                    str(value.relationship_id) for value in selected_relationships
                ),
                method="deterministic bounded SRG context selection",
                input_entities=tuple(map(str, request.seed_entity_ids)),
                transformation_process="ContextSnapshotGeneration",
                tool_or_system="ASRP-SciOS Context Engineering MVP",
                review_status="NotRequested",
                version_history=("0.4.0",),
            ),
            traceability=Traceability(
                requirements=("DDD-001", "ONT-001", "AGG-001", "CAP-001"),
                decisions=("ADR-0001", "ADR-0002"),
                specifications=(
                    "Sprint-004/CONTEXT_MVP_SPEC",
                    "Sprint-004/CONTEXT_SELECTION_RULES",
                    "Sprint-004/CONTEXT_QUALITY_MODEL",
                ),
                implementation_version="0.4.0",
            ),
            mission_reference=request.mission_reference,
            task_reference=request.task_reference,
            context_data=context_data,
            scientific_entity_ids=tuple(value.id for value in selected_entities),
            relationships=tuple(
                value.relationship_id for value in selected_relationships
            ),
        )
        self.validate_context_snapshot(snapshot)
        return snapshot

    def compute_context_quality(
        self, snapshot: ContextSnapshot, request: ContextRequest
    ) -> ContextQualityResult:
        """Recompute quality deterministically from snapshot selection metrics."""
        if not isinstance(request, ContextRequest):
            raise TypeError("request must be a ContextRequest")
        self.validate_context_snapshot(snapshot)
        if snapshot.context_data.get("request_id") != str(request.request_id):
            raise InvalidContextSnapshotError(
                "snapshot request_id does not match ContextRequest"
            )
        explanation = self.explain_context_selection(snapshot)
        metrics = snapshot.context_data.get("selection_metrics")
        if not isinstance(metrics, Mapping):
            raise InvalidContextSnapshotError("selection_metrics must be a mapping")
        return self._quality_from_metrics(request, explanation, metrics)

    def explain_context_selection(
        self, snapshot: ContextSnapshot
    ) -> ContextSelectionExplanation:
        """Return the structured, non-interpretive rationale embedded in a snapshot."""
        if not isinstance(snapshot, ContextSnapshot):
            raise TypeError("snapshot must be a ContextSnapshot")
        values = snapshot.context_data.get("selection_explanation")
        if not isinstance(values, Mapping):
            raise InvalidContextSnapshotError(
                "selection_explanation must be a mapping"
            )
        return ContextSelectionExplanation.from_context_data(values)

    def validate_context_snapshot(self, snapshot: ContextSnapshot) -> None:
        """Raise a context-specific error when projection closure is inconsistent."""
        if not isinstance(snapshot, ContextSnapshot):
            raise TypeError("snapshot must be a ContextSnapshot")
        issues: list[str] = []
        selected_ids = tuple(str(value) for value in snapshot.scientific_entity_ids)
        if len(selected_ids) != len(set(selected_ids)):
            issues.append("scientific_entity_ids contains duplicates")
        data_selected = snapshot.context_data.get("selected_entity_ids")
        if not isinstance(data_selected, Sequence) or isinstance(data_selected, str):
            issues.append("selected_entity_ids must be a sequence")
        elif tuple(data_selected) != selected_ids:
            issues.append("selected_entity_ids does not match scientific_entity_ids")

        seed_ids = snapshot.context_data.get("seed_entity_ids")
        explanation: ContextSelectionExplanation | None = None
        try:
            explanation = self.explain_context_selection(snapshot)
        except (InvalidContextSnapshotError, TypeError, ValueError) as error:
            issues.append(str(error))
        if not isinstance(seed_ids, Sequence) or isinstance(seed_ids, str):
            issues.append("seed_entity_ids must be a sequence")
        elif explanation is not None:
            requested = tuple(map(str, explanation.requested_seed_entity_ids))
            if tuple(seed_ids) != requested:
                issues.append("seed_entity_ids does not match selection explanation")
            included = set(map(str, explanation.included_seed_entity_ids))
            if not included.issubset(set(selected_ids)):
                issues.append("included seeds must occur in selected entities")

        relationship_rows = snapshot.context_data.get("selected_relationships")
        relationship_ids: list[str] = []
        if not isinstance(relationship_rows, Sequence) or isinstance(
            relationship_rows, str
        ):
            issues.append("selected_relationships must be a sequence")
        else:
            for index, row in enumerate(relationship_rows):
                if not isinstance(row, Mapping):
                    issues.append(f"selected_relationships[{index}] must be a mapping")
                    continue
                relationship_id = row.get("relationship_id")
                source_id = row.get("source_entity_id")
                target_id = row.get("target_entity_id")
                if not all(
                    isinstance(value, str)
                    for value in (relationship_id, source_id, target_id)
                ):
                    issues.append(
                        f"selected_relationships[{index}] has invalid identifiers"
                    )
                    continue
                relationship_ids.append(relationship_id)
                if source_id not in selected_ids or target_id not in selected_ids:
                    issues.append(
                        f"selected_relationships[{index}] endpoint is not selected"
                    )
        if tuple(map(str, snapshot.relationships)) != tuple(relationship_ids):
            issues.append("relationship IDs do not match snapshot relationships")

        quality_values = snapshot.context_data.get("quality")
        quality: ContextQualityResult | None = None
        try:
            quality = ContextQualityResult.from_context_data(quality_values)  # type: ignore[arg-type]
        except (InvalidContextSnapshotError, TypeError, ValueError) as error:
            issues.append(str(error))
        metrics = snapshot.context_data.get("selection_metrics")
        if not isinstance(metrics, Mapping):
            issues.append("selection_metrics must be a mapping")
        elif explanation is not None and quality is not None:
            try:
                stored_request = self._request_from_snapshot(snapshot)
                expected_quality = self._quality_from_metrics(
                    stored_request, explanation, metrics
                )
                if quality != expected_quality:
                    issues.append("quality does not match selection metrics")
            except (InvalidContextSnapshotError, TypeError, ValueError) as error:
                issues.append(str(error))
        if issues:
            raise InvalidContextSnapshotError("; ".join(issues))

    @staticmethod
    def _request_from_snapshot(snapshot: ContextSnapshot) -> ContextRequest:
        data = snapshot.context_data

        def required_string(name: str) -> str:
            value = data.get(name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidContextSnapshotError(f"{name} must be a non-empty string")
            return value

        raw_seed_ids = data.get("seed_entity_ids")
        if not isinstance(raw_seed_ids, Sequence) or isinstance(raw_seed_ids, str):
            raise InvalidContextSnapshotError("seed_entity_ids must be a sequence")
        raw_filters = data.get("relationship_type_filters")
        if not isinstance(raw_filters, Sequence) or isinstance(raw_filters, str):
            raise InvalidContextSnapshotError(
                "relationship_type_filters must be a sequence"
            )
        try:
            seed_entity_ids = tuple(EntityId(value) for value in raw_seed_ids)
            relationship_filters = tuple(
                RelationshipType(value) for value in raw_filters
            )
        except (TypeError, ValueError) as error:
            raise InvalidContextSnapshotError(str(error)) from error
        request = ContextRequest(
            request_id=EntityId(required_string("request_id")),
            task_id=snapshot.task_reference,
            mission_id=snapshot.mission_reference,
            purpose=required_string("purpose"),
            seed_entity_ids=seed_entity_ids,
            max_depth=data.get("max_depth"),  # type: ignore[arg-type]
            max_entities=data.get("max_entities"),  # type: ignore[arg-type]
            relationship_type_filters=relationship_filters,
            include_archived=data.get("include_archived"),  # type: ignore[arg-type]
            generated_by=required_string("generated_by"),
        )
        expected_task_id = str(request.task_id) if request.task_id else None
        expected_mission_id = str(request.mission_id) if request.mission_id else None
        if data.get("task_id") != expected_task_id:
            raise InvalidContextSnapshotError(
                "task_id does not match ContextSnapshot task_reference"
            )
        if data.get("mission_id") != expected_mission_id:
            raise InvalidContextSnapshotError(
                "mission_id does not match ContextSnapshot mission_reference"
            )
        if snapshot.description != request.purpose:
            raise InvalidContextSnapshotError(
                "purpose does not match ContextSnapshot description"
            )
        if snapshot.created_by != request.generated_by:
            raise InvalidContextSnapshotError(
                "generated_by does not match ContextSnapshot created_by"
            )
        if str(snapshot.id) != f"context:{request.request_id}":
            raise InvalidContextSnapshotError(
                "ContextSnapshot ID does not match request_id"
            )
        return request

    def _select(
        self, request: ContextRequest, srg: ScientificResearchGraph
    ) -> _Selection:
        if not isinstance(request, ContextRequest):
            raise TypeError("request must be a ContextRequest")
        if not isinstance(srg, ScientificResearchGraph):
            raise TypeError("srg must implement ScientificResearchGraph")

        candidates: dict[str, ScientificEntity] = {}
        included_seeds: list[ScientificEntity] = []
        missing_seeds: list[EntityId] = []
        queue: deque[tuple[str, int]] = deque()
        for entity_id in request.seed_entity_ids:
            entity = srg.get_entity(entity_id)
            if entity is None:
                missing_seeds.append(entity_id)
                continue
            key = str(entity.id)
            candidates[key] = entity
            included_seeds.append(entity)
            queue.append((key, 0))

        visited_depth = {key: 0 for key in candidates}
        excluded_historical: dict[str, EntityId] = {}
        filters = set(request.relationship_type_filters)
        while queue:
            current_key, depth = queue.popleft()
            if depth >= request.max_depth:
                continue
            current_entity = candidates[current_key]
            relationships = srg.get_relationships(
                entity_id=current_key, direction=GraphDirection.BOTH
            )
            for relationship in sorted(
                relationships, key=self._policy.relationship_sort_key
            ):
                if filters and relationship.relationship_type not in filters:
                    continue
                if (
                    self._policy.is_historical(current_entity)
                    and not request.include_archived
                    and not self._policy.preserves_traceability(relationship)
                ):
                    continue
                source_key = str(relationship.source_entity_id)
                target_key = str(relationship.target_entity_id)
                neighbor_key = target_key if source_key == current_key else source_key
                neighbor = srg.get_entity(neighbor_key)
                if neighbor is None:
                    raise ContextGraphInconsistencyError(
                        f"relationship endpoint is absent from SRG: {neighbor_key}"
                    )
                historical_allowed = (
                    request.include_archived
                    or not self._policy.is_historical(neighbor)
                    or self._policy.preserves_traceability(relationship)
                )
                if not historical_allowed:
                    if neighbor_key not in candidates:
                        excluded_historical[neighbor_key] = neighbor.id
                    continue
                excluded_historical.pop(neighbor_key, None)
                next_depth = depth + 1
                previous_depth = visited_depth.get(neighbor_key)
                if previous_depth is None or next_depth < previous_depth:
                    visited_depth[neighbor_key] = next_depth
                    candidates[neighbor_key] = neighbor
                    queue.append((neighbor_key, next_depth))

        seed_keys = {str(value.id) for value in included_seeds}
        ordered_seeds = tuple(sorted(included_seeds, key=lambda value: str(value.id)))
        ordered_expanded = tuple(
            sorted(
                (
                    value
                    for key, value in candidates.items()
                    if key not in seed_keys
                ),
                key=self._policy.entity_sort_key,
            )
        )
        capacity = request.max_entities - len(ordered_seeds)
        selected_entities = ordered_seeds + ordered_expanded[:capacity]
        truncated_entities = ordered_expanded[capacity:]
        candidate_entities = ordered_seeds + ordered_expanded
        candidate_keys = {str(value.id) for value in candidate_entities}
        selected_keys = {str(value.id) for value in selected_entities}
        candidate_relationships = self._relationship_closure(
            srg, candidate_keys, request
        )
        selected_relationships = tuple(
            value
            for value in candidate_relationships
            if str(value.source_entity_id) in selected_keys
            and str(value.target_entity_id) in selected_keys
        )
        return _Selection(
            included_seed_entities=ordered_seeds,
            missing_seed_entity_ids=tuple(sorted(missing_seeds, key=str)),
            candidate_entities=candidate_entities,
            selected_entities=selected_entities,
            candidate_relationships=candidate_relationships,
            selected_relationships=selected_relationships,
            truncated_entities=truncated_entities,
            excluded_historical_entity_ids=tuple(
                sorted(excluded_historical.values(), key=str)
            ),
        )

    def _relationship_closure(
        self,
        srg: ScientificResearchGraph,
        entity_keys: set[str],
        request: ContextRequest,
    ) -> tuple[ScientificRelationship, ...]:
        filters = set(request.relationship_type_filters)
        matches = []
        for relationship in srg.get_relationships():
            if str(relationship.source_entity_id) not in entity_keys or str(
                relationship.target_entity_id
            ) not in entity_keys:
                continue
            if filters and relationship.relationship_type not in filters:
                continue
            if (
                self._policy.is_historical_relationship(relationship)
                and not request.include_archived
                and not self._policy.preserves_traceability(relationship)
            ):
                continue
            matches.append(relationship)
        return tuple(sorted(matches, key=self._policy.relationship_sort_key))

    def _explain(
        self, request: ContextRequest, selection: _Selection
    ) -> ContextSelectionExplanation:
        seed_keys = {str(value) for value in request.seed_entity_ids}
        return ContextSelectionExplanation(
            requested_seed_entity_ids=request.seed_entity_ids,
            included_seed_entity_ids=tuple(
                value.id for value in selection.included_seed_entities
            ),
            missing_seed_entity_ids=selection.missing_seed_entity_ids,
            expanded_entity_ids=tuple(
                value.id
                for value in selection.candidate_entities
                if str(value.id) not in seed_keys
            ),
            selected_entity_ids=tuple(value.id for value in selection.selected_entities),
            truncated_entity_ids=tuple(value.id for value in selection.truncated_entities),
            excluded_historical_entity_ids=selection.excluded_historical_entity_ids,
            selection_rules=_SELECTION_RULES,
        )

    def _quality(
        self,
        request: ContextRequest,
        selection: _Selection,
        explanation: ContextSelectionExplanation,
    ) -> ContextQualityResult:
        return self._quality_from_metrics(
            request, explanation, self._selection_metrics(selection, request)
        )

    def _quality_from_metrics(
        self,
        request: ContextRequest,
        explanation: ContextSelectionExplanation,
        metrics: Mapping[str, object],
    ) -> ContextQualityResult:
        def count(name: str) -> int:
            value = metrics.get(name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise InvalidContextSnapshotError(
                    f"selection_metrics.{name} must be a non-negative integer"
                )
            return value

        requested_seeds = count("requested_seed_count")
        included_seeds = count("included_seed_count")
        candidate_relationships = count("candidate_relationship_count")
        selected_relationships = count("selected_relationship_count")
        candidate_decisions = count("candidate_decision_count")
        selected_decisions = count("selected_decision_count")
        candidate_evidence = count("candidate_evidence_count")
        selected_evidence = count("selected_evidence_count")
        candidate_unknowns = count("candidate_unknown_count")
        selected_unknowns = count("selected_unknown_count")

        seed_coverage = _coverage(included_seeds, requested_seeds)
        relationship_coverage = _coverage(
            selected_relationships, candidate_relationships
        )
        decision_coverage = _coverage(selected_decisions, candidate_decisions)
        evidence_coverage = _coverage(selected_evidence, candidate_evidence)
        unknown_coverage = _coverage(selected_unknowns, candidate_unknowns)
        completeness_score = round(
            0.30 * seed_coverage
            + 0.20 * relationship_coverage
            + 0.20 * decision_coverage
            + 0.20 * evidence_coverage
            + 0.10 * unknown_coverage,
            6,
        )

        warnings: list[str] = []
        if explanation.missing_seed_entity_ids:
            warnings.append(
                "Missing seed entities: "
                + ", ".join(map(str, explanation.missing_seed_entity_ids))
            )
        if explanation.truncated_entity_ids:
            warnings.append(
                f"max_entities truncated {len(explanation.truncated_entity_ids)} "
                "reachable entities"
            )
        if request.max_depth == 0:
            warnings.append("max_depth is zero; graph expansion was not performed")
        if selected_relationships == 0:
            warnings.append("No relationships connect the selected entities")
        if selected_evidence == 0:
            warnings.append("No Evidence entity is included")
        if selected_decisions == 0:
            warnings.append("No ResearchDecision entity is included")
        if candidate_unknowns > 0 and selected_unknowns == 0:
            warnings.append("Reachable Unknown entities were not included")

        limitations = [
            f"Selection is bounded to max_depth={request.max_depth} and "
            f"max_entities={request.max_entities}.",
            "Coverage scores describe in-memory SRG selection, not scientific validity.",
        ]
        if request.relationship_type_filters:
            limitations.append(
                "Relationship selection is restricted to: "
                + ", ".join(
                    value.value for value in request.relationship_type_filters
                )
                + "."
            )
        if explanation.excluded_historical_entity_ids:
            limitations.append(
                "Archived or deprecated entities were excluded unless required "
                "for traceability."
            )
        return ContextQualityResult(
            completeness_score=completeness_score,
            seed_coverage=seed_coverage,
            relationship_coverage=relationship_coverage,
            decision_coverage=decision_coverage,
            evidence_coverage=evidence_coverage,
            unknown_coverage=unknown_coverage,
            warnings=tuple(warnings),
            limitations=tuple(limitations),
        )

    @staticmethod
    def _selection_metrics(
        selection: _Selection, request: ContextRequest
    ) -> dict[str, object]:
        return {
            "requested_seed_count": len(request.seed_entity_ids),
            "included_seed_count": len(selection.included_seed_entities),
            "candidate_entity_count": len(selection.candidate_entities),
            "selected_entity_count": len(selection.selected_entities),
            "candidate_relationship_count": len(selection.candidate_relationships),
            "selected_relationship_count": len(selection.selected_relationships),
            "candidate_decision_count": sum(
                isinstance(value, ResearchDecision)
                for value in selection.candidate_entities
            ),
            "selected_decision_count": sum(
                isinstance(value, ResearchDecision)
                for value in selection.selected_entities
            ),
            "candidate_evidence_count": sum(
                isinstance(value, Evidence) for value in selection.candidate_entities
            ),
            "selected_evidence_count": sum(
                isinstance(value, Evidence) for value in selection.selected_entities
            ),
            "candidate_unknown_count": sum(
                isinstance(value, Unknown) for value in selection.candidate_entities
            ),
            "selected_unknown_count": sum(
                isinstance(value, Unknown) for value in selection.selected_entities
            ),
        }

    @staticmethod
    def _ids_of_type(
        entities: Sequence[ScientificEntity], entity_type: type[ScientificEntity]
    ) -> tuple[str, ...]:
        return tuple(str(value.id) for value in entities if isinstance(value, entity_type))

    @staticmethod
    def _domain_limitations(
        entities: Sequence[ScientificEntity],
    ) -> tuple[str, ...]:
        limitations: list[str] = []
        for entity in entities:
            values = getattr(entity, "limitations", ())
            for value in values:
                if value not in limitations:
                    limitations.append(value)
        return tuple(limitations)

    @staticmethod
    def _next_actions(entities: Sequence[ScientificEntity]) -> tuple[str, ...]:
        actions: list[str] = []
        for entity in entities:
            if not isinstance(entity, Unknown):
                continue
            for value in entity.proposed_investigations:
                if value not in actions:
                    actions.append(value)
        return tuple(actions)
