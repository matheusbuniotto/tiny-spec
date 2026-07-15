---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T11:16:51.648515'
gate_notes: ''
id: '0006'
parent: ''
status: draft
tags:
- ci
- repo
template: feature
title: 'Repo hygiene: CI, ruff config, own AGENTS.md'
updated_at: '2026-07-15T11:16:51.648675'
---

## User Story

> As a **maintainer merging PRs into tiny-spec itself**, I want **CI to catch broken tests and lint issues before merge**, so that **agent-written code passes the same bar as human-written code**.

## Problem Statement

> tiny-spec has no CI. PRs #1–#4 all merged with zero automated verification. `[tool.ruff]` only sets `line-length`; mypy is declared as a dev dependency but has never been run.

## Proposed Solution

Add `.github/workflows/ci.yml`: on PR + push to main, `uv sync`, `ruff check`, `ruff format --check`, `pytest`. Add a real ruff rule selection (`E`, `F`, `I`, `UP`, `B`) and fix whatever it flags. Add tiny-spec's own `AGENTS.md` documenting build/test commands and the skill.md ↔ SKILL.md sync rule.

## Acceptance Criteria

- [ ] **AC1**: CI is green on a no-op PR
- [ ] **AC2**: CI fails red when a test is deliberately broken (verify once, then revert)
- [ ] **AC3**: `ruff check` and `ruff format --check` pass locally with the new rule selection

## Technical Notes

One job, Python 3.11 (matches `requires-python`). mypy enablement is explicitly out of scope — it's never been run and cleaning that up is its own PR.

### Dependencies / Blockers

None.

### Out of Scope

mypy in CI, pre-commit hooks, coverage gates, release automation.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: open a throwaway PR with a trivial change, confirm the CI workflow runs and passes
- [ ] **Test the failure case**: temporarily break a test, push, confirm CI goes red, then revert
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?
