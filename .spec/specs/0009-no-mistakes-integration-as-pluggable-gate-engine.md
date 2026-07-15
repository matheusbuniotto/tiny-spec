---
assignee: ''
author: Matheus Buniotto
blocked_by:
- 0008
created_at: '2026-07-15T14:59:46.329616'
gate_notes: ''
id: 0009
parent: ''
status: draft
tags:
- gate
- no-mistakes
- integration
template: feature
title: no-mistakes integration as pluggable gate engine
updated_at: '2026-07-15T14:59:46.329757'
---

## User Story

> As a **spec author whose project has `no-mistakes` installed**, I want **tiny-spec to delegate checks/review/CI to it under `draft`/`pr` gate mode**, so that **I get no-mistakes' review-with-findings and PR/CI monitoring instead of tiny-spec reimplementing that machinery**.

## Problem Statement

> `no-mistakes` (a separate, already-installed CLI: `~/.claude/skills/no-mistakes/SKILL.md`) already runs a full pipeline — intent capture, AI review with `auto-fix`/`no-op`/`ask-user`-classified findings, test, lint, docs, push, PR, and background PR/CI monitoring through merge. tiny-spec's own `spec review` (advisory-only) and `checks:` runner cover only a slice of this. Reimplementing a "thin no-mistakes" inside tiny-spec would duplicate a tool that already does this well and grow tiny-spec's surface area, contradicting its thin-by-design goal.

## Proposed Solution

Detect the `no-mistakes` binary (e.g. `shutil.which("no-mistakes")`). When present *and* the spec's effective gate mode (spec 0008) is `draft` or `pr`, tiny-spec's flow hands the review+test+lint+CI stage to `no-mistakes axi run --intent "..."` instead of running its own advisory `spec review` — `ask-user` findings from no-mistakes surface to the human exactly as no-mistakes already presents them. When no-mistakes is absent, or gate mode is `local`, tiny-spec's existing `spec review` stays the fallback — unchanged. Regardless of no-mistakes' presence, tiny-spec's own `checks:` (spec verify) still runs first as a fast local pre-flight at `in-progress → at-gate` — no-mistakes re-running the same suite later is acceptable, cheap redundancy that catches obvious breakage before the heavier round-trip.

## Acceptance Criteria

- [ ] **AC1**: On a machine without the `no-mistakes` binary, all gate modes behave exactly as spec 0008 defines them — `spec review` is the only review path, no error or degraded behavior from the missing binary.
- [ ] **AC2**: On a machine with `no-mistakes` installed and gate mode `pr` (or `draft`), a documented command (e.g. `spec advance <id> --run-no-mistakes` or equivalent) shells out to `no-mistakes axi run --intent "<derived intent>"` and surfaces its `gate:`/`outcome:` back through tiny-spec's own output.
- [ ] **AC3**: With `no-mistakes` installed, `in-progress → at-gate` still runs tiny-spec's own `checks:` first; a failing local check blocks at-gate before no-mistakes is ever invoked.
- [ ] **AC4**: `spec doctor` (or `spec config`) reports whether `no-mistakes` was detected, so `gate: pr` projects can tell at a glance whether the integration path is even available.

## Technical Notes

New thin wrapper module (e.g. `integrations/no_mistakes.py`) mirroring `integrations/git.py`'s shape: binary detection, a function that shells `no-mistakes axi run`/`axi respond` and parses TOON output just enough to extract `gate:`/`outcome:`/`findings`. No vendoring or reimplementing no-mistakes' pipeline logic — tiny-spec only drives the CLI and relays its output. Reuses spec 0008's `gate:` config field to decide when this path is even considered.

### Dependencies / Blockers

Depends on spec 0008 (`gate:` config/frontmatter must exist first).

### Out of Scope

No GitHub Action/webhook automation (trigger stays human-signaled per spec 0008). No attempt to replace or vendor no-mistakes' own review/test/lint logic. No verification that a `pr`-mode merge was actually done by a non-author.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: on a machine with no-mistakes installed, gate: pr, run the integration command and confirm no-mistakes' `gate:`/`outcome:` shows up through tiny-spec's own output
- [ ] **Test the failure case**: on a machine without no-mistakes, confirm `spec review` and `checks:` still work with no error mentioning the missing binary
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?