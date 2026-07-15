---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T14:59:46.613465'
gate_notes: ''
id: '0011'
parent: ''
status: draft
tags:
- templates
- tdd
- review
template: feature
title: 'Tracer-bullet AC: ordered vertical slices in feature/api templates'
updated_at: '2026-07-15T14:59:46.613572'
---

## User Story

> As an **implementer (human or AI agent) picking up a feature/api spec**, I want **its Acceptance Criteria to already be ordered as a tracer-bullet sequence**, so that **I implement it as thin vertical slices instead of guessing how to decompose a flat requirements list**.

## Problem Statement

> tiny-spec's global `/tdd` skill already teaches tracer-bullet TDD (one test → RED → minimal fix → GREEN → repeat, never all tests up front), but nothing in tiny-spec *itself* reinforces this at the point where it matters most — spec authoring. Today's `feature`/`api` templates present AC as a flat, unordered checklist (see spec 0002's own AC1–AC3), which invites horizontal-slice implementation (build everything, then test everything) even when an agent knows the tracer-bullet discipline in the abstract.

## Proposed Solution

Reshape the `feature` and `api` templates' Acceptance Criteria section so AC are explicitly an ordered sequence: AC1 must describe the thinnest possible end-to-end path (something demonstrably working, even if minimal), and each subsequent AC adds exactly one increment on top of the previous one — never an unrelated requirement bolted on. Update the template's own guidance text to state this ordering rule (replacing the current generic "each criterion must be independently testable" note). `spec review` gains one more judgment: does AC1 read as a thin end-to-end slice, and does each later AC read as a single increment rather than a grab-bag requirement — flagged as a `NEEDS WORK` finding when it doesn't, same advisory severity as today's other review checks. `bug`/`adr`/`data-pipeline`/`experiment` templates are untouched — a bug fix is usually one slice by nature, and data-pipeline/experiment already have their own structured DQ/Human-Gate sections that don't map onto "increments."

## Acceptance Criteria

- [ ] **AC1**: `spec new "<title>" --template feature` (no --ai) produces a spec whose AC section template text explicitly instructs "AC1 = thinnest end-to-end slice, AC2+ = one increment each" — visible in the raw scaffolded file.
- [ ] **AC2**: The same instruction appears in the `api` template; `bug`, `adr`, `data-pipeline`, `experiment` templates are unchanged (verify via diff against their current content).
- [ ] **AC3**: `spec review <id>` on a feature/api spec whose AC list is an unordered flat bag (e.g. AC1 is unrelated to AC2, or AC1 isn't independently runnable end-to-end) returns a `NEEDS WORK` finding calling out the ordering, not just today's existing checks.
- [ ] **AC4**: `spec review <id>` on a feature/api spec whose AC is already a proper ordered sequence (e.g. rewrite spec 0002's AC as a positive test case) does not raise this new finding.

## Technical Notes

Changes are confined to `templates/feature.md`, `templates/api.md` (or wherever their template strings live, likely alongside `templates/data-pipeline.md`), and the AI review prompt used by `spec review` (wherever that prompt template lives — same place spec 0002's rename touched for review-adjacent strings, if any). No schema/data-model change — AC stays a plain markdown checklist, just with different guidance text and one more advisory review dimension.

### Dependencies / Blockers

None — independent of specs 0008/0009/0010.

### Out of Scope

No gate-level enforcement (no blocking `in-progress → at-gate` on AC ordering) — purely template guidance plus advisory review, per the earlier discussion ruling out commit-granularity policing as too fuzzy to enforce deterministically.

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: `spec new "test" --template feature`, read the scaffolded AC section, confirm the ordering instruction is present and clear
- [ ] **Test the failure case**: `spec review` against a spec with deliberately flat/unordered AC — confirm the new NEEDS WORK finding actually fires
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?