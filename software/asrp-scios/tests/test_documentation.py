"""Regression tests for mandatory public module documentation sections."""

import importlib
import unittest


PUBLIC_MODULES = (
    "asrp_scios",
    "asrp_scios.contracts",
    "asrp_scios.contracts.common",
    "asrp_scios.contracts.cognitive",
    "asrp_scios.contracts.events",
    "asrp_scios.contracts.graph",
    "asrp_scios.contracts.method",
    "asrp_scios.context",
    "asrp_scios.context.errors",
    "asrp_scios.context.generator",
    "asrp_scios.context.model",
    "asrp_scios.context.policy",
    "asrp_scios.eventing",
    "asrp_scios.eventing.in_memory",
    "asrp_scios.kernel",
    "asrp_scios.kernel.plugin",
    "asrp_scios.kernel.runtime",
    "asrp_scios.srg",
    "asrp_scios.srg.errors",
    "asrp_scios.srg.in_memory",
    "asrp_scios.srg.model",
    "asrp_scios.srg.protocol",
)


class PublicModuleDocumentationTests(unittest.TestCase):
    def test_public_modules_document_required_coding_standard_sections(self) -> None:
        required_sections = (
            "Purpose:",
            "Responsibilities:",
            "Inputs:",
            "Outputs:",
            "Dependencies:",
            "Limitations:",
        )
        for module_name in PUBLIC_MODULES:
            with self.subTest(module=module_name):
                documentation = importlib.import_module(module_name).__doc__ or ""
                for section in required_sections:
                    self.assertIn(section, documentation)


if __name__ == "__main__":
    unittest.main()
