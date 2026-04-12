## User Story

> As a **[type of user]**, I want **[goal]** so that **[reason/value]**.

## Problem Statement

> What specific problem does this solve? Who is affected and how often?
> Bad: "Users can't find things." Good: "New users abandon onboarding at step 3 because the next action isn't obvious."

## Proposed Solution

> High-level approach in 2–4 sentences. What will exist after this is implemented that doesn't exist now?

## Acceptance Criteria

> Each criterion must be independently testable and binary (pass/fail).
> Bad: "The UI should be fast." Good: "Search results appear in < 300 ms for datasets up to 10 000 items."

- [ ] **AC1**: [Observable outcome — not an implementation detail]
- [ ] **AC2**: [Edge case or error path explicitly covered]
- [ ] **AC3**: [Performance, security, or accessibility requirement if applicable]

## Technical Notes

> Architecture decisions, chosen approach, and constraints.
> Call out: new dependencies, schema changes, breaking changes to existing interfaces, and anything that touches shared infrastructure.

### Dependencies / Blockers

> List specs or external things this depends on. Leave blank if none.

### Out of Scope

> What are we explicitly NOT doing in this spec? This prevents scope creep.
> Example: "Pagination is out of scope — we'll add it in spec 0007."

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`<test command>`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.
> Every item must be completable in under 5 minutes. Replace placeholders with real commands.

- [ ] **Run the tests**: `<test command>` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: [describe exact steps — what to click/call/send and what to expect]
- [ ] **Test the failure case**: [describe one edge case or error path — what input, what expected response]
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?
