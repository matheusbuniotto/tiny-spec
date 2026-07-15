---
assignee: ''
author: Matheus Buniotto
blocked_by:
- '0006'
created_at: '2026-07-15T11:16:51.798779'
gate_notes: ''
id: '0007'
parent: ''
status: draft
tags:
- testing
- ci
template: feature
title: CLI smoke tests + skill-drift test
updated_at: '2026-07-15T11:16:51.798885'
---

## User Story

> As a **maintainer relying on CI to catch regressions**, I want **the CLI's actual command surface exercised by tests**, so that **CI (spec 0006) is verifying real behavior, not just that the test files that exist happen to pass**.

## Problem Statement

> 23 commands, 2 test files before this backlog started, none exercising the CLI surface end-to-end. skill.md has drifted from the packaged `src/spec_cli/SKILL.md` copy twice already, silently, because nothing checks they match.

## Proposed Solution

Add `tests/test_cli.py` using Typer's `CliRunner` against a `tmp_path` git repo: golden path (`init` → `new` → `advance` ×4 with status assertions via `show --json`), `claim`/release flow, `doctor` clean + one seeded finding, and JSON shape assertions on `list`/`next`/`show`. Add `tests/test_skill_drift.py`: parse every `spec <subcommand>`/`--flag` mentioned in skill.md, assert each exists in the Typer app, and assert skill.md and `src/spec_cli/SKILL.md` are byte-identical.

## Acceptance Criteria

- [ ] **AC1**: the golden-path CLI test passes and would fail if a lifecycle transition broke
- [ ] **AC2**: deliberately editing only one of skill.md / SKILL.md fails the drift test
- [ ] **AC3**: the full suite runs in under 10 seconds with no network calls and no real AI calls

## Technical Notes

No coverage targets, no AI-drafting integration tests beyond the existing `test_glossary.py` mock pattern.

### Dependencies / Blockers

Depends on spec 0006 (CI) landing first so these tests run somewhere; easier to write after the `--json` non-interactive fix (already merged).

### Out of Scope

Coverage percentage targets, real AI provider calls in tests.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: run the new suite locally, confirm it passes; desync SKILL.md on purpose and confirm the drift test catches it
- [ ] **Test the failure case**: run the golden-path test against a deliberately broken lifecycle transition, confirm it fails
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?
