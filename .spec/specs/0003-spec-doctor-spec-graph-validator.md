---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T11:16:51.198743'
gate: ''
gate_notes: 'TDD: 10 new tests covering AC1-AC3 plus the remaining check types from
  Technical Notes (tests/test_doctor.py). New ''spec doctor [--json]'' command checks
  dangling blocked_by/parent refs, duplicate spec IDs, unassigned in-progress specs,
  stale claims (reuse STALE_DAYS pattern), maps with all children done but still open,
  at-gate specs missing a Human Gate Checklist (reuses gate_check''s extractor), and
  circular blocked_by chains via DFS cycle detection. Exits 1 with findings, 0 clean.
  65/65 tests pass, no new mypy/ruff issues. Manually verified: clean project prints
  ''no issues'' exit 0, seeded dangling blocked_by is caught with spec ID + fix hint
  on both human and --json output.'
id: '0003'
parent: ''
pr: https://github.com/matheusbuniotto/tiny-spec/pull/11
status: implemented
tags:
- validation
- ci
template: feature
title: 'spec doctor: spec-graph validator'
updated_at: '2026-07-15T18:16:00.750521'
---

## User Story

> As an **agent or CI pipeline**, I want **a deterministic command that validates the spec graph**, so that **I can catch broken references and stale state without a human reading every file**.

## Problem Statement

> tiny-spec has no linter for the artifact it owns. Dangling `blocked_by`/`parent` references, stale claims, and maps whose children are all done but the map is still open currently go unnoticed until someone reads `spec list` closely.

## Proposed Solution

New command `spec doctor [--json]` checks: dangling `blocked_by`/`parent` refs, duplicate spec IDs, `in-progress` specs with no assignee, stale claims (reuse `STALE_DAYS`), maps with all children implemented/closed but still open, at-gate specs missing a Human Gate Checklist section, and circular `blocked_by` chains. Exit 0 when clean, 1 when findings — drops straight into CI.

## Acceptance Criteria

- [ ] **AC1**: clean project → `spec doctor` prints "no issues", exits 0
- [ ] **AC2**: a spec with a dangling `blocked_by` ID is flagged with the spec ID and a fix hint
- [ ] **AC3**: `spec doctor --json` returns `{"count": N, "findings": [...], "help": [...]}`

## Technical Notes

No AI involved — pure deterministic checks over `list_specs()`. Reuses `open_blockers`/`children_of` from storage.py.

### Dependencies / Blockers

None.

### Out of Scope

Auto-fixing (`--fix`) and action-classified findings (agent-verifiable vs human-only) — tracked in backlog.md, revisit after this proves out.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: seed a project with one dangling `blocked_by` ref, run `spec doctor`, confirm it's caught
- [ ] **Test the failure case**: run `spec doctor` on a clean project, confirm exit 0 and no false positives
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?