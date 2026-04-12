"""Show the Human Gate Checklist for a spec — standalone command."""
from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from ..storage import find_spec, find_root
from ..ui import console, error

_GATE_CHECKLIST_RE = re.compile(
    r"## Human Gate Checklist\s*\n(.*?)(?=\n## |\Z)",
    re.DOTALL,
)


def _extract_gate_checklist(body: str) -> str:
    m = _GATE_CHECKLIST_RE.search(body)
    if not m:
        return ""
    raw = m.group(1).strip()
    lines = [l for l in raw.splitlines() if l.strip() and not l.strip().startswith(">")]
    return "\n".join(lines)


def cmd_gate_check(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    checklist = _extract_gate_checklist(spec.body)

    if json_out:
        typer.echo(json.dumps({
            "id": spec.id,
            "title": spec.title,
            "status": spec.status.value,
            "has_gate_checklist": bool(checklist),
            "gate_checklist": checklist,
        }))
        return

    if not checklist:
        console.print(Panel(
            f"[bold]{spec.id}[/bold] — {spec.title}\n\n"
            "[yellow]⚠ No Human Gate Checklist found.[/yellow]\n"
            "[dim]Add a '## Human Gate Checklist' section to the spec file.[/dim]",
            title="[bold yellow]No Checklist[/bold yellow]",
            box=box.ROUNDED, border_style="yellow",
        ))
        return

    console.print(Panel(
        Markdown(f"**{spec.id}** — {spec.title}\n\n{checklist}"),
        title="[bold magenta]⏸ Human Gate Checklist[/bold magenta]",
        box=box.ROUNDED, border_style="magenta",
    ))
