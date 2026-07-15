# 002 — Agent output ergonomics: `help[]`, error recovery, counts

**Size:** M · **PR:** `feat/agent-output-ergonomics`

Adopts AXI principles P4/P5/P9 and no-mistakes' "errors carry the fix" pattern.
Benchmark evidence: next-command hints are the single biggest turn-count reducer
for agents driving a CLI.

## Scope

- Every `--json` output gains a `"help": [...]` array of concrete next-command
  templates for the current state (e.g. `spec show` on a claimable spec suggests
  `spec advance 0001 --yes --json`). One shared helper in `ui.py`; commands pass
  their suggestions.
- JSON errors gain the same `"help"` field with the exact recovery command.
- Rich (human) output: one dim next-step line where a clear next action exists.
- `spec list --json` returns `{"count": N, "specs": [...]}` — never a bare array.
- Empty states are definitive and echo the active filter:
  "0 specs match --status at-gate", never blank output.
- Truncation hints: `spec export` / `spec list --full` truncate long bodies with
  `"(truncated, N chars — use spec show <id> --json)"`.

## Out of scope

TOON output format (backlog), minimal-schema trimming of existing fields (backlog —
breaking change).

## Acceptance

- `spec next --json`, `show`, `list`, `advance`, `claim` all emit `help[]`.
- `spec show 9999 --json` error includes a `help` entry.
- `spec list --status at-gate` on empty result names the filter in both modes.
- Existing JSON consumers keep working (fields added, none removed) —
  update SKILL.md/skill.md to document `help[]` and the list envelope.
