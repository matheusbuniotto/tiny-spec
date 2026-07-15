# Spec Log

Append-only record of spec events.

- **2026-07-15 11:16 UTC** — `0001` **Agent output ergonomics: help[], counts, truncation** created (template: feature)
- **2026-07-15 11:16 UTC** — `0002` **Rename kata to checks, run-kata to spec verify** created (template: feature)
- **2026-07-15 11:16 UTC** — `0003` **spec doctor: spec-graph validator** created (template: feature)
- **2026-07-15 11:16 UTC** — `0004` **spec claim --worktree: parallel-agent isolation** created (template: feature)
- **2026-07-15 11:16 UTC** — `0005` **AGENTS.md scaffold + SessionStart hook** created (template: feature)
- **2026-07-15 11:16 UTC** — `0006` **Repo hygiene: CI, ruff config, own AGENTS.md** created (template: feature)
- **2026-07-15 11:16 UTC** — `0007` **CLI smoke tests + skill-drift test** created (template: feature)
- **2026-07-15 11:19 UTC** — `0002` **Rename kata to checks, run-kata to spec verify** → `approved`
- **2026-07-15 11:22 UTC** — `0002` **Rename kata to checks, run-kata to spec verify** → `in-progress`
- **2026-07-15 11:33 UTC** — 🔵 GATE OPENED `0002` **Rename kata to checks, run-kata to spec verify** — Renamed run-kata to verify (hidden alias kept), katas: to checks: in config.yaml (legacy key still read), --skip-kata to --skip-checks (hidden alias kept). Swept all user-facing strings/JSON keys (kata_failed->checks_failed error code, katas->checks JSON field) in kata.py, lifecycle.py, config_cmd.py, export.py, setup_checks.py, init.py, greenfield.py scaffolds, skill.md/SKILL.md, claude_md.py, agents.py, data-pipeline.md template. Kept internal Python names (Kata class, kata.py, cfg.katas attribute) unchanged per the spec's own scope decision. grep -ri kata README.md skill.md src/spec_cli/SKILL.md returns nothing. 20/20 tests pass, manually verified spec verify/run-kata/--help in a scratch project.
- **2026-07-15 14:59 UTC** — `0008` **Gate modes: local, draft, pr** created (template: feature)
- **2026-07-15 14:59 UTC** — `0009` **no-mistakes integration as pluggable gate engine** created (template: feature)
- **2026-07-15 14:59 UTC** — `0010` **spec pr-body: generate Intent/Risk/Evidence from a spec** created (template: feature)
- **2026-07-15 14:59 UTC** — `0011` **Tracer-bullet AC: ordered vertical slices in feature/api templates** created (template: feature)
- **2026-07-15 15:10 UTC** — `0008` **Gate modes: local, draft, pr** → `approved`
- **2026-07-15 15:10 UTC** — `0008` **Gate modes: local, draft, pr** → `in-progress`
- **2026-07-15 15:10 UTC** — 🔵 GATE OPENED `0008` **Gate modes: local, draft, pr** — Implemented via TDD: Config.gate (default local, read+write), Spec.gate/pr frontmatter fields, effective_gate() helper, --pr flag on spec advance (satisfies notes-required, records pr distinctly), gate_mode surfaced in spec show/gate-check --json. 9/9 new tests pass (tests/test_gate_modes.py). Full suite 27/29 — 2 pre-existing failures in test_verify_checks_rename.py confirmed unrelated via git stash. AC1-AC4 all covered by tests.
- **2026-07-15 15:17 UTC** — ✅ GATE PASSED `0008` **Gate modes: local, draft, pr** — PR #7
- **2026-07-15 15:18 UTC** — ✅ GATE PASSED `0002` **Rename kata to checks, run-kata to spec verify** — PR #6
- **2026-07-15 15:19 UTC** — `0010` **spec pr-body: generate Intent/Risk/Evidence from a spec** → `approved`
- **2026-07-15 15:19 UTC** — `0010` **spec pr-body: generate Intent/Risk/Evidence from a spec** → `in-progress`
- **2026-07-15 15:24 UTC** — 🔵 GATE OPENED `0010` **spec pr-body: generate Intent/Risk/Evidence from a spec** — Implemented via TDD: spec pr-body <id> [--json] renders Intent (User Story + Problem Statement + Proposed Solution), Risk (Out of Scope, with graceful fallback when absent), Evidence (AC checkbox state + gate_notes). Fixed a real bug found via manual verification against spec 0008: the blockquote-line filter meant to skip unfilled template guidance was also stripping real filled content, since specs here write User Story/Problem Statement as blockquotes by convention — fixed and regression-tested. 7/7 new tests pass, full suite 34/36 (2 pre-existing unrelated failures).
- **2026-07-15 16:02 UTC** — ✅ GATE PASSED `0010` **spec pr-body: generate Intent/Risk/Evidence from a spec** — PR #8
