# 004 — `spec doctor`: spec-graph validator

**Size:** M · **PR:** `feat/spec-doctor`

The "linter" for the artifact tiny-spec owns. Deterministic, no AI, drops straight
into any CI pipeline.

## Scope

New command `spec doctor [--json]`. Checks:

- dangling `blocked_by` refs (blocker ID doesn't exist)
- dangling `parent` refs (map ID doesn't exist, or parent isn't a `map` template)
- duplicate spec IDs across specs/ and decisions/
- `in-progress` specs with no assignee
- stale claims (in-progress + assignee + not updated in N days; reuse `STALE_DAYS`)
- maps whose children are all implemented/closed but the map is still open
- specs at gate with no `## Human Gate Checklist` section
- circular `blocked_by` chains

Output: one line per finding with spec ID + fix hint; `--json` returns
`{"count": N, "findings": [...], "help": [...]}`. Exit 0 when clean, 1 when findings.

## Out of scope

Auto-fixing (backlog), action-classified findings (backlog).

## Acceptance

- Unit tests per check (constructed Spec objects, same pattern as `test_storage.py`).
- Clean project → "✓ no issues", exit 0.
- Documented in README, skill.md, SKILL.md.
