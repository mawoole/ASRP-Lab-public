"""Sprint-005 acceptance tests for the Context Recovery Benchmark MVP."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


BENCHMARK_PACKAGE_ROOT = Path(__file__).parents[1]
if str(BENCHMARK_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_PACKAGE_ROOT))

from benchmarks.context_recovery import (  # noqa: E402
    ContextRecoveryBenchmark,
    build_context_recovery_fixture,
    calculate_context_recovery_metrics,
    compute_deterministic_output_hash,
    render_markdown_report,
    write_benchmark_reports,
)
from asrp_scios.context import ContextSnapshotGenerator  # noqa: E402


class _SequenceTimer:
    def __init__(self, *values: int) -> None:
        self._values = iter(values)

    def __call__(self) -> int:
        return next(self._values)


class FixtureTests(unittest.TestCase):
    def test_fixture_has_required_types_relationships_and_integrity(self) -> None:
        fixture = build_context_recovery_fixture()
        entity_types = {entity.entity_type for entity in fixture.entities}
        self.assertEqual(len(fixture.entities), 18)
        self.assertEqual(len(fixture.relationships), 22)
        self.assertTrue(
            {
                "ScientificProgram",
                "ResearchCampaign",
                "ScientificQuestion",
                "Hypothesis",
                "Evidence",
                "ResearchDecision",
                "Unknown",
                "KnowledgeItem",
                "ContextSnapshot",
            }.issubset(entity_types)
        )
        relationship_types = {
            relationship.relationship_type.value
            for relationship in fixture.relationships
        }
        self.assertTrue(
            {
                "belongs_to",
                "generates",
                "supports",
                "contradicts",
                "validates",
                "decided_by",
                "derives_from",
                "uses_context",
                "references",
                "depends_on",
            }.issubset(relationship_types)
        )
        self.assertTrue(fixture.graph.validate_graph_integrity().is_valid)

    def test_fixture_inventory_and_scenarios_are_repeatable(self) -> None:
        first = build_context_recovery_fixture()
        second = build_context_recovery_fixture()
        self.assertEqual(first.entities, second.entities)
        self.assertEqual(first.relationships, second.relationships)
        self.assertEqual(first.scenarios, second.scenarios)


class ScenarioAndRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_context_recovery_fixture()

    def test_all_three_scenarios_recover_expected_entity_categories(self) -> None:
        generator = ContextSnapshotGenerator(clock=lambda: self.fixture.fixed_time)
        for scenario in self.fixture.scenarios:
            with self.subTest(scenario=scenario.scenario_id):
                snapshot = generator.generate_context_snapshot(
                    scenario.to_context_request(), self.fixture.graph
                )
                selected_types = {
                    self.fixture.graph.get_entity(entity_id).entity_type
                    for entity_id in snapshot.scientific_entity_ids
                }
                self.assertTrue(set(scenario.expected_entity_types).issubset(selected_types))

    def test_evidence_audit_preserves_direction_and_provenance(self) -> None:
        scenario = self.fixture.scenario("evidence_audit_recovery")
        snapshot = ContextSnapshotGenerator(
            clock=lambda: self.fixture.fixed_time
        ).generate_context_snapshot(scenario.to_context_request(), self.fixture.graph)
        selected_entities = snapshot.context_data["selected_entities"]
        evidence_row = next(
            value
            for value in selected_entities
            if value["entity_id"] == "evidence.support-a"
        )
        self.assertEqual(
            evidence_row["provenance"]["source"], "Synthetic benchmark fixture"
        )
        support_row = next(
            value
            for value in snapshot.context_data["selected_relationships"]
            if value["relationship_id"] == "rel.07"
        )
        self.assertEqual(support_row["relationship_type"], "supports")
        self.assertEqual(support_row["source_entity_id"], "evidence.support-a")
        self.assertEqual(support_row["target_entity_id"], "hypothesis.recovery-a")

    def test_runner_returns_every_required_result_field(self) -> None:
        result = ContextRecoveryBenchmark(self.fixture).run_scenario(
            "hypothesis_review_recovery"
        )
        payload = result.to_dict()
        self.assertEqual(payload["scenario_id"], "hypothesis_review_recovery")
        self.assertGreaterEqual(payload["generation_time_ms"], 0.0)
        self.assertIn("metrics", payload)
        self.assertTrue(payload["selected_entity_ids"])
        self.assertEqual(
            payload["selected_relationship_count"],
            len(payload["selected_relationship_ids"]),
        )
        self.assertEqual(len(payload["deterministic_output_hash"]), 64)

    def test_hash_is_stable_when_only_generation_timing_changes(self) -> None:
        benchmark = ContextRecoveryBenchmark(
            self.fixture,
            timer=_SequenceTimer(0, 1_000_000, 0, 9_000_000),
        )
        first = benchmark.run_scenario("hypothesis_review_recovery")
        second = benchmark.run_scenario("hypothesis_review_recovery")
        self.assertNotEqual(first.generation_time_ms, second.generation_time_ms)
        self.assertEqual(
            first.deterministic_output_hash, second.deterministic_output_hash
        )
        self.assertEqual(
            first.deterministic_output_hash,
            compute_deterministic_output_hash(first.stable_payload()),
        )


class MetricsAndReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_context_recovery_fixture()
        self.scenario = self.fixture.scenario("hypothesis_review_recovery")
        self.generator = ContextSnapshotGenerator(clock=lambda: self.fixture.fixed_time)
        self.request = self.scenario.to_context_request()
        self.snapshot = self.generator.generate_context_snapshot(
            self.request, self.fixture.graph
        )
        self.quality = self.generator.compute_context_quality(
            self.snapshot, self.request
        )

    def test_metrics_match_snapshot_and_source_graph_sizes(self) -> None:
        metrics = calculate_context_recovery_metrics(
            snapshot=self.snapshot,
            quality=self.quality,
            generation_time_ms=1.25,
            source_graph_entity_count=len(self.fixture.entities),
            source_graph_relationship_count=len(self.fixture.relationships),
        )
        self.assertEqual(metrics.context_entity_count, len(self.snapshot.scientific_entity_ids))
        self.assertEqual(metrics.context_relationship_count, len(self.snapshot.relationships))
        self.assertEqual(metrics.source_graph_entity_count, 18)
        self.assertEqual(metrics.source_graph_relationship_count, 22)
        self.assertEqual(
            metrics.context_reduction_ratio,
            round(1 - metrics.context_entity_count / 18, 6),
        )
        self.assertEqual(metrics.seed_coverage, 1.0)

    def test_zero_source_graph_size_reports_reduction_safely(self) -> None:
        metrics = calculate_context_recovery_metrics(
            snapshot=self.snapshot,
            quality=self.quality,
            generation_time_ms=0.0,
            source_graph_entity_count=0,
            source_graph_relationship_count=0,
        )
        self.assertIsNone(metrics.context_reduction_ratio)

    def test_reports_are_structured_and_state_scientific_limitations(self) -> None:
        results = ContextRecoveryBenchmark(self.fixture).run_all()
        markdown = render_markdown_report(results)
        self.assertIn("automated synthetic proxy benchmark", markdown)
        self.assertIn("Human evaluation executed: no", markdown)
        self.assertIn("do not establish faster human recovery", markdown)
        with TemporaryDirectory() as directory:
            json_path, markdown_path = write_benchmark_reports(results, directory)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["benchmark_id"], "sprint-005-context-recovery")
            self.assertFalse(payload["human_evaluation_executed"])
            self.assertEqual(len(payload["results"]), 3)
            self.assertEqual(markdown_path.read_text(encoding="utf-8"), markdown)


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_benchmark_has_no_external_service_or_program_specific_imports(self) -> None:
        source_root = BENCHMARK_PACKAGE_ROOT / "benchmarks" / "context_recovery"
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in source_root.rglob("*.py")
        ).lower()
        forbidden = (
            "import openai",
            "import sqlalchemy",
            "import neo4j",
            "import networkx",
            "import fastapi",
            "import requests",
            "import numpy",
            "import pandas",
            "regenerative medicine",
            "rm-x",
        )
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()

