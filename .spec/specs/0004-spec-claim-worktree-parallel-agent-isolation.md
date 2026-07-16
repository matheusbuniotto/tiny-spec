---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T11:16:51.354060'
gate: ''
gate_notes: 'TDD: 7 tests covering AC1-AC3 plus two regression tests from code review
  (failed worktree add reported honestly not as success; branch survives after manual
  worktree removal is reused not errored). New ''spec claim --worktree'' runs git
  worktree add into a sibling <repo>-spec-<id> dir on branch spec/<id>-<slug>, idempotent
  via git.py''s git_worktree_add/find_worktree_for_spec helpers. spec advance/close
  print a git worktree remove reminder on terminal transitions (no auto-delete), deduped
  into ui.py''s worktree_reminder_fields/print_worktree_reminder. Includes the spec''s
  required ''run your install step'' hint. Claiming without --worktree is byte-identical
  to before. 72/72 tests pass, no new mypy/ruff issues. Manually verified end-to-end
  in a scratch repo: create+idempotent-reuse+terminal-transition reminder all work.'
id: '0004'
parent: ''
pr: ''
status: at-gate
tags:
- claim
- worktree
template: feature
title: 'spec claim --worktree: parallel-agent isolation'
updated_at: '2026-07-15T20:24:29.429826'
---

## User Story

> As an **agent working alongside other agents**, I want **claiming a spec to give me an isolated worktree**, so that **parallel sessions never touch each other's files**.

## Problem Statement

> Hard isolation beats coordination for parallel agent work, but tiny-spec's `claim` command only sets an assignee today — two agents claiming different specs still share one working directory and can clobber each other's edits.

## Proposed Solution

`spec claim <id> --agent <name> --worktree` additionally runs `git worktree add ../<repo>-spec-<id> -b spec/<id>-<slug>`, prints the path (and includes it in `--json` as `worktree`/`branch`), and is idempotent if the worktree/branch already exists. `spec advance`/`spec close` to a terminal state prints a reminder of the worktree path and the `git worktree remove` command — no auto-delete.

## Acceptance Criteria

- [ ] **AC1**: `spec claim 0001 --agent bot --worktree` creates the directory and branch, and prints/returns the path
- [ ] **AC2**: claiming the same spec with `--worktree` again reuses the existing worktree/branch instead of erroring
- [ ] **AC3**: claiming without `--worktree` behaves exactly as it does today (no behavior change)

## Technical Notes

No auto-cleanup, no per-worktree env/db/port management — document "run your install step" in the hint instead of automating it.

### Dependencies / Blockers

None.

### Out of Scope

Auto-cleanup on close, dependency install inside the worktree, per-worktree environment management.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: in a scratch git repo, claim a spec with `--worktree`, `cd` into the printed path, confirm it's on the right branch and has the spec files
- [ ] **Test the failure case**: claim the same spec with `--worktree` twice, confirm the second call reuses rather than errors
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?