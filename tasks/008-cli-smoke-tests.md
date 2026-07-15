# 008 — CLI smoke tests + skill-drift test

**Size:** M · **PR:** `test/cli-smoke-and-skill-drift`

23 commands, 2 test files, none exercising the CLI surface. These tests are the
local eval that makes CI (task 007) actually protective. Depends on 007 (CI) and
is easier after 001 (non-interactive JSON).

## Scope

- `tests/test_cli.py` using Typer's `CliRunner` + `tmp_path` git repo:
  - golden path: `init --yes` → `new --json` → `advance` ×4 → status transitions
    asserted via `show --json`
  - `claim` / release flow
  - `doctor` clean + one seeded finding (after task 004 lands)
  - JSON shape assertions on `list`, `next`, `show` (presence of `help[]`,
    `count` — after task 002 lands)
- `tests/test_skill_drift.py`: parse every `spec <subcommand>` and `--flag`
  mentioned in `skill.md`, assert each exists in the Typer app; assert
  `skill.md` and `src/spec_cli/SKILL.md` are byte-identical (kills the recurring
  manual-sync failure).

## Out of scope

Coverage targets, AI-drafting integration tests beyond the existing
`test_glossary.py` mock pattern.

## Acceptance

- Suite runs in <10s, no network, no real AI calls.
- Deliberately desyncing SKILL.md fails the drift test.
