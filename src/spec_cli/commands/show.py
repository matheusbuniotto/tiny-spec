from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich import box

from ..models import SpecStatus, STATUS_STYLE, TRANSITIONS, TRANSITION_LABELS
from ..storage import find_spec, find_root
from ..ui import console, error

_STAGE_ORDER = list(SpecStatus)

_NEXT_ACTIONS: dict[SpecStatus, str] = {
    SpecStatus.DRAFT:       "Review and approve → [cyan]spec advance {id}[/cyan]",
    SpecStatus.APPROVED:    "Start implementation → [cyan]spec advance {id}[/cyan]",
    SpecStatus.IN_PROGRESS: "Finish and gate → [cyan]spec advance {id} --note \"...\"[/cyan]",
    SpecStatus.AT_GATE:     "Verify the gate checklist → [cyan]spec gate-check {id}[/cyan] then [cyan]spec advance {id} --note \"...\"[/cyan]",
    SpecStatus.IMPLEMENTED: "[dim]Done — no further action[/dim]",
}


def _progress_bar(status: SpecStatus) -> str:
    stages = _STAGE_ORDER
    idx = stages.index(status)
    parts = []
    for i, s in enumerate(stages):
        icon, color = STATUS_STYLE[s]
        if i < idx:
            parts.append(f"[dim green]● {s.value}[/dim green]")
        elif i == idx:
            parts.append(f"[bold {color}]● {s.value}[/bold {color}]")
        else:
            parts.append(f"[dim]○ {s.value}[/dim]")
    return "  →  ".join(parts)


def _age_str(dt: datetime) -> str:
    delta = datetime.utcnow() - dt
    days = delta.days
    if days == 0:
        hours = delta.seconds // 3600
        return f"{hours}h ago" if hours > 0 else "just now"
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


def cmd_show(spec_id: str, json_out: bool, root: Path, *, full: bool = False) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    if json_out:
        typer.echo(json.dumps(spec.to_dict(include_body=True)))
        return

    icon, color = STATUS_STYLE[spec.status]
    tags_str = "  ".join(f"[dim]#{t}[/dim]" for t in spec.tags) if spec.tags else "[dim](none)[/dim]"

    progress = _progress_bar(spec.status)
    next_action = _NEXT_ACTIONS[spec.status].format(id=spec.id)

    assignee_str = f"[cyan]{spec.assignee}[/cyan]" if spec.assignee else "[dim]—[/dim]"
    meta = (
        f"[bold]{spec.id}[/bold]  [{color}]{icon} {spec.status.value}[/{color}]"
        f"  [dim]({_age_str(spec.updated_at)})[/dim]\n"
        f"[dim]Author:[/dim] {spec.author or '—'}   "
        f"[dim]Assignee:[/dim] {assignee_str}   "
        f"[dim]Template:[/dim] {spec.template}   "
        f"[dim]Updated:[/dim] {spec.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"[dim]Tags:[/dim] {tags_str}\n\n"
        f"{progress}\n\n"
        f"[dim]Next →[/dim] {next_action}"
    )
    if spec.gate_notes:
        meta += f"\n\n[dim]Gate notes:[/dim]\n[dim]{spec.gate_notes}[/dim]"

    console.print(Panel(meta, title=f"[bold]{spec.title}[/bold]", box=box.ROUNDED, border_style=color))

    if full:
        console.print()
        console.print(Markdown(spec.body))
        console.print(Rule(style="dim"))
    else:
        console.print(f"[dim]Use [cyan]spec show {spec.id} --full[/cyan] to see the full spec body[/dim]")

    console.print(f"[dim]{spec.file_path}[/dim]")
