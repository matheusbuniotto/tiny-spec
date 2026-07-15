# 007 — Repo hygiene: CI, ruff config, own AGENTS.md

**Size:** S · **PR:** `chore/ci-and-lint`

tiny-spec has no CI: PRs #1–3 merged with zero automated verification. Agent-written
code must pass the same pipeline as human code — starting with this repo.

## Scope

- `.github/workflows/ci.yml`: on PR + push to main — `uv sync`, `ruff check`,
  `ruff format --check`, `pytest`. One job, Python 3.11.
- `pyproject.toml`: real ruff rule selection — `select = ["E", "F", "I", "UP", "B"]`
  — and fix whatever it flags (expect import-sorting noise, little else).
- Run `ruff format` once to normalize.
- Add tiny-spec's own `AGENTS.md`: build/test commands (`uv run pytest`,
  `uv run ruff check`), src layout, the skill.md ↔ SKILL.md sync rule,
  conventions (JSON-first outputs, thin-by-design philosophy).

## Out of scope

mypy in CI (it's never been run; enabling it is its own cleanup — backlog),
pre-commit, coverage gates, release automation.

## Acceptance

- CI green on a no-op PR; red when a test is deliberately broken.
- `ruff check` and `ruff format --check` pass locally.
