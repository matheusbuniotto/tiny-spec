from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table
from rich import box

from ..models import SpecStatus, STATUS_STYLE
from ..storage import list_specs, find_root
from ..ui import console, error

STALE_DAYS = 3


def _age_days(dt: datetime) -> int:
    return (datetime.utcnow() - dt).days


def cmd_list(
    status: Optional[str], stale: bool, json_out: bool, root: Path,
    full: bool = False, assignee: Optional[str] = None,
) -> None:
    root = find_root(root)
    filter_status: Optional[SpecStatus] = None

    if status:
        try:
            filter_status = SpecStatus(status)
        except ValueError:
            valid = ", ".join(s.value for s in SpecStatus)
            error(f"Invalid status. Valid: {valid}", json_out, {"error": "invalid_status", "valid": valid})

    specs = list_specs(root, filter_status)

    if stale:
        specs = [s for s in specs
                 if s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)
                 and _age_days(s.updated_at) >= STALE_DAYS]

    if assignee:
        specs = [s for s in specs if assignee.lower() in (s.assignee or "").lower()]

    if json_out:
        typer.echo(json.dumps([s.to_dict(include_body=full) for s in specs]))
        return

    if not specs:
        if stale:
            console.print("[dim]No stale specs — everything is moving.[/dim]")
        else:
            console.print("[dim]No specs found.[/dim] Run [cyan]spec new \"My spec\"[/cyan]")
        return

    has_assignees = any(s.assignee for s in specs)
    table = Table(box=box.ROUNDED, border_style="dim", header_style="bold", show_lines=False, pad_edge=True)
    table.add_column("ID", style="bold dim", width=6, no_wrap=True)
    table.add_column("Title", min_width=20)
    table.add_column("Status", width=18)
    table.add_column("Age", width=8, no_wrap=True)
    if has_assignees:
        table.add_column("Assignee", style="cyan", width=14, no_wrap=True)
    table.add_column("Tags", style="dim")

    for i, s in enumerate(specs):
        icon, color = STATUS_STYLE[s.status]
        days = _age_days(s.updated_at)
        age_str = f"{days}d" if days > 0 else "today"
        is_stale = days >= STALE_DAYS and s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)
        age_style = "[red]" if is_stale else "[dim]"
        age_close = "[/red]" if is_stale else "[/dim]"
        row_args = [
            s.id, s.title,
            f"[{color}]{icon} {s.status.value}[/{color}]",
            f"{age_style}{age_str}{age_close}",
        ]
        if has_assignees:
            row_args.append(s.assignee or "[dim]—[/dim]")
        row_args.append(", ".join(s.tags) if s.tags else "")
        table.add_row(*row_args, style="" if i % 2 == 0 else "on grey7")

    console.print(table)
    label = "stale spec" if stale else "spec"
    console.print(f"[dim]{len(specs)} {label}{'s' if len(specs) != 1 else ''}[/dim]")
