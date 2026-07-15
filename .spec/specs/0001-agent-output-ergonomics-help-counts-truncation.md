---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T11:16:50.870169'
gate: ''
gate_notes: 'TDD: 13 new tests covering AC1-AC4 (tests/test_agent_output_ergonomics.py).
  54/54 tests pass, no new mypy/ruff issues (verified pre-existing ones untouched).
  Manually verified spec next/show/list --json help[], list empty envelope + human
  filter naming, show 9999 not-found help, and export/list --full truncation. SKILL.md
  + skill.md kept in sync. De-duplicated the 10 identical not_found error call sites
  into ui.not_found() while touching them for help[].


  ---

  Merged via PR#10, including the code-review fix commit (892f56c) for the AT_GATE
  help[] bug. Verified locally on main: 55/55 tests pass, no new lint/type issues.
  Manual usage test re-confirmed post-merge: help[] is a single runnable command at
  every lifecycle stage.'
id: '0001'
parent: ''
pr: ''
status: implemented
tags:
- ergonomics
- json
template: feature
title: 'Agent output ergonomics: help[], counts, truncation'
updated_at: '2026-07-15T17:35:18.342774'
---

## User Story

> As an **agent driving the CLI**, I want **every output to tell me what to do next**, so that **I don't have to re-consult skill.md between every command**.

## Problem Statement

> AXI-benchmark evidence (915 runs) shows next-command hints are the single biggest turn-count reducer for agents driving a CLI. tiny-spec's `--json` output today gives raw state but no guidance, and empty/error states are inconsistent (`spec list --json` on no matches returns a bare `[]`, not a count or explanation).

## Proposed Solution

Every `--json` output gains a `"help": [...]` array of concrete next-command templates for the current state (e.g. `spec show` on a claimable spec suggests `spec advance 0001 --yes --json`). JSON errors get the same field with the exact recovery command. `spec list --json` wraps results in `{"count": N, "specs": [...]}`. Empty states are definitive and name the active filter. Long bodies get a truncation hint pointing at `--full`.

## Acceptance Criteria

- [x] **AC1**: `spec next --json`, `show`, `list`, `advance`, `claim` all emit a `help` array with at least one concrete command
- [x] **AC2**: `spec show 9999 --json` (not found) includes a `help` entry with a recovery command
- [x] **AC3**: `spec list --status at-gate --json` on an empty result returns `{"count": 0, "specs": []}` and human output names the filter ("0 specs match --status at-gate")
- [x] **AC4**: `spec export --full` / long bodies show `"(truncated, N chars — use spec show <id> --json)"` when truncated

## Technical Notes

One shared `help()` helper in `ui.py` that commands call with a list of suggestion strings; keep the schema additive (only new fields, nothing renamed or removed) so existing JSON consumers don't break.

### Dependencies / Blockers

None — builds on existing command surface.

### Out of Scope

TOON output format (see backlog.md). Minimal-schema trimming of existing JSON fields — that's a breaking change, tracked separately in backlog.md.

## Definition of Done

- [x] All acceptance criteria above are met
- [x] Tests written and passing (`uv run pytest tests/ -q`)
- [x] No regressions in related flows
- [x] Code reviewed or self-reviewed against project conventions
- [x] SKILL.md / skill.md document `help[]` and the `list` envelope (kept in sync)

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: run `spec next --json`, `spec show <id> --json`, `spec list --json` on a project with a few specs — confirm `help[]`/`count` appear and are sensible
- [ ] **Test the failure case**: `spec show 9999 --json` — confirm structured error with `help`
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?