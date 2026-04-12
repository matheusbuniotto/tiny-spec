"""spec log — show and filter the append-only event log."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.text import Text
from rich import box

from ..storage import find_root, spec_dir
from ..ui import console, error

_LOG_ENTRY_RE = re.compile(
    r"^- \*\*(?P<ts>[^*]+)\*\* — (?P<body>.+)$"
)

_STATUS_COLORS = {
    "GATE OPENED": "magenta",
    "GATE PASSED": "bright_green",
    "REVERTED": "yellow",
    "CLOSED": "dim",
    "created": "cyan",
    "→": "blue",
}

_SPEC_ID_RE = re.compile(r"`(\d{4})`")


def _parse_log(log_path: Path) -> list[dict]:
    entries = []
    for line in log_path.read_text().splitlines():
        m = _LOG_ENTRY_RE.match(line.strip())
        if not m:
            continue
        entries.append({"ts": m.group("ts").strip(), "body": m.group("body").strip()})
    return entries


def _entry_color(body: str) -> str:
    for keyword, color in _STATUS_COLORS.items():
        if keyword in body:
            return color
    return "dim"


def _render_entry(entry: dict, query: Optional[str] = None) -> Text:
    t = Text()
    t.append(f"  {entry['ts']}", style="dim")
    t.append("  ")

    body = entry["body"]
    color = _entry_color(body)

    if query:
        lower = body.lower()
        lower_q = query.lower()
        pos = 0
        while True:
            idx = lower.find(lower_q, pos)
            if idx == -1:
                t.append(body[pos:], style=color)
                break
            t.append(body[pos:idx], style=color)
            t.append(body[idx:idx + len(query)], style="bold yellow")
            pos = idx + len(query)
    else:
        t.append(body, style=color)

    return t


def cmd_log(
    last: int,
    spec_id: Optional[str],
    query: Optional[str],
    json_out: bool,
    root: Path,
) -> None:
    root = find_root(root)
    log_path = spec_dir(root) / "log.md"

    if not log_path.exists():
        if json_out:
            typer.echo(json.dumps({"entries": [], "message": "No log found"}))
        else:
            console.print("[dim]No log yet. Lifecycle events will appear here.[/dim]")
        return

    entries = _parse_log(log_path)

    # Filter by spec_id
    if spec_id:
        padded = spec_id.zfill(4)
        entries = [e for e in entries if padded in e["body"] or spec_id in e["body"]]

    # Filter by query
    if query:
        entries = [e for e in entries if query.lower() in e["body"].lower()]

    # Most recent first, then truncate
    entries = list(reversed(entries))
    if last:
        entries = entries[:last]

    if json_out:
        typer.echo(json.dumps(entries))
        return

    if not entries:
        console.print("[dim]No log entries match your filter.[/dim]")
        return

    filter_desc = ""
    if spec_id:
        filter_desc += f"  [dim]spec:[/dim] [bold]{spec_id}[/bold]"
    if query:
        filter_desc += f"  [dim]search:[/dim] [yellow]\"{query}\"[/yellow]"

    console.print()
    console.print(Panel(
        f"[bold cyan]◈ spec log[/bold cyan]"
        f"  [dim]last {len(entries)} entries[/dim]{filter_desc}",
        box=box.ROUNDED, border_style="bright_blue", padding=(0, 2),
    ))
    console.print()

    for entry in entries:
        console.print(_render_entry(entry, query))

    console.print()
    console.print(f"  [dim]{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}[/dim]  "
                  f"[dim]full log → .spec/log.md[/dim]")
    console.print()
