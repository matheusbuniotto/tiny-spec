---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T11:16:51.045572'
gate: ''
gate_notes: 'Renamed run-kata to verify (hidden alias kept), katas: to checks: in
  config.yaml (legacy key still read), --skip-kata to --skip-checks (hidden alias
  kept). Swept all user-facing strings/JSON keys (kata_failed->checks_failed error
  code, katas->checks JSON field) in kata.py, lifecycle.py, config_cmd.py, export.py,
  setup_checks.py, init.py, greenfield.py scaffolds, skill.md/SKILL.md, claude_md.py,
  agents.py, data-pipeline.md template. Kept internal Python names (Kata class, kata.py,
  cfg.katas attribute) unchanged per the spec''s own scope decision. grep -ri kata
  README.md skill.md src/spec_cli/SKILL.md returns nothing. 20/20 tests pass, manually
  verified spec verify/run-kata/--help in a scratch project.'
id: '0002'
parent: ''
pr: '6'
status: implemented
tags:
- ergonomics
- naming
template: feature
title: Rename kata to checks, run-kata to spec verify
updated_at: '2026-07-15T15:18:06.226349'
---

## User Story

> As a **user reading `--help` for the first time**, I want **`kata` to say what it does**, so that **I don't have to learn tiny-spec's private vocabulary before using it**.

## Problem Statement

> "Kata" is the one piece of CLI vocabulary that doesn't explain itself — everything else (`gate`, `claim`, `advance`) reads as English. It also collides with the planned `spec doctor` validator naming.

## Proposed Solution

`spec run-kata` becomes `spec verify` (hidden `run-kata` alias for one release). Config key `katas:` becomes `checks:` (old key still read, never written back as `katas:`). `--skip-kata` becomes `--skip-checks` (hidden alias). Do this before any other spec touches docs, so everything after uses final vocabulary.

## Acceptance Criteria

- [ ] **AC1**: `spec verify` runs the configured checks; `spec run-kata` still works but is hidden from `--help`
- [ ] **AC2**: A project with legacy `katas:` in config.yaml works unmodified
- [ ] **AC3**: `grep -ri kata README.md skill.md src/spec_cli/SKILL.md` returns nothing

## Technical Notes

Rename internals (`Kata` model, `kata.py`) only where cheap; the user-facing surface is the priority.

### Dependencies / Blockers

None — do first so specs 0003+ document the final command names.

### Out of Scope

`spec doctor` (separate spec) — different command, different concern.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: run `spec verify` on a project with checks configured, confirm it runs them; run `spec run-kata` and confirm it still works silently
- [ ] **Test the failure case**: a project with an old `katas:` config.yaml still loads and runs correctly
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?