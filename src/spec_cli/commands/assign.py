"""Assign a spec to a person or agent."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich import box

from ..models import STATUS_STYLE
from ..storage import find_spec, find_root, save_spec, append_log
from ..ui import console, error


def cmd_assign(spec_id: str, assignee: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    old_assignee = spec.assignee
    spec.assignee = assignee.strip()
    spec.updated_at = datetime.utcnow()
    save_spec(spec, root)

    action = "assigned" if assignee.strip() else "unassigned"
    append_log(root, f"👤 {action.upper()} `{spec.id}` **{spec.title}** → {assignee or '(none)'}")

    if json_out:
        typer.echo(json.dumps(spec.to_dict(include_body=False)))
        return

    icon, color = STATUS_STYLE[spec.status]
    old_str = f"[dim]{old_assignee}[/dim]" if old_assignee else "[dim](unassigned)[/dim]"
    new_str = f"[bold cyan]{assignee}[/bold cyan]" if assignee.strip() else "[dim](unassigned)[/dim]"

    console.print(Panel(
        f"[bold]{spec.id}[/bold] — {spec.title}\n"
        f"[{color}]{icon} {spec.status.value}[/{color}]\n\n"
        f"  [dim]Assignee:[/dim]  {old_str}  [dim]→[/dim]  {new_str}",
        title="[bold cyan]👤 Assigned[/bold cyan]",
        box=box.ROUNDED, border_style="cyan",
    ))
