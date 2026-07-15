"""Show the Human Gate Checklist for a spec — standalone command."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich import box
from rich.markdown import Markdown
from rich.panel import Panel

from ..config import effective_gate, load_config
from ..storage import find_root, find_spec
from ..ui import console, not_found

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


def _parse_checklist_items(checklist: str) -> list[str]:
    items = []
    for line in checklist.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        item = re.sub(r"^-\s*\[[ xX]\]\s*", "", stripped)
        item = re.sub(r"^-\s+", "", item)
        if item:
            items.append(item)
    return items


def cmd_gate_check(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        not_found(spec_id, json_out)

    checklist = _extract_gate_checklist(spec.body)
    gate_mode = effective_gate(spec, load_config(root))

    if json_out:
        typer.echo(
            json.dumps(
                {
                    "id": spec.id,
                    "title": spec.title,
                    "status": spec.status.value,
                    "gate_mode": gate_mode,
                    "has_gate_checklist": bool(checklist),
                    "gate_checklist": checklist,
                    "gate_checklist_items": _parse_checklist_items(checklist),
                }
            )
        )
        return

    if not checklist:
        console.print(
            Panel(
                f"[bold]{spec.id}[/bold] — {spec.title}\n\n"
                "[yellow]⚠ No Human Gate Checklist found.[/yellow]\n"
                "[dim]Add a '## Human Gate Checklist' section to the spec file.[/dim]",
                title="[bold yellow]No Checklist[/bold yellow]",
                box=box.ROUNDED,
                border_style="yellow",
            )
        )
        return

    console.print(
        Panel(
            Markdown(f"**{spec.id}** — {spec.title}\n\n{checklist}"),
            title="[bold magenta]⏸ Human Gate Checklist[/bold magenta]",
            box=box.ROUNDED,
            border_style="magenta",
        )
    )
