# 006 — AGENTS.md scaffold + SessionStart hook

**Size:** S · **PR:** `feat/agents-md-scaffold`

AGENTS.md is the de facto universal agent-instruction format (read natively by
Claude Code, Codex, Cursor, Copilot, Gemini CLI, …). tiny-spec currently scaffolds
`.claude/skills/` only — Claude-specific.

## Scope

- `spec init` writes an `AGENTS.md` at project root (skip + note if one exists):
  short — what tiny-spec is, the golden-path commands (`spec next --json`,
  `spec show/claim/advance/verify`), where specs live, pointer to constitution.md.
  Derive content from the existing SKILL.md so there's one source of truth
  (a trimmed generated section, not a second hand-maintained copy).
- Optional Claude Code `SessionStart` hook scaffold (prompted in init, or
  `--hooks` flag): runs `spec next --json` so every session opens with pipeline
  state visible.

## Out of scope

Rewriting the skill system; CI scaffolding for user projects (backlog).

## Acceptance

- Fresh `spec init --yes` produces AGENTS.md; existing AGENTS.md is never overwritten.
- Hook is opt-in and documented.
