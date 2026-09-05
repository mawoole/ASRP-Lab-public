# Context Recovery Benchmark Report

## Benchmark

- Benchmark ID: `sprint-005-context-recovery`
- ASRP-SciOS runtime version: `0.4.0`
- Evaluation type: automated synthetic proxy benchmark
- Human evaluation executed: no

## Fixture Summary

- Source entities: 18
- Source relationships: 22
- Scenarios executed: 3

## Metrics

| Scenario | generation_time_ms | Entities | Relationships | Reduction | Seed | Relationship | Decision | Evidence | Unknown | Quality proxy | Stable hash |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Hypothesis Review Recovery | 1.147200 | 10 | 12 | 0.444444 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | `50cc098995a2230d48e958ccb21941617b431bedcb3bbe48e7becb9ca577eb59` |
| Decision Trace Recovery | 0.694500 | 8 | 10 | 0.555556 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | `59aaf6b4d41a3023f854c9081add72a6dea8998d430b2200b45ff826cb419b73` |
| Evidence Audit Recovery | 2.788500 | 8 | 10 | 0.555556 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | `87a1dc6ee8a98b1a39802ecd12b44134cedb4f3fae0e333d3999ff8599458922` |

## Selected Context

### Hypothesis Review Recovery

Selected entity IDs:

- `hypothesis.recovery-a`
- `decision.recovery-a`
- `evidence.contradict-a`
- `evidence.support-a`
- `unknown.recovery-a`
- `hypothesis.recovery-b`
- `question.recovery-a`
- `knowledge.recovery-a`
- `campaign.synthetic-context`
- `context.synthetic-prior`

Selected relationships: 12

Warnings: None

### Decision Trace Recovery

Selected entity IDs:

- `decision.recovery-a`
- `evidence.contradict-a`
- `evidence.support-a`
- `unknown.recovery-a`
- `hypothesis.recovery-a`
- `question.recovery-a`
- `knowledge.recovery-a`
- `context.synthetic-prior`

Selected relationships: 10

Warnings: None

### Evidence Audit Recovery

Selected entity IDs:

- `evidence.support-a`
- `decision.recovery-a`
- `evidence.contradict-a`
- `unknown.recovery-a`
- `hypothesis.recovery-a`
- `question.recovery-a`
- `knowledge.recovery-a`
- `context.synthetic-prior`

Selected relationships: 10

Warnings: None

## Interpretation

These results show deterministic, bounded graph selection on the controlled synthetic fixture. Coverage and compactness are proxy measurements of the generated ContextSnapshot; they do not establish faster human recovery or improved scientific productivity.

The stable hash excludes `generation_time_ms`, because process timing is inherently variable. It includes scenario identity, all other metrics, selected entity and relationship identities, warnings, and limitations.

## Limitations

- Synthetic fixture only; external validity has not been assessed.
- Automated proxy metrics only; the documented human protocol was not executed.
- Timing is local generation latency, not human Context Recovery Time.
- No statistical significance or human productivity claim is made.
- Coverage reflects the fixture and Sprint-004 selection policy, not scientific correctness.

## Next Step

Run the documented controlled human evaluation in a future validation sprint with approved participants, tasks, scoring, and analysis.
