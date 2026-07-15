# 001 — `--json` implies non-interactive (bug fix)

**Size:** S · **PR:** `fix/json-non-interactive`

## Problem

`spec new "Title" --json` crashes with a questionary traceback when stdin is not a
terminal: interactive prompts fire whenever `--yes` is absent, even in JSON mode.
Any agent or CI pipeline calling without `--yes` hits it.

## Scope

- `--json` behaves as `--yes` everywhere: no prompt may ever fire in JSON mode
  (`new.py` is the known offender — audit the other commands that import questionary).
- Missing required input in JSON mode → structured JSON error on stdout + exit 1,
  not a prompt, not a traceback.
- Codify the exit-code contract with a test: 0 = success/no-op, 1 = error, 2 = bad usage;
  JSON errors always on stdout.

## Out of scope

`help[]` hints on outputs (task 002).

## Acceptance

- `echo | spec new "X" --json` (non-TTY stdin) creates a spec with defaults, exits 0.
- `echo | spec new --json` (no title) prints a JSON error, exits 1.
- New test file asserts exit codes for success / error / bad-usage cases.
