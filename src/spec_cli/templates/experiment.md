## Hypothesis

> State the hypothesis in this exact form:
> "We believe that **[change]** will cause **[outcome]** for **[audience]**,
> measured by **[metric]** changing by **[threshold]** within **[timeframe]**."

## Problem & Motivation

> What behaviour or metric are we trying to improve? What's the current baseline?
> Include numbers: "Current 7-day retention is 34%. Industry benchmark is 42%."

## Experiment Design

| | Details |
|---|---|
| **Type** | [A/B / multivariate / holdout / shadow] |
| **Unit of randomisation** | [user_id / session_id / org_id] |
| **Traffic split** | [50/50 / 90 control / 10 treatment / ...] |
| **Target audience** | [all users / new users / paid tier / specific segment] |
| **Exclusions** | [internal users / QA accounts / users in other active experiments] |
| **Planned duration** | [N days — minimum for statistical significance] |
| **Min sample size** | [N users per arm — calculated from MDE below] |

## Metrics

### Primary metric
> The single metric that determines success or failure. One only.

- **Metric**: [name]
- **Definition**: [exact SQL or computation — no ambiguity]
- **Minimum detectable effect (MDE)**: [e.g. +5% relative]
- **Statistical significance**: [α = 0.05, power = 0.80]
- **Current baseline**: [value ± std dev]

### Guardrail metrics
> Metrics that must NOT regress. Experiment fails if any guardrail is violated.

- [ ] **[metric]**: must not decrease by more than [X%]
- [ ] **[metric]**: must not increase by more than [X%]

### Secondary / observational metrics
> Metrics we track but don't use to make the go/no-go decision.

- [metric]: [what we expect to see and why]

## Implementation

> What changes in the product/system between control and treatment?
> Be specific enough that an engineer can implement without a follow-up meeting.

### Feature flag / experiment config

```python
# Example
EXPERIMENT_KEY = "exp_2024_q1_feature_name"
VARIANTS = {"control": 0.5, "treatment": 0.5}
```

### Rollout plan

> How do we ramp? Day 1: 5% → Day 3: 20% → Day 7: 50% → ...

## Decision Criteria

> The decision rule must be unambiguous — no post-hoc interpretation.

| Outcome | Condition | Decision |
|---|---|---|
| **Ship** | Primary metric improves by ≥ MDE, p < 0.05, no guardrail regressions | Roll out to 100% |
| **Iterate** | Directional improvement but below MDE, or p > 0.05 | Extend by N days or redesign |
| **Kill** | Primary metric flat/negative OR any guardrail regresses | Revert treatment, document learnings |

> Who makes the final call? [Name / team]
> Deadline for decision: [date]

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| [Risk] | Low/Med/High | [what we do] |
| Novelty effect | Medium | Run for at least 2 weeks |
| Instrumentation error | Medium | Validate event logs on day 1 |

## Out of Scope

> What this experiment does NOT test or measure.

## Human Gate Checklist

> Before advancing to at-gate, the human verifies each item.

- [ ] **Instrumentation live**: events firing correctly in staging? `[validation query or command]`
- [ ] **Randomisation verified**: treatment and control groups have similar baseline metrics (SRM check)?
- [ ] **Sample size calculator run**: `[link or command]` — planned duration is sufficient for MDE?
- [ ] **Guardrail alerts configured**: alerts set up for all guardrail metrics?
- [ ] **Rollback plan ready**: feature flag can disable treatment within 5 minutes?
- [ ] **Decision criteria documented**: everyone on the team agrees on the go/no-go rule above?
