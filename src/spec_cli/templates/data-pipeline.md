## Purpose

> What does this pipeline do, what business question does it answer, and who consumes the output?
> Example: "Computes daily active users per product segment, consumed by the growth dashboard and weekly exec report."

## Source & Sink

| | Details |
|---|---|
| **Source** | [system name, table/topic, owner] |
| **Source schema** | [key fields — use code block below for full schema] |
| **Sink** | [system name, table/dataset, owner] |
| **Output schema** | [key fields] |
| **Trigger** | [schedule: `0 6 * * *` / event-driven / on-demand] |
| **Latency SLA** | [e.g. "must complete by 07:00 UTC"] |

```python
# Source schema
{
    "field": "type",  # description
}

# Output schema
{
    "field": "type",  # description
}
```

## Transformation Logic

> Step-by-step description of the transformation. Clear enough that an engineer can implement without guessing.
> Call out: joins, aggregations, window functions, deduplication logic, and any business rules embedded in the transform.

### Business rules

> Rules that are NOT obvious from the code. Example: "Users with `is_internal=True` are excluded from all metrics."

### Edge cases

> What happens when: source is empty / late / has duplicates / schema changes?

## Data Quality Checks

> These become kata entries. Each check must be automatable.

- [ ] **Row count**: output has at least N rows (or delta from yesterday is within ±X%)
- [ ] **Null check**: `[key field]` has 0 nulls
- [ ] **Freshness**: `updated_at` max is within the last [N hours]
- [ ] **Schema**: output columns match expected schema exactly
- [ ] **Business invariant**: [e.g. "sum of segment users equals total users"]

## Backfill Strategy

> How do we reprocess historical data?
> - Can the pipeline be run idempotently for a past date range?
> - What's the command? `spark-submit ... --date 2024-01-01 --end 2024-01-31`
> - Are there dependencies that must be backfilled first?

## Failure & Recovery

| Failure mode | Expected behavior | Recovery action |
|---|---|---|
| Source unavailable | [fail fast / retry N times / skip] | [alert + manual rerun] |
| Partial source data | [detect and fail / proceed with warning] | [page on-call] |
| Schema mismatch | [fail pipeline / coerce / drop column] | [schema registry update] |
| Output write failure | [retry / dead-letter queue] | [manual replay] |

## Monitoring & Alerting

> What metrics and alerts exist for this pipeline?

- **Success alert**: notify `[channel]` on completion with row count
- **Failure alert**: page `[channel]` if pipeline fails or SLA is missed
- **Data quality alert**: notify if any quality check above fails
- **Dashboard**: [link to monitoring dashboard if any]

## Dependencies & Blockers

> What must exist / run before this pipeline?

## Out of Scope

> What this pipeline explicitly does NOT do.

## Human Gate Checklist

> Before passing the gate, the human verifies each item.

- [ ] **Run end-to-end on staging**: `[pipeline run command]` — completes without errors?
- [ ] **Verify row count**: output has expected number of rows (check against source)?
- [ ] **Spot-check sample rows**: pull 10 rows — do values look correct for known entities?
- [ ] **Run data quality checks**: `[dq check command]` — all pass?
- [ ] **Test failure mode**: cut source access and verify pipeline fails gracefully with a clear error?
- [ ] **Read the diff**: `git diff main` — no hardcoded dates, credentials, or dev-only overrides?
