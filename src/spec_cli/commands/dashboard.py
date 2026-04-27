from __future__ import annotations

import time
from pathlib import Path

from rich.columns import Columns
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box

from ..models import Spec, SpecStatus, STATUS_STYLE
from ..storage import list_specs, find_root
from ..ui import console, age_days

STALE_DAYS = 3


def _age_badge(spec: Spec) -> str:
    days = age_days(spec.updated_at)
    if days >= STALE_DAYS and spec.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED):
        return f" [red]({days}d)[/red]"
    if days >= 1:
        return f" [dim]({days}d)[/dim]"
    return ""


def _pipeline(specs) -> Columns:
    panels = []
    for status in SpecStatus:
        icon, color = STATUS_STYLE[status]
        matching = [s for s in specs if s.status == status]
        lines = []
        for s in matching:
            badge = _age_badge(s)
            lines.append(f"[bold]{s.id}[/bold] {s.title[:26]}{badge}")
        body = "\n".join(lines) or "[dim](none)[/dim]"
        count_label = f" ({len(matching)})" if matching else ""
        panels.append(Panel(body, title=f"[{color}]{icon} {status.value}{count_label}[/{color}]",
                           border_style=color, box=box.ROUNDED, expand=True, padding=(0, 1)))
    return Columns(panels, equal=True, expand=True)


def _summary(specs) -> Panel:
    rows = []
    for status in SpecStatus:
        icon, color = STATUS_STYLE[status]
        count = sum(1 for s in specs if s.status == status)
        bar = "█" * count + "░" * max(0, 10 - count)
        rows.append(f"[{color}]{icon} {status.value:<13}[/{color}] [{color}]{bar}[/{color}] [bold]{count}[/bold]")
    rows += ["", f"[dim]Total[/dim]  [bold]{len(specs)}[/bold]"]
    return Panel("\n".join(rows), title="[bold]Summary[/bold]", box=box.ROUNDED, border_style="dim", padding=(0, 1))


def _alerts(specs) -> str:
    lines = []
    at_gate = [s for s in specs if s.status == SpecStatus.AT_GATE]
    if at_gate:
        ids = ", ".join(f"[bold]{s.id}[/bold]" for s in at_gate)
        lines.append(f"[magenta]⏸ {len(at_gate)} spec{'s' if len(at_gate) != 1 else ''} waiting at gate:[/magenta] {ids}")

    stale = [s for s in specs
             if s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED) and age_days(s.updated_at) >= STALE_DAYS]
    if stale:
        ids = ", ".join(f"[bold]{s.id}[/bold] ({age_days(s.updated_at)}d)" for s in stale)
        lines.append(f"[red]⚠ {len(stale)} stale spec{'s' if len(stale) != 1 else ''} (>{STALE_DAYS}d):[/red] {ids}")

    return "\n".join(lines)


def _layout(specs, live: bool = False) -> Table:
    outer = Table.grid(expand=True)
    outer.add_column()
    subtitle = "  [dim]Ctrl+C to exit[/dim]" if live else ""
    outer.add_row(Panel(
        f"[bold cyan]◈ tiny-spec dashboard[/bold cyan]{subtitle}",
        box=box.ROUNDED, border_style="bright_blue", padding=(0, 1),
    ))

    alerts = _alerts(specs)
    if alerts:
        outer.add_row(Panel(alerts, box=box.ROUNDED, border_style="yellow", padding=(0, 1)))

    body = Table.grid(expand=True)
    body.add_column(ratio=4)
    body.add_column(ratio=1)
    body.add_row(_pipeline(specs), _summary(specs))
    outer.add_row(body)
    return outer


def cmd_dashboard(root: Path, watch: bool) -> None:
    root = find_root(root)
    if not watch:
        console.print(_layout(list_specs(root)))
        return
    try:
        with Live(console=console, refresh_per_second=2, screen=True) as live:
            while True:
                live.update(_layout(list_specs(root), live=True))
                time.sleep(1)
    except KeyboardInterrupt:
        pass
