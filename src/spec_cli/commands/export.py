"""Export all spec context into a single AI-ingestible payload."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

from ..config import load_config
from ..models import SpecStatus, STATUS_STYLE
from ..storage import list_specs, find_root, spec_dir
from ..ui import console


def _age_str(dt: datetime) -> str:
    delta = datetime.utcnow() - dt
    d = delta.days
    if d == 0:
        h = delta.seconds // 3600
        return f"{h}h ago" if h > 0 else "just now"
    return f"{d}d ago"


def cmd_export(json_out: bool, active_only: bool, root: Path) -> None:
    root = find_root(root)
    cfg = load_config(root)
    specs = list_specs(root)

    if active_only:
        specs = [s for s in specs if s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)]

    sd = spec_dir(root)
    constitution = (sd / "constitution.md").read_text() if (sd / "constitution.md").exists() else ""
    git_context = (sd / "git-context.md").read_text() if (sd / "git-context.md").exists() else ""
    log_tail = ""
    log_path = sd / "log.md"
    if log_path.exists():
        lines = log_path.read_text().splitlines()
        log_tail = "\n".join(lines[-20:])

    payload = {
        "exported_at": datetime.utcnow().isoformat(),
        "config": {
            "project_name": cfg.project_name,
            "description": cfg.description,
            "languages": cfg.languages,
            "frameworks": cfg.frameworks,
            "libraries": cfg.libraries,
            "testing": cfg.testing,
            "architecture": cfg.architecture,
            "conventions": cfg.conventions,
            "out_of_bounds": cfg.out_of_bounds,
            "katas": [k.to_dict() for k in cfg.katas],
        },
        "constitution": constitution,
        "git_context": git_context,
        "recent_log": log_tail,
        "specs": [s.to_dict(include_body=True) for s in specs],
        "summary": {
            "total": len(specs),
            "by_status": {s.value: sum(1 for sp in specs if sp.status == s) for s in SpecStatus},
        },
    }

    if json_out:
        typer.echo(json.dumps(payload))
        return

    # ── Rich preview ──────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold cyan]◈ spec export[/bold cyan]  [dim]{root}[/dim]\n"
        f"[dim]{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}[/dim]"
        + (f"  [yellow]· active only[/yellow]" if active_only else ""),
        box=box.ROUNDED, border_style="bright_blue", padding=(0, 2),
    ))
    console.print()

    # Config summary
    cfg_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    cfg_table.add_column("k", style="dim cyan", no_wrap=True)
    cfg_table.add_column("v")
    if cfg.project_name:
        cfg_table.add_row("project", f"[bold]{cfg.project_name}[/bold]")
    if cfg.description:
        cfg_table.add_row("description", cfg.description)
    if cfg.languages:
        cfg_table.add_row("languages", "  ".join(f"[cyan]{l}[/cyan]" for l in cfg.languages))
    if cfg.frameworks:
        cfg_table.add_row("frameworks", "  ".join(f"[cyan]{f}[/cyan]" for f in cfg.frameworks))
    if cfg.testing:
        cfg_table.add_row("testing", cfg.testing)
    if cfg.katas:
        cfg_table.add_row("katas", "  ".join(f"[magenta]{k.name}[/magenta]" for k in cfg.katas))
    if cfg.out_of_bounds:
        cfg_table.add_row("out of bounds", "  ".join(f"[red]{o}[/red]" for o in cfg.out_of_bounds))
    console.print(Panel(cfg_table, title="[bold]Project context[/bold]", box=box.ROUNDED,
                        border_style="dim", padding=(0, 1)))

    # Spec list grouped by status
    console.print()
    active_statuses = [s for s in SpecStatus if s not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)]
    done_statuses = [SpecStatus.IMPLEMENTED, SpecStatus.CLOSED]

    for group_label, group_statuses in [("Active", active_statuses), ("Completed / Closed", done_statuses)]:
        group_specs = [s for s in specs if s.status in group_statuses]
        if not group_specs:
            continue
        console.print(Rule(f"[dim]{group_label} ({len(group_specs)})[/dim]", style="dim"))
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        t.add_column("id", style="bold dim", width=6, no_wrap=True)
        t.add_column("status", width=16, no_wrap=True)
        t.add_column("title")
        t.add_column("age", style="dim", width=9, no_wrap=True)
        t.add_column("tags", style="dim")
        for s in group_specs:
            icon, color = STATUS_STYLE[s.status]
            t.add_row(
                s.id,
                f"[{color}]{icon} {s.status.value}[/{color}]",
                s.title,
                _age_str(s.updated_at),
                " ".join(f"#{tag}" for tag in s.tags) if s.tags else "",
            )
        console.print(t)

    console.print()

    # Payload stats
    payload_bytes = len(json.dumps(payload).encode())
    console.print(
        f"  [dim]Specs exported:[/dim] [bold]{len(specs)}[/bold]"
        f"  [dim]Payload:[/dim] [bold]{payload_bytes // 1024} KB[/bold]"
        f"  [dim]·[/dim] [cyan]spec export --json | pbcopy[/cyan] [dim]to send to AI[/dim]"
    )
    console.print()
