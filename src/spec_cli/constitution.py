"""Read/update .spec/constitution.md — the project's living domain glossary lives here."""

from __future__ import annotations

import re
from pathlib import Path

from .storage import spec_dir

_GLOSSARY_RE = re.compile(r"## Glossary\s*\n(.*?)(?=\n## |\Z)", re.DOTALL)
_PROPOSED_HEADING = "## Glossary — Proposed (review before promoting)"


def constitution_path(root: Path) -> Path:
    return spec_dir(root) / "constitution.md"


def read_constitution(root: Path) -> str:
    p = constitution_path(root)
    return p.read_text() if p.exists() else ""


def approved_glossary(root: Path) -> str:
    """The human-curated ## Glossary section only — not the Proposed subsection."""
    m = _GLOSSARY_RE.search(read_constitution(root))
    if not m:
        return ""
    raw = m.group(1).split(_PROPOSED_HEADING)[0].strip()
    lines = [line for line in raw.splitlines() if line.strip() and not line.strip().startswith(">")]
    return "\n".join(lines)


def propose_glossary_terms(root: Path, terms: list[str]) -> list[str]:
    """Append new terms to constitution.md's Proposed section. Returns the ones actually added (skips exact dupes)."""
    text = read_constitution(root)
    added = [t.strip() for t in terms if t.strip() and t.strip() not in text]
    if not added:
        return []

    if _PROPOSED_HEADING in text:
        text = text.rstrip("\n") + "\n" + "\n".join(f"- {t}" for t in added) + "\n"
    else:
        text = (
            text.rstrip("\n")
            + f"\n\n{_PROPOSED_HEADING}\n\n"
            + "\n".join(f"- {t}" for t in added)
            + "\n"
        )

    constitution_path(root).write_text(text)
    return added
