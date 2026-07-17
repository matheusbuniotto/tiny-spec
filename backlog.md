# Backlog — later, maybe, or never

Deferred items from the 2026-07 AI-first engineering mapping (AXI principles,
no-mistakes patterns, ecosystem research) plus a 2026-07-16 gap check against
spec-kit (GitHub), no-mistakes (kunchenguid), and lavish-axi (kunchenguid).
Near-term work lives in `tasks/`; this file is for ideas that earned a note
but not a PR yet. Review when the tasks/ queue empties — promote, or delete
without guilt.

## P0 — real must-haves, close these first

- **Finish spec 0005 (AGENTS.md scaffold + SessionStart hook)** — currently
  `approved`, not implemented. This is the one place tiny-spec actually lags
  the reference set: spec-kit supports Copilot/Gemini/Cursor, no-mistakes
  lists claude/codex/rovodev/opencode, and tiny-spec's `SKILL.md` is
  Claude-only today. `AGENTS.md` is the cross-agent standard — ship it before
  anything else here.
- **`spec review --json` returns unstructured markdown** — `doctor` already
  emits structured findings (`{type, spec_id, message, hint}`); `review`
  still dumps a markdown blob an agent has to re-parse for Blockers/
  Suggestions. Parse into `blockers: [...]` / `suggestions: [...]` arrays the
  same way `doctor` does. Small, consistent with an existing pattern, not a
  new one.
- **Dogfood: fill in this repo's own `.spec/constitution.md`** — still the
  empty template (blank Principles/Standards/Out of Bounds/Glossary). README
  sells the living-glossary feature; the source repo doesn't use it.

## P1 — do next, no blockers

- **Action-classified gate checklist items** — promoted to spec 0012
  ("Gate split: agent-verifiable checks vs human-only decisions").
- **`spec doctor --fix`** — auto-fix the mechanical findings (drop dangling
  refs, close satisfied maps). Only after doctor's findings are trusted in
  practice.
- **`commands:` block feeding AI drafts** — expose configured checks to
  `spec new --ai` so generated Human Gate Checklists name the *exact*
  commands (`uv run pytest`) instead of guessing.
- **Intent-verbatim pattern** — no-mistakes requires `--intent` passed
  verbatim from the conversation as authoritative acceptance criteria. tiny-
  spec analogue: richer guidance on `advance --note` and spec Context
  sections ("capture decisions, tradeoffs, ruled-out approaches — a
  paragraph, not a line"). Pure skill.md wording; fold into any docs-touching
  PR.
- **Relay-verbatim skill discipline** — at-gate section of skill.md: agents
  relay checklist items / findings verbatim, never paraphrase or pre-judge.
  Fold into a docs pass if trivial, else its own line.

## P2 — later, opportunistic

- **`spec init --ci`** — scaffold a GitHub Actions workflow for user projects
  running `spec doctor` + `spec verify`. After doctor exists and proves
  useful (it does now — this can move up once someone wants it).
- **pre-commit hooks** — CI covers the trust boundary; add only if drift
  actually happens in practice.
- **mypy in CI** — declared in dev deps, never run; enabling it is its own
  cleanup PR.
- **Competitive glance: "specops" (Jarvus)** — spec-driven-dev AXI listed in
  the axi.md ecosystem catalog. Worth an hour of study for convergent ideas.

## P3 — token/output diet, defer until real pain

- **Minimal default schemas (AXI P2)** — trim `--json` defaults to 3–4 fields
  (`id`, `title`, `status`, …) with `--full` for everything. Breaking change
  for existing consumers; do in one deliberate pass, not piecemeal. Revisit
  after real agent transcripts show which fields go unused.
- **TOON output format** — ~40% token savings vs JSON, but a second
  serialization format + dependency that only pays off at hundreds of rows.
  tiny-spec payloads are small. Adopt only if `spec export` on big projects
  becomes a real agent pain point.
- **Body-less default everywhere** — `show --json` returns frontmatter only,
  `--body` opts in. Same breaking-change caveat as minimal schemas.

## Explicitly rejected (don't re-add)

- Daemon / git-proxy gate architecture, pipeline engine with finding IDs and
  auto-fix rounds, TUI, multi-agent backend orchestration, telemetry/
  benchmark infrastructure — all no-mistakes features that would double the
  codebase. tiny-spec's gate is a human reading a checklist. Keep it that way.
- Owning push/PR/CI end-to-end — that's no-mistakes' job. Pair the two tools
  (spec for lifecycle/gating, no-mistakes for push-time validation) instead
  of rebuilding it here.
- Splitting spec body into separate plan.md/tasks.md artifacts (spec-kit
  does this) — folded into the spec body + Human Gate Checklist on purpose;
  splitting it contradicts "tiny." Use `map` + child specs when a spec
  actually needs decomposing.
- Extension/preset template-override system (spec-kit) — no evidence tiny-
  spec's templates need per-project overriding; adds a resolution-order
  concept for a problem nobody has hit.
