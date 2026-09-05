# ASRP-SciOS foundation

This package contains the Sprint-001 ASRP-SciOS foundation, the Sprint-002B
Scientific Domain Model baseline, the Sprint-003 in-memory Scientific Research
Graph MVP, and the Sprint-004 Context Engineering MVP. It deliberately
separates stable domain and transport contracts from replaceable
implementations.

## Components

- `asrp_scios.contracts`: immutable scientific contracts and structural engine
  interfaces.
- `asrp_scios.context`: deterministic, bounded, SRG-backed generation of the
  existing immutable `ContextSnapshot` aggregate.
- `asrp_scios.domain`: immutable entities, aggregate roots, domain events,
  relationships, lifecycle vocabularies, value objects, and capability
  descriptors.
- `asrp_scios.eventing`: infrastructure adapters implementing event contracts.
- `asrp_scios.kernel`: the minimal plugin lifecycle runtime.
- `asrp_scios.srg`: deterministic, domain-object-based in-memory registration,
  relationship, neighborhood, bounded-path, traceability, and integrity queries.

The kernel depends on an injected `EventBus`. The bundled
`InMemoryEventBus` is a deterministic reference adapter for local execution
and tests, not a durable message broker.

Scientific Research Graph, Scientific Method Engine, and Scientific Cognitive
System contracts define extension boundaries only. The domain, SRG, and context
packages add no durable storage, API, LLM or embedding integration, scientific
inference, workflow execution, provider selection, or autonomous decisions.

## Validation benchmark

Sprint-005 adds a dependency-free benchmark harness at
`benchmarks/context_recovery/`. It builds an 18-entity synthetic SRG, runs
hypothesis-review, decision-trace, and evidence-audit recovery scenarios through
the existing Context Engineering MVP, and emits JSON and Markdown proxy-metric
reports. The benchmark is outside the runtime package and does not change the
`asrp-scios` 0.4.0 architecture or dependency set.

From the repository root:

```powershell
$env:PYTHONPATH='software/asrp-scios/src'
python -B software/asrp-scios/benchmarks/context_recovery/run_benchmark.py
```
