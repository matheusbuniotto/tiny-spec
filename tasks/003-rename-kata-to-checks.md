# 003 — Rename kata → checks, `run-kata` → `spec verify`

**Size:** S · **PR:** `feat/rename-kata-verify`

"Kata" is the one piece of CLI vocabulary that doesn't explain itself. Do this
before other tasks touch docs so everything after uses the final vocabulary.

## Scope

- `spec run-kata` → `spec verify` (keep `run-kata` as a hidden alias for one release).
- Config key `katas:` → `checks:` in `.spec/config.yaml` — keep *reading* `katas:`
  so existing projects don't break; write `checks:` on save.
- `--skip-kata` flag on `advance` → `--skip-checks` (hidden alias likewise).
- Rename internals (`Kata` model, `kata.py`) only where cheap; user-facing surface
  is the priority.
- Update README.md, skill.md, `src/spec_cli/SKILL.md` (keep in sync!), scaffolded
  agent prompts, and `setup-checks` help text.

## Out of scope

`spec doctor` (task 004) — different command, different concern.

## Acceptance

- `spec verify` runs the configured checks; `spec run-kata` still works but is
  hidden from `--help`.
- A project with legacy `katas:` in config.yaml works unmodified.
- `grep -ri kata README.md skill.md` returns nothing.
