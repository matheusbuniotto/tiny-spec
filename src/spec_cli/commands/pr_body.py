"""Render Intent/Risk/Evidence PR-body markdown from a spec."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer

from ..storage import find_spec
from ..ui import find_root_or_error, not_found


def _section(body: str, heading: str) -> str:
    """Pull the content of a `## heading` or `### heading` section, minus blockquote guidance."""
    pattern = re.compile(
        rf"#{{2,3}}\s+{re.escape(heading)}\s*\n(.*?)(?=\n#{{2,3}}\s|\Z)", re.DOTALL
    )
    m = pattern.search(body)
    if not m:
        return ""
    raw = m.group(1).strip()
    lines = [line for line in raw.splitlines() if line.strip()]
    return "\n".join(lines).strip()


def _build_intent(spec) -> str:
    parts = [
        _section(spec.body, "User Story"),
        _section(spec.body, "Problem Statement"),
        _section(spec.body, "Proposed Solution"),
    ]
    return "\n\n".join(p for p in parts if p)


_AC_RE = re.compile(r"-\s*\[( |x|X)\]\s*(.+)")


def _build_evidence(spec) -> str:
    ac_section = _section(spec.body, "Acceptance Criteria")
    lines = []
    for line in ac_section.splitlines():
        m = _AC_RE.match(line.strip())
        if not m:
            continue
        mark = "x" if m.group(1).lower() == "x" else " "
        text = m.group(2).strip().replace("**", "")
        lines.append(f"- [{mark}] {text}")
    if spec.gate_notes:
        lines.append("")
        lines.append(spec.gate_notes)
    if not lines:
        return "_No Acceptance Criteria or gate notes recorded yet._"
    return "\n".join(lines)


def _build_risk(spec) -> str:
    out_of_scope = _section(spec.body, "Out of Scope")
    if out_of_scope:
        return out_of_scope
    return "_No Out of Scope section in this spec — fill in known risks by hand._"


def cmd_pr_body(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root_or_error(root, json_out)
    spec = find_spec(root, spec_id)
    if not spec:
        not_found(spec_id, json_out)

    intent = _build_intent(spec)
    risk = _build_risk(spec)
    evidence = _build_evidence(spec)

    if json_out:
        typer.echo(
            json.dumps({"id": spec.id, "intent": intent, "risk": risk, "evidence": evidence})
        )
        return

    typer.echo(f"## Intent\n\n{intent}\n\n## Risk\n\n{risk}\n\n## Evidence\n\n{evidence}")
