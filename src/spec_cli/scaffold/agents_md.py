"""Generate AGENTS.md from SKILL.md — one source of truth, not a hand-maintained duplicate."""

from __future__ import annotations

import re
from pathlib import Path

_SKILL_MD = Path(__file__).parent.parent / "SKILL.md"


def _section(markdown: str, heading: str) -> str:
    """Body of a `heading` line up to the next heading of any level."""
    pattern = rf"^{re.escape(heading)}\n(.*?)(?=\n#{{2,6}} |\Z)"
    match = re.search(pattern, markdown, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def generate_agents_md() -> str:
    skill = _SKILL_MD.read_text() if _SKILL_MD.exists() else ""
    bootstrap = _section(skill, "## Bootstrap (start of every session)")
    lifecycle = _section(skill, "### Lifecycle")

    parts = [
        "# AGENTS.md\n",
        "This project uses [tiny-spec](https://github.com/matheusbuniotto/tiny-spec) for "
        "spec-first development. The `spec` CLI is the source of truth for what's in "
        "flight and what to do next — same commands regardless of which agent you are.\n",
    ]
    if bootstrap:
        parts.append(f"## Start of every session\n\n{bootstrap}\n")
    if lifecycle:
        parts.append(f"## Golden-path commands\n\n{lifecycle}\n")
    parts.append(
        "## Where specs live\n\n"
        "- `.spec/specs/` — active specs\n"
        "- `.spec/decisions/` — ADRs\n"
        "- `.spec/log.md` — event log\n"
        "- `.spec/constitution.md` — project principles, standards, and glossary "
        "(read this before drafting new specs)\n"
    )
    return "\n".join(parts)


def write_agents_md(root: Path) -> bool:
    """Write AGENTS.md at root if it doesn't already exist. Returns True if written."""
    path = root / "AGENTS.md"
    if path.exists():
        return False
    path.write_text(generate_agents_md())
    return True
