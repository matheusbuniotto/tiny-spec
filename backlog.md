# Backlog — later, maybe, or never

Deferred items from the 2026-07 AI-first engineering mapping (AXI principles,
no-mistakes patterns, ecosystem research). Near-term work lives in `tasks/`;
this file is for ideas that earned a note but not a PR yet. Review when the
tasks/ queue empties — promote, or delete without guilt.

## Token saving / output diet

- **Minimal default schemas (AXI P2)** — trim `--json` defaults to 3–4 fields
  (`id`, `title`, `status`, …) with `--full` for everything. Breaking change for
  existing consumers; do in one deliberate pass, not piecemeal. Revisit after
  tasks/002 lands and real agent transcripts show which fields go unused.
- **TOON output format** — ~40% token savings vs JSON, but a second serialization
  format + dependency that only pays off at hundreds of rows. tiny-spec payloads
  are small. Adopt only if `spec export` on big projects becomes a real agent
  pain point. The *spirit* (counts, truncation, minimal schemas) ships in tasks/002.
- **Body-less default everywhere** — `show --json` returns frontmatter only,
  `--body` opts in. Same breaking-change caveat as minimal schemas.

## Validations / no-mistakes-adjacent

- **Action-classified gate checklist items** — tag Human Gate Checklist items
  `agent-verifiable` vs `human-only`; `gate-check --json` exposes the split so
  agents pre-verify what they may before parking at the gate. Revisit after
  `spec doctor` (tasks/004) proves the validation appetite.
- **`spec doctor --fix`** — auto-fix the mechanical findings (drop dangling refs,
  close satisfied maps). Only after doctor's findings are trusted.
- **Intent-verbatim pattern** — no-mistakes requires `--intent` passed verbatim
  from the conversation as authoritative acceptance criteria. tiny-spec analogue:
  richer guidance on `advance --note` and spec Context sections ("capture
  decisions, tradeoffs, ruled-out approaches — a paragraph, not a line").
  Pure skill.md wording; fold into any docs-touching PR.
- **Relay-verbatim skill discipline** — at-gate section of skill.md: agents relay
  checklist items / findings verbatim, never paraphrase or pre-judge. Fold into
  tasks/003's docs pass if trivial, else here.
- **`commands:` block feeding AI drafts** — expose configured checks to
  `spec new --ai` so generated Human Gate Checklists name the *exact* commands
  (`uv run pytest`) instead of guessing. Small, after tasks/003 renames the config.

## Scaffolding / ecosystem

- **`spec init --ci`** — scaffold a GitHub Actions workflow for user projects
  running `spec doctor` + `spec verify`. After doctor exists and proves useful.
- **pre-commit hooks** — CI covers the trust boundary; add only if drift actually
  happens in practice.
- **mypy in CI** — declared in dev deps, never run; enabling it is its own
  cleanup PR.
- **Competitive glance: "specops" (Jarvus)** — spec-driven-dev AXI listed in the
  axi.md ecosystem catalog. Worth an hour of study for convergent ideas.

## Explicitly rejected (don't re-add)

- Daemon / git-proxy gate architecture, pipeline engine with finding IDs and
  auto-fix rounds, TUI, multi-agent backend orchestration, telemetry/benchmark
  infrastructure — all no-mistakes features that would double the codebase.
  tiny-spec's gate is a human reading a checklist. Keep it that way.
