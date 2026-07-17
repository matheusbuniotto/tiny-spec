"""AGENTS.md scaffold — tool-agnostic agent instructions derived from SKILL.md."""

from __future__ import annotations

import json
from pathlib import Path

_SKILL_MD = Path(__file__).parent.parent / "SKILL.md"

# SKILL.md sections that make up the golden path. Extracted at scaffold time so
# SKILL.md stays the single source of truth — no parallel hand-maintained copy.
_SECTIONS = [
    "Bootstrap (start of every session)",
    "JSON output conventions",
    "Status lifecycle",
    "Gate rule (non-negotiable)",
]

_INTRO = """\
# AGENTS.md

This project uses [tiny-spec](https://github.com/matheusbuniotto/tiny-spec) for
spec-driven development. Every feature, bug fix, and decision is a markdown spec
in `.spec/specs/` with a lifecycle: draft → approved → in-progress → at-gate →
implemented. Drive it with the `spec` CLI — always pass `--json --yes`.

Project principles and shared vocabulary live in `.spec/constitution.md` — read
it before drafting or implementing anything.
"""


def _section(body: str, title: str) -> str:
    """Extract one `## title` section from markdown (heading included)."""
    for chunk in body.split("\n## ")[1:]:
        if chunk.startswith(title):
            return "## " + chunk.rstrip("\n-— ").rstrip() + "\n"
    return ""


def generate_agents_md() -> str:
    text = _SKILL_MD.read_text()
    body = text.split("---", 2)[2] if text.startswith("---") else text
    parts = [_INTRO] + [s for t in _SECTIONS if (s := _section(body, t))]
    return "\n".join(parts)


def write_agents_md(root: Path) -> bool:
    """Write AGENTS.md at project root. Returns False (untouched) if it exists."""
    target = root / "AGENTS.md"
    if target.exists():
        return False
    target.write_text(generate_agents_md())
    return True


def write_sessionstart_hook(root: Path) -> bool:
    """Write a Claude Code SessionStart hook running `spec next --json`.

    Returns False (untouched) if .claude/settings.json already exists.
    """
    settings = root / ".claude" / "settings.json"
    if settings.exists():
        return False
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {"hooks": [{"type": "command", "command": "spec next --json"}]}
                    ]
                }
            },
            indent=2,
        )
        + "\n"
    )
    return True
