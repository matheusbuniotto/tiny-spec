# 005 — `spec claim --worktree`: parallel-agent isolation

**Size:** M · **PR:** `feat/claim-worktree`

Hard isolation beats coordination: each agent works in its own git worktree so
parallel sessions never touch each other's files. Composes with the existing
claim system — claim = assignee + branch + isolated directory in one command.

## Scope

- `spec claim <id> --agent <name> --worktree` additionally runs:
  `git worktree add ../<repo>-spec-<id> -b spec/<id>-<slug>`
- Prints the worktree path (and includes it in `--json` as `"worktree"`), plus a
  next-step hint: `cd <path>` then work there.
- Idempotent-ish: if the worktree/branch already exists, point at it instead of erroring.
- `spec advance <id>` to implemented (or `spec close`) prints a reminder that the
  worktree exists and how to remove it: `git worktree remove <path>`. No auto-delete —
  deleting a directory the agent may be standing in is not our call.
- Graceful error if not in a git repo or the branch name collides.

## Out of scope

Auto-cleanup, per-worktree env/db/port management, dependency install in the
worktree (document "run your install step" in the hint instead).

## Acceptance

- Smoke test in a scratch git repo: claim --worktree creates dir + branch,
  second claim of same spec reuses them.
- `--json` includes `worktree` and `branch` fields.
- Documented in skill.md workflow section ("parallel work" recipe).
