---
assignee: ''
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T11:16:51.498048'
gate_notes: ''
id: '0005'
parent: ''
status: draft
tags:
- scaffold
- agents-md
template: feature
title: AGENTS.md scaffold + SessionStart hook
updated_at: '2026-07-15T11:16:51.498167'
---

## User Story

> As a **user driving tiny-spec with a non-Claude agent** (Codex, Cursor, Copilot), I want **`spec init` to scaffold the tool-agnostic AGENTS.md convention**, so that **tiny-spec works with whatever agent I'm using, not just Claude Code**.

## Problem Statement

> AGENTS.md is now the de facto universal agent-instruction format, read natively by Claude Code, Codex, Cursor, Copilot, and Gemini CLI. tiny-spec currently only scaffolds `.claude/skills/`, which is Claude-specific.

## Proposed Solution

`spec init` writes a short `AGENTS.md` at project root (skip + note if one already exists) covering: what tiny-spec is, the golden-path commands, where specs live, and a pointer to constitution.md — derived from the existing SKILL.md content so there's one source of truth, not a second hand-maintained copy. An optional Claude Code `SessionStart` hook (prompted in init, or a `--hooks` flag) runs `spec next --json` so every session opens with pipeline state visible.

## Acceptance Criteria

- [ ] **AC1**: fresh `spec init --yes` produces an `AGENTS.md` at project root
- [ ] **AC2**: running `spec init` again on a project with an existing `AGENTS.md` never overwrites it
- [ ] **AC3**: the optional SessionStart hook is opt-in, not default-on

## Technical Notes

Generate AGENTS.md content from SKILL.md's existing sections rather than hand-writing a parallel doc that will drift.

### Dependencies / Blockers

None.

### Out of Scope

Rewriting the skill system; CI scaffolding for user projects (separate spec).

## Definition of Done

- [ ] All acceptance criteria above are met
- [ ] Tests written and passing (`uv run pytest tests/ -q`)
- [ ] No regressions in related flows
- [ ] Code reviewed or self-reviewed against project conventions
- [ ] `.spec/` updated if any follow-on specs are needed

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Run the tests**: `uv run pytest tests/ -q` — all pass, no skips that weren't there before?
- [ ] **Walk the happy path**: `spec init --yes` in a scratch dir, confirm AGENTS.md exists and documents the real command surface
- [ ] **Test the failure case**: run `spec init` twice, confirm the second run doesn't clobber a hand-edited AGENTS.md
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?
