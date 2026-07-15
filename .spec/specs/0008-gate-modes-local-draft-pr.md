---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T14:59:46.170962'
gate: ''
gate_notes: ''
id: 0008
parent: ''
pr: ''
status: approved
tags:
- gate
- pr-review
template: feature
title: 'Gate modes: local, draft, pr'
updated_at: '2026-07-15T15:10:24.651917'
---

## User Story

> As a **spec author driving a change through tiny-spec**, I want **the human-gate step to match how I'm actually shipping the work (no PR, a self-mergeable draft PR, or a fully-reviewed PR)**, so that **`at-gate → implemented` isn't a redundant manual step on top of verification that already happened elsewhere**.

## Problem Statement

> Today `at-gate → implemented` always means the same thing: a human runs `spec advance <id> --note "..."` after manually walking the Human Gate Checklist. In practice, most real usage (this whole project included) routes changes through a GitHub PR — the PR review/merge already *is* the human verification, but tiny-spec has no way to record that or lean on it. Specs end up sitting at `at-gate` in the tool long after their PR has merged (spec 0002 is a live example: PR #6 merged, spec still at-gate).

## Proposed Solution

Add a `gate:` setting (`local | draft | pr`) to `config.yaml`, default `local` — matches today's behavior exactly, zero breaking change for existing projects. `local` = today's flow unchanged (manual `--note`, full checklist). `draft` = a PR is expected but the author can self-merge once checks are green — it's an audit trail, not a review request. `pr` = a non-draft PR is expected and the gate isn't satisfied until someone other than the author merges it. A spec's own frontmatter can override the project default. `spec advance` gains a `--pr <url|number>` flag that records the PR reference distinctly from a freeform `--note`; supplying `--pr` under `draft`/`pr` mode is a rubber-stamp (no full checklist walk required — the PR already served that role).

## Acceptance Criteria

- [ ] **AC1**: A project with no `gate:` key in config.yaml behaves exactly as today — `spec advance <id> --note "..."` works, requires no `--pr`, and `spec show`/`gate-check` display nothing new.
- [ ] **AC2**: `gate: pr` (or `draft`) set in config.yaml, or overridden per-spec in frontmatter, is surfaced by `spec show <id>` and `spec gate-check <id>` (e.g. "Gate mode: pr — needs a non-author merge").
- [ ] **AC3**: `spec advance <id> --pr 123 --yes` succeeds without requiring `--note`; the resulting `.spec/log.md` entry and spec frontmatter record `pr: 123` distinctly from a freeform note.
- [ ] **AC4**: Under `gate: pr` (or `draft`) mode, `spec advance <id> --yes` with neither `--pr` nor `--note` is rejected with a clear error naming both options.

## Technical Notes

New `gate` field in `Config` (`config.py`), read with the same known-fields pattern as `checks`. Spec frontmatter gets an optional `gate` override. `advance` (`main.py`) gains a `--pr` typer.Option threaded into `lifecycle.py`'s `_do_transition` alongside `note`. No verification that the merge was actually done by a non-author for `pr` mode — that's a documented human/process expectation, not enforced code, in this first pass (see spec 0009 for where automated verification could later plug in).

### Dependencies / Blockers

None — this is the base spec. Spec 0009 (no-mistakes integration) depends on the `gate:` concept existing here.

### Out of Scope

No GitHub API calls, no automatic detection of PR merges (trigger stays human-signaled), no `spec pr-body` generation (spec 0010), no no-mistakes shelling (spec 0009).

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: set `gate: pr` in a scratch project's config.yaml, run `spec advance <id> --pr 42 --yes`, confirm no `--note` was required and the log records `pr: 42`
- [ ] **Test the failure case**: same `gate: pr` project, run `spec advance <id> --yes` with neither `--pr` nor `--note` — confirm a clear rejection naming both flags
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?