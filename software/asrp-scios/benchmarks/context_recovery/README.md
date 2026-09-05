# Context Recovery Benchmark

This Sprint-005 harness measures deterministic ContextSnapshot generation over a
small synthetic Scientific Research Graph. It composes the existing
`InMemoryScientificResearchGraph` and `ContextSnapshotGenerator`; it does not
change ASRP-SciOS runtime architecture.

## Scenarios

- Hypothesis Review Recovery: recover the question, supporting/contradicting
  evidence, decision, and unknowns around a hypothesis.
- Decision Trace Recovery: recover the evidence, hypothesis, question,
  knowledge, and prior context behind a decision.
- Evidence Audit Recovery: recover the hypothesis, decision, direction,
  provenance, and related knowledge around evidence.

## Run

From the repository root with Python 3.11 or newer:

```powershell
$env:PYTHONPATH='software/asrp-scios/src'
python -B software/asrp-scios/benchmarks/context_recovery/run_benchmark.py
```

Use `--output-dir PATH` to choose a different local report directory. The
default JSON and Markdown outputs are written to `artifacts/` beside this file.

## Metrics

The result includes generation latency, seed/relationship/decision/evidence/
unknown coverage, context and source graph sizes, context reduction ratio, the
Sprint-004 context quality proxy, and a SHA-256 deterministic output hash.

`generation_time_ms` is deliberately excluded from the stable hash because
process timing varies. All other metrics, scenario identity, selected entity
and relationship IDs, warnings, and limitations are hashed as canonical JSON.

## Interpretation and limitations

These metrics are automated proxies over a synthetic fixture. Generation
latency is not human Context Recovery Time. The benchmark does not establish
scientific validity, statistical significance, faster human recovery, or
improved productivity. The human evaluation protocol in the Sprint-005 package
is future work and was not executed in this sprint.

