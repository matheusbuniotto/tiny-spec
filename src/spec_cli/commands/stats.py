"""Pipeline health stats — one object for CI, bots, and morning checks."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from statistics import mean

import typer
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

from ..models import SpecStatus, STATUS_STYLE
from ..storage import list_specs, find_root
from ..ui import console

STALE_DAYS = 3
BAR_WIDTH = 20


def _age_days(dt: datetime) -> float:
    return (datetime.utcnow() - dt).total_seconds() / 86400


def _bar(value: int, total: int, color: str, width: int = BAR_WIDTH) -> str:
    if total == 0:
        filled = 0
    else:
        filled = round((value / total) * width)
    filled = max(0, min(width, filled))
    empty = width - filled
    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"


def cmd_stats(json_out: bool, root: Path) -> None:
    root = find_root(root)
    specs = list_specs(root)

    by_status = {s: [sp for sp in specs if sp.status == s] for s in SpecStatus}
    active = [s for s in specs if s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)]
    stale = [s for s in active if _age_days(s.updated_at) >= STALE_DAYS]
    at_gate = by_status[SpecStatus.AT_GATE]
    implemented = by_status[SpecStatus.IMPLEMENTED]

    cycle_days: list[float] = []
    for s in implemented:
        age = _age_days(s.created_at)
        if age > 0:
            cycle_days.append(age)

    avg_cycle = round(mean(cycle_days), 1) if cycle_days else None

    payload = {
        "total": len(specs),
        "active": len(active),
        "stale": len(stale),
        "blocked_at_gate": len(at_gate),
        "implemented": len(implemented),
        "closed": len(by_status[SpecStatus.CLOSED]),
        "avg_cycle_days": avg_cycle,
        "by_status": {s.value: len(v) for s, v in by_status.items()},
        "health": "green" if not stale and not at_gate else ("red" if stale else "yellow"),
    }

    if json_out:
        typer.echo(json.dumps(payload))
        return

    total = len(specs) or 1  # avoid div/0

    # ── Header ────────────────────────────────────────────────────────────────
    health_color = {"green": "bright_green", "yellow": "yellow", "red": "red"}[payload["health"]]
    health_icon = {"green": "●", "yellow": "◐", "red": "●"}[payload["health"]]
    console.print()
    console.print(Panel(
        f"[bold cyan]◈ spec stats[/bold cyan]  "
        f"[{health_color}]{health_icon} {payload['health'].upper()}[/{health_color}]  "
        f"[dim]{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}[/dim]",
        box=box.ROUNDED, border_style="bright_blue", padding=(0, 2),
    ))
    console.print()

    # ── Status breakdown ──────────────────────────────────────────────────────
    console.print(Rule("[dim]Pipeline[/dim]", style="dim"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column("status", style="bold", width=16, no_wrap=True)
    t.add_column("bar", no_wrap=True)
    t.add_column("n", width=4, no_wrap=True, style="bold")
    t.add_column("pct", width=6, no_wrap=True, style="dim")

    for s in SpecStatus:
        icon, color = STATUS_STYLE[s]
        count = len(by_status[s])
        pct = round(count / total * 100)
        t.add_row(
            f"[{color}]{icon} {s.value}[/{color}]",
            _bar(count, total, color),
            str(count),
            f"{pct}%",
        )

    console.print(t)
    console.print()

    # ── Key metrics ───────────────────────────────────────────────────────────
    console.print(Rule("[dim]Key metrics[/dim]", style="dim"))
    m = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    m.add_column("label", style="dim", no_wrap=True)
    m.add_column("value", style="bold")
    m.add_column("note", style="dim")

    m.add_row("Total specs", str(len(specs)), "")
    m.add_row("Active", str(len(active)), "not implemented or closed")

    stale_style = "red" if stale else "bright_green"
    m.add_row("Stale", f"[{stale_style}]{len(stale)}[/{stale_style}]",
              f">{STALE_DAYS}d without movement")

    gate_style = "magenta" if at_gate else "bright_green"
    m.add_row("Blocked at gate", f"[{gate_style}]{len(at_gate)}[/{gate_style}]",
              "waiting for human review")

    if avg_cycle is not None:
        cycle_color = "bright_green" if avg_cycle < 7 else ("yellow" if avg_cycle < 14 else "red")
        m.add_row("Avg cycle", f"[{cycle_color}]{avg_cycle}d[/{cycle_color}]",
                  f"draft→implemented ({len(implemented)} specs)")
    else:
        m.add_row("Avg cycle", "[dim]—[/dim]", "no implemented specs yet")

    console.print(m)
    console.print()

    # ── Alerts ────────────────────────────────────────────────────────────────
    alerts = []
    if stale:
        ids = " ".join(f"[bold]{s.id}[/bold]" for s in stale)
        alerts.append(f"[red]⚠ {len(stale)} stale:[/red] {ids}  [dim]→ spec list --stale[/dim]")
    if at_gate:
        ids = " ".join(f"[bold]{s.id}[/bold]" for s in at_gate)
        alerts.append(f"[magenta]⏸ {len(at_gate)} at gate:[/magenta] {ids}  [dim]→ spec gate-check <id>[/dim]")

    if alerts:
        console.print(Panel(
            "\n".join(alerts),
            title="[bold yellow]Attention needed[/bold yellow]",
            box=box.ROUNDED, border_style="yellow", padding=(0, 2),
        ))
    else:
        console.print(Panel(
            "[bright_green]✓ No blockers — pipeline is clean.[/bright_green]",
            box=box.ROUNDED, border_style="bright_green", padding=(0, 2),
        ))
    console.print()
