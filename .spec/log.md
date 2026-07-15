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
