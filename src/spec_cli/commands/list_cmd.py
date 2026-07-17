from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.table import Table

from ..models import STATUS_STYLE, SpecStatus
from ..storage import broken_spec_files, list_specs, open_blockers
from ..ui import console, error, find_root_or_error, truncate_body, with_help

STALE_DAYS = 3


def _age_days(dt: datetime) -> int:
    return (datetime.utcnow() - dt).days


def _active_filters(
    status: Optional[str],
    stale: bool,
    assignee: Optional[str],
    claimable: bool,
    blocked: bool,
    parent: Optional[str],
) -> str:
    parts = []
    if status:
        parts.append(f"--status {status}")
    if stale:
        parts.append("--stale")
    if assignee:
        parts.append(f"--assignee {assignee}")
    if claimable:
        parts.append("--claimable")
    if blocked:
        parts.append("--blocked")
    if parent:
        parts.append(f"--parent {parent}")
    return " ".join(parts)


def cmd_list(
    status: Optional[str],
    stale: bool,
    json_out: bool,
    root: Path,
    full: bool = False,
    assignee: Optional[str] = None,
    claimable: bool = False,
    blocked: bool = False,
    parent: Optional[str] = None,
) -> None:
    root = find_root_or_error(root, json_out)
    filter_status: Optional[SpecStatus] = None

    if status:
        try:
            filter_status = SpecStatus(status)
        except ValueError:
            valid = ", ".join(s.value for s in SpecStatus)
            error(
                f"Invalid status. Valid: {valid}",
                json_out,
                {"error": "invalid_status", "valid": valid},
            )

    all_specs = list_specs(root)
    specs = list_specs(root, filter_status)

    if stale:
        specs = [
            s
            for s in specs
            if s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)
            and _age_days(s.updated_at) >= STALE_DAYS
        ]

    if assignee:
        specs = [s for s in specs if assignee.lower() in (s.assignee or "").lower()]

    if claimable:
        specs = [
            s
            for s in specs
            if s.status == SpecStatus.APPROVED
            and not s.assignee
            and not open_blockers(s, all_specs)
        ]

    if blocked:
        specs = [s for s in specs if open_blockers(s, all_specs)]

    if parent:
        specs = [s for s in specs if s.parent == parent.zfill(4)]

    broken = broken_spec_files(root) if not specs else []

    if json_out:
        spec_dicts = []
        for s in specs:
            d = s.to_dict(include_body=full)
            if full and "body" in d:
                d["body"] = truncate_body(d["body"], s.id)
            spec_dicts.append(d)
        help_cmd = f"spec show {specs[0].id} --json" if specs else 'spec new "<title>" --yes --json'
        payload = with_help({"count": len(spec_dicts), "specs": spec_dicts}, help_cmd)
        if broken:
            payload["warnings"] = [
                f"{len(broken)} spec file(s) exist but failed to load — run `spec doctor` for details"
            ]
        typer.echo(json.dumps(payload))
        return

    if not specs:
        if broken:
            console.print(
                f"[yellow]⚠ {len(broken)} spec file(s) exist but failed to load[/yellow] "
                f"[dim](malformed/missing frontmatter — run [cyan]spec doctor[/cyan] for details)[/dim]"
            )
            return
        filters = _active_filters(status, stale, assignee, claimable, blocked, parent)
        if stale and filters == "--stale":
            console.print("[dim]No stale specs — everything is moving.[/dim]")
        elif filters:
            console.print(f"[dim]0 specs match {filters}[/dim]")
        else:
            console.print('[dim]No specs found.[/dim] Run [cyan]spec new "My spec"[/cyan]')
        return

    has_assignees = any(s.assignee for s in specs)
    table = Table(
        box=box.ROUNDED, border_style="dim", header_style="bold", show_lines=False, pad_edge=True
    )
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
        is_stale = days >= STALE_DAYS and s.status not in (
            SpecStatus.IMPLEMENTED,
            SpecStatus.CLOSED,
        )
        age_style = "[red]" if is_stale else "[dim]"
        age_close = "[/red]" if is_stale else "[/dim]"
        row_args = [
            s.id,
            s.title,
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
