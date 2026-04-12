## Status

> **[Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]**

| Field | Value |
|-------|-------|
| Owner | [Name or team] |
| Proposed | [Date] |
| Accepted | [Date or "pending"] |
| Review date | [When to revisit — e.g. "Q3 2026 or after 10k users"] |

## Context

> What is the situation that makes this decision necessary?
> Describe the forces at play: technical constraints, business requirements, team size, timeline.
> Write it as if explaining to someone who just joined the project.
> Bad: "We need a database." Good: "We need durable, queryable storage for ~50 write/s with complex join queries. The team has strong Postgres experience and the data is relational."

## Decision Drivers

> What criteria matter most for this decision? List them explicitly — they make the tradeoff visible.

- **[Driver 1]**: e.g. Operational simplicity — we have no dedicated DBA
- **[Driver 2]**: e.g. Cost at scale — must stay under $X/month at 1M users
- **[Driver 3]**: e.g. Team familiarity — we cannot afford a long learning curve right now

## Decision

> The specific choice being made, stated plainly.
> Example: "We will use PostgreSQL with SQLAlchemy ORM, hosted on RDS, with a single replica for read scaling."

## Alternatives Considered

> Each alternative must get an honest evaluation — not a strawman. Include why it was rejected in terms of the Decision Drivers above.

### Option A: [Name]
- **Pro**: ...
- **Pro**: ...
- **Con**: ...
- **Rejected because**: [reference a specific driver]

### Option B: [Name]
- **Pro**: ...
- **Con**: ...
- **Rejected because**: [reference a specific driver]

## Consequences

### Positive
- [Specific benefit — measurable where possible]

### Negative
- [Specific downside or risk — be honest]

### Risks & Mitigations
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| [Risk] | Low/Med/High | [What we'll do if it materializes] |

## Implementation Notes

> What needs to happen for this decision to be enacted?
> This is not a full implementation plan — it's the minimum a responsible engineer needs to know.

- [ ] [Action item or dependency]
- [ ] [Migration or rollout consideration]
- [ ] [What to monitor / alert on after rollout]

## Human Gate Checklist

> Before accepting this ADR, verify each item.

- [ ] **Context is accurate**: does the context section reflect the real situation today, not a hypothetical?
- [ ] **Drivers are explicit**: are the decision criteria listed — not implied?
- [ ] **Alternatives are fair**: does each rejected option get a specific reason tied to a driver?
- [ ] **Negatives are honest**: are the downsides listed without sugarcoating?
- [ ] **Owner is accountable**: is there a named person or team who owns the outcome?
- [ ] **Review date is set**: is there a trigger condition or date to revisit this decision?
