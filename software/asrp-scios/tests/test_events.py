"""Tests for immutable scientific event contracts."""

from datetime import datetime, timezone
from types import MappingProxyType
import unittest

from asrp_scios.contracts import ScientificEvent, Traceability


def traceability() -> Traceability:
    return Traceability(
        requirements=("Sprint-001",),
        decisions=("ADR-0002",),
        specifications=("ARC-001", "RFC-0001"),
        implementation_version="0.1.0",
    )


class ScientificEventTests(unittest.TestCase):
    def test_create_deeply_freezes_payload(self) -> None:
        payload = {"entity": {"tags": ["hypothesis", "candidate"]}}

        event = ScientificEvent.create(
            event_type="HypothesisCreated",
            source="test.plugin",
            traceability=traceability(),
            payload=payload,
        )
        payload["entity"]["tags"].append("changed")  # type: ignore[index,union-attr]

        self.assertIsInstance(event.payload, MappingProxyType)
        self.assertEqual(
            event.payload["entity"]["tags"],  # type: ignore[index]
            ("hypothesis", "candidate"),
        )
        with self.assertRaises(TypeError):
            event.payload["new"] = "value"  # type: ignore[index]

    def test_rejects_non_serializable_payload_values(self) -> None:
        with self.assertRaises(TypeError):
            ScientificEvent.create(
                event_type="EvidenceAdded",
                source="test.plugin",
                traceability=traceability(),
                payload={"unsupported": object()},
            )

    def test_rejects_naive_timestamps(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            ScientificEvent(
                event_id="fdc2b7f0-48b9-407f-9807-206a8073af0c",
                event_type="EvidenceAdded",
                occurred_at=datetime.now(),
                source="test.plugin",
                traceability=traceability(),
            )

    def test_create_generates_utc_timestamp(self) -> None:
        event = ScientificEvent.create(
            event_type="ReviewRequested",
            source="test.plugin",
            traceability=traceability(),
        )

        self.assertEqual(event.occurred_at.utcoffset(), timezone.utc.utcoffset(None))


if __name__ == "__main__":
    unittest.main()

