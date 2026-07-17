---
assignee: claude-fable
author: Matheus Buniotto
blocked_by: []
created_at: '2026-07-15T11:16:51.498048'
gate: ''
gate_notes: 'Fixed AC2 (was untestable — spec init errors on second run before any
  write logic; rewrote as no-overwrite-if-hand-authored) and extended scope to spec
  greenfield, which was the actual source of the Claude-only scaffold gap the problem
  statement described.


  ---

  Claimed by claude-fable'
id: '0005'
parent: ''
pr: ''
status: in-progress
tags:
- scaffold
- agents-md
template: feature
title: AGENTS.md scaffold + SessionStart hook
updated_at: '2026-07-17T01:14:45.425202'
---

## User Story

> As a **user driving tiny-spec with a non-Claude agent** (Codex, Cursor, Copilot), I want **`spec init` to scaffold the tool-agnostic AGENTS.md convention**, so that **tiny-spec works with whatever agent I'm using, not just Claude Code**.

## Problem Statement

> AGENTS.md is now the de facto universal agent-instruction format, read natively by Claude Code, Codex, Cursor, Copilot, and Gemini CLI. tiny-spec's project scaffolders — `spec init` and `spec greenfield` — currently write only Claude-specific files (`.claude/skills/spec/SKILL.md`, `CLAUDE.md`, `.claude/agents/`), nothing a non-Claude agent can read.

## Proposed Solution

`spec init` and `spec greenfield` each write a short `AGENTS.md` at project root if one doesn't already exist (skip + note otherwise) — covering what tiny-spec is, the golden-path commands, where specs live, and a pointer to constitution.md — derived from the existing SKILL.md content so there's one source of truth, not a second hand-maintained copy. An optional Claude Code `SessionStart` hook (prompted in init, or a `--hooks` flag) runs `spec next --json` so every session opens with pipeline state visible.

## Acceptance Criteria

- [ ] **AC1**: fresh `spec init --yes` produces an `AGENTS.md` at project root
- [ ] **AC2**: `spec greenfield <dir> --yes` produces the same `AGENTS.md` at project root
- [ ] **AC3**: if `AGENTS.md` already exists at project root (e.g. hand-authored) before `spec init` or `spec greenfield` runs, it's left untouched — not overwritten
- [ ] **AC4**: the optional SessionStart hook is opt-in, not default-on

## Technical Notes

Generate AGENTS.md content from SKILL.md's existing sections rather than hand-writing a parallel doc that will drift. The no-overwrite check (AC3) happens at write time, not via a second `spec init` run — `cmd_init` already hard-errors with "Already initialized" if `.spec/` exists, so the real scenario is a hand-authored `AGENTS.md` present *before* the first successful init/greenfield.

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
- [ ] **Walk the happy path**: `spec init --yes` in a scratch dir, confirm AGENTS.md exists and documents the real command surface; also run `spec greenfield <dir> --yes`, confirm AGENTS.md there too
- [ ] **Test the failure case**: hand-write an AGENTS.md in a scratch dir before running `spec init --yes`, confirm it's left untouched (not overwritten)
- [ ] **Check the diff**: `git diff main` — no debug code, no unrelated changes, no hardcoded secrets?
- [ ] **Re-read acceptance criteria**: each AC above is demonstrably met?