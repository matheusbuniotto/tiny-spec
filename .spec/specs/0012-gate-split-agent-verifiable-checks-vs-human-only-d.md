---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-17T01:23:14.355107'
gate: ''
gate_notes: ''
id: '0012'
parent: ''
pr: ''
status: draft
tags:
- gate
- agents
- no-mistakes
template: feature
title: 'Gate split: agent-verifiable checks vs human-only decisions'
updated_at: '2026-07-17T01:23:14.355232'
---

## User Story

> As a **human passing the gate on agent-delivered work**, I want **the Human Gate Checklist split into agent-verifiable items (CI, tests, intent-vs-done validation) and human-only items (decisions, product judgment)**, so that **agents pre-verify everything mechanical before parking at the gate and I only spend attention on what genuinely needs a human**.

## Problem Statement

> Today every Human Gate Checklist item lands on the human, including purely mechanical ones ("run the tests", "check the diff for debug code") that an agent can — and per no-mistakes' model, should — verify itself before handing off. The human's scarce attention gets diluted across items an agent already proved, and the genuinely human calls (does this match intent? is this the right product behavior?) get the same weight as "did pytest pass". no-mistakes solves this with a pipeline where mechanical checks gate automatically and only intent-affecting findings escalate to the human.

## Proposed Solution

Checklist items get an optional class marker in the markdown — `[agent]` or `[human]` prefix on the item text (unmarked items default to `human`, the safe direction). `spec gate-check <id> --json` parses the marker and returns items split into `agent_verifiable: [...]` and `human_only: [...]` alongside the existing flat list. skill.md's at-gate workflow tells agents: before advancing to at-gate, run and report every `[agent]` item verbatim in the `--note`; never touch `[human]` items — relay them verbatim to the human. `spec new --ai` template guidance updated so AI-drafted checklists classify items at draft time (test/lint/diff commands → `[agent]`; product behavior, UX judgment, intent-vs-done → `[human]`).

## Acceptance Criteria

- [ ] **AC1**: a checklist item written as `- [ ] [agent] Run the tests: pytest -q` appears in `spec gate-check <id> --json` under `agent_verifiable`; an item marked `[human]` appears under `human_only`
- [ ] **AC2**: unmarked items (all existing specs) appear under `human_only` — default is human, nothing silently becomes agent-passable
- [ ] **AC3**: the existing `gate_checklist_items` flat array is unchanged (markers stripped from display text in all outputs) — no breaking change for current consumers
- [ ] **AC4**: skill.md's at-gate section instructs agents to pre-verify `[agent]` items and report results verbatim in the advance `--note`, and to relay `[human]` items verbatim without pre-judging
- [ ] **AC5**: the feature/api/bug templates' Human Gate Checklist sections ship with classified example items, so new specs are born classified

## Technical Notes

Parsing lives next to the existing checklist extraction in `src/spec_cli/commands/gate_check.py` (`extract_gate_checklist` / `_parse_items`) — a marker regex on each item, no new files. No frontmatter changes, no state-machine changes: the gate itself still requires a human for at-gate → implemented; this only changes what the human has to personally re-verify. This is the tiny-spec analogue of no-mistakes' split between auto-applied mechanical fixes and human-escalated intent findings — the classification is advisory metadata for the agent workflow, not a new enforcement layer.

### Dependencies / Blockers

None.

### Out of Scope

- Auto-executing `[agent]` items from tiny-spec itself (agents run them; the CLI only classifies) — no pipeline engine, per backlog's rejected list.
- Any change to the at-gate → implemented human requirement.
- `spec verify` integration (configured checks already gate mechanically).

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] [agent] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] [agent] **Walk the happy path**: create a scratch spec with one `[agent]` and one `[human]` checklist item, run `spec gate-check <id> --json`, confirm the split arrays and that markers are stripped from display text
- [ ] [agent] **Test the backward-compat case**: `spec gate-check 0005 --json` (unmarked legacy checklist) — all items land in `human_only`, flat `gate_checklist_items` unchanged
- [ ] [agent] **Check the diff**: `git diff main` — no debug code, no unrelated changes?
- [ ] [human] **Judgment call**: read skill.md's updated at-gate wording — does the verbatim-relay rule read unambiguous enough that an agent can't rationalize pre-judging a `[human]` item?
