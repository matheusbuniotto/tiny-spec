"""Show the single most important action across all specs."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.panel import Panel
from rich import box

from ..models import SpecStatus, STATUS_STYLE, CLOSE_REASONS
from ..storage import list_specs, find_root
from ..ui import console

_PRIORITY = {
    SpecStatus.AT_GATE:     0,
    SpecStatus.IN_PROGRESS: 1,
    SpecStatus.APPROVED:    2,
    SpecStatus.DRAFT:       3,
}

_ACTIONS: dict[SpecStatus, str] = {
    SpecStatus.AT_GATE:     "Verify the gate checklist and pass or reject",
    SpecStatus.IN_PROGRESS: "Continue implementation",
    SpecStatus.APPROVED:    "Start implementation",
    SpecStatus.DRAFT:       "Review and approve",
}

_COMMANDS: dict[SpecStatus, str] = {
    SpecStatus.AT_GATE:     'spec gate-check {id}  then  spec advance {id} --note "..."',
    SpecStatus.IN_PROGRESS: 'spec show {id}',
    SpecStatus.APPROVED:    'spec advance {id}',
    SpecStatus.DRAFT:       'spec show {id}  then  spec advance {id}',
}


def _age_days(dt: datetime) -> int:
    return (datetime.utcnow() - dt).days


def cmd_next(json_out: bool, root: Path) -> None:
    root = find_root(root)
    specs = list_specs(root)
    active = [s for s in specs if s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)]

    if not active:
        if json_out:
            typer.echo(json.dumps({"action": "none", "message": "All specs implemented or none exist."}))
        else:
            console.print("[dim]Nothing to do — all specs are implemented or none exist.[/dim]")
            console.print("[dim]Create one:[/dim] [cyan]spec new \"...\"[/cyan]")
        return

    active.sort(key=lambda s: (_PRIORITY.get(s.status, 99), -_age_days(s.updated_at)))
    top = active[0]

    action = _ACTIONS.get(top.status, "Review")
    cmd = _COMMANDS.get(top.status, f"spec show {top.id}").format(id=top.id)
    icon, color = STATUS_STYLE[top.status]
    days = _age_days(top.updated_at)
    age_str = f"{days}d ago" if days > 0 else "today"

    if json_out:
        claimable = [s for s in active if s.status == SpecStatus.APPROVED and not s.assignee]
        claimable.sort(key=lambda s: -_age_days(s.updated_at))
        queue = [{"id": s.id, "title": s.title, "age_days": _age_days(s.updated_at)} for s in claimable[:3]]
        typer.echo(json.dumps({
            "id": top.id,
            "title": top.title,
            "status": top.status.value,
            "assignee": top.assignee,
            "action": action,
            "command": cmd,
            "age_days": days,
            "claimable_queue": queue,
        }))
        return

    body = (
        f"[bold]{top.id}[/bold] — {top.title}\n"
        f"[{color}]{icon} {top.status.value}[/{color}]  [dim]({age_str})[/dim]\n\n"
        f"[bold]{action}[/bold]\n\n"
        f"[cyan]{cmd}[/cyan]"
    )

    remaining = len(active) - 1
    if remaining > 0:
        body += f"\n\n[dim]+{remaining} more active spec{'s' if remaining != 1 else ''}[/dim]"

    console.print(Panel(
        body,
        title="[bold bright_blue]▶ Next action[/bold bright_blue]",
        box=box.ROUNDED, border_style="bright_blue",
    ))
