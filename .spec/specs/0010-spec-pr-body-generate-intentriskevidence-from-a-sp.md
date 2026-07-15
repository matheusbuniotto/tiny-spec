---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T14:59:46.469648'
gate: ''
gate_notes: ''
id: '0010'
parent: ''
pr: ''
status: in-progress
tags:
- gate
- pr-review
template: feature
title: 'spec pr-body: generate Intent/Risk/Evidence from a spec'
updated_at: '2026-07-15T15:19:11.910612'
---

## User Story

> As a **spec author about to open a PR**, I want **the PR body's Intent/Risk/Evidence generated from the spec I already wrote**, so that **I'm not hand-typing a summary of the same content that lives in `.spec/specs/`**.

## Problem Statement

> Every PR opened this session (#1–#6) had its body hand-written by whoever drove the session, re-deriving "what was this for" and "what did we verify" from memory each time — even though the spec already contains Purpose/AC and a verification story. `no-mistakes` (spec 0009) requires an `--intent` string as input to its review; today that also gets hand-typed per run instead of coming from the spec.

## Proposed Solution

New `spec pr-body <id>` command renders markdown with three sections: **Intent** (from the spec's User Story + Problem Statement + Proposed Solution), **Risk** (from Out of Scope / any Failure-mode-style content if present, otherwise a short prompt reminding the author to fill it in), and **Evidence** (the result of the most recent `spec verify <id>` run, plus which AC are checked off). Output is plain markdown, usable directly as `gh pr create --body-file` and as the `--intent` string for `no-mistakes axi run` when spec 0009 is available. Works standalone — no dependency on spec 0008 or 0009.

## Acceptance Criteria

- [ ] **AC1**: `spec pr-body 0002` (or any implemented/at-gate spec) prints markdown with `## Intent`, `## Risk`, `## Evidence` headings populated from that spec's actual content.
- [ ] **AC2**: The Evidence section reflects the real, current state of AC checkboxes and the last recorded `spec verify` result for that spec — not a static template.
- [ ] **AC3**: `spec pr-body <id> --json` emits the same three fields as structured JSON (`intent`, `risk`, `evidence`) for programmatic use (e.g. as `no-mistakes axi run --intent "$(spec pr-body <id> --json | jq -r .intent)"`).
- [ ] **AC4**: Running it on a spec with no Out of Scope section and no test runs yet still succeeds, with each section noting what's missing rather than crashing.

## Technical Notes

New command module (`commands/pr_body.py`) reusing the existing spec-parsing/export machinery (`commands/export.py` already assembles spec bodies for AI context — same parsing, different rendering). No new stored state; purely a view over existing spec + log data.

### Dependencies / Blockers

None.

### Out of Scope

No actual `gh pr create` invocation — this only renders the body text. No automatic risk inference beyond what the spec already states.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: `spec pr-body 0002` — read it, confirm Intent/Risk/Evidence actually reflect that spec's real content
- [ ] **Test the failure case**: run it against a bare-bones draft spec with no Out of Scope and no verify runs — confirm graceful "missing" notes, not a crash
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?