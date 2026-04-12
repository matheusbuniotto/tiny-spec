"""Full-text search across spec titles and bodies."""
from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich import box

from ..models import SpecStatus, STATUS_STYLE
from ..storage import list_specs, find_root
from ..ui import console, error


def _highlight(text: str, query: str, style: str = "bold yellow") -> Text:
    """Return a Rich Text with all occurrences of query highlighted."""
    t = Text()
    lower_text = text.lower()
    lower_q = query.lower()
    pos = 0
    while True:
        idx = lower_text.find(lower_q, pos)
        if idx == -1:
            t.append(text[pos:])
            break
        t.append(text[pos:idx])
        t.append(text[idx:idx + len(query)], style=style)
        pos = idx + len(query)
    return t


def _excerpt(body: str, query: str, context: int = 120) -> str:
    """Extract a short excerpt around the first match in body."""
    lower_body = body.lower()
    lower_q = query.lower()
    idx = lower_body.find(lower_q)
    if idx == -1:
        return ""
    start = max(0, idx - context // 2)
    end = min(len(body), idx + len(query) + context // 2)
    snippet = body[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(body):
        snippet = snippet + "…"
    return snippet


def cmd_search(query: str, status: str | None, json_out: bool, root: Path) -> None:
    root = find_root(root)

    if not query.strip():
        error("Search query cannot be empty.", json_out, {"error": "empty_query"})

    filter_status = None
    if status:
        try:
            filter_status = SpecStatus(status)
        except ValueError:
            valid = ", ".join(s.value for s in SpecStatus)
            error(f"Invalid status. Valid: {valid}", json_out, {"error": "invalid_status"})

    specs = list_specs(root, filter_status)
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    results = []
    for spec in specs:
        title_match = bool(pattern.search(spec.title))
        body_match = bool(pattern.search(spec.body))
        if title_match or body_match:
            results.append({
                "spec": spec,
                "title_match": title_match,
                "body_match": body_match,
                "excerpt": _excerpt(spec.body, query) if body_match else "",
            })

    # Title matches first, then body-only
    results.sort(key=lambda r: (0 if r["title_match"] else 1, r["spec"].id))

    if json_out:
        typer.echo(json.dumps([{
            **r["spec"].to_dict(include_body=False),
            "title_match": r["title_match"],
            "body_match": r["body_match"],
            "excerpt": r["excerpt"],
        } for r in results]))
        return

    console.print()
    if not results:
        console.print(Panel(
            f"[dim]No specs found matching[/dim] [bold yellow]\"{query}\"[/bold yellow]",
            box=box.ROUNDED, border_style="dim",
        ))
        return

    match_word = "match" if len(results) == 1 else "matches"
    console.print(Panel(
        f"[bold yellow]🔍 \"{query}\"[/bold yellow]  [dim]— {len(results)} {match_word}[/dim]"
        + (f"  [dim]in status:[/dim] [cyan]{status}[/cyan]" if status else ""),
        box=box.ROUNDED, border_style="yellow", padding=(0, 2),
    ))
    console.print()

    for r in results:
        spec = r["spec"]
        icon, color = STATUS_STYLE[spec.status]

        # Build title line with highlight
        title_text = _highlight(spec.title, query) if r["title_match"] else Text(spec.title)
        header = Text()
        header.append(f"{spec.id}", style="bold dim")
        header.append("  ")
        header.append(f"{icon} {spec.status.value}", style=color)
        header.append("  ")
        header.append(title_text)

        body_parts: list = [header]

        if r["excerpt"]:
            excerpt_text = Text("  ")
            excerpt_text.append(_highlight(r["excerpt"], query, style="bold yellow on grey15"))
            body_parts.append(excerpt_text)

        match_badges = []
        if r["title_match"]:
            match_badges.append("[yellow]title[/yellow]")
        if r["body_match"]:
            match_badges.append("[dim]body[/dim]")

        footer = Text(f"  matched in: {' · '.join(match_badges)}  ", style="dim")
        footer.append(f"spec show {spec.id}", style="cyan")
        body_parts.append(footer)

        from rich.console import Group
        console.print(Panel(
            Group(*body_parts),
            box=box.ROUNDED,
            border_style=color,
            padding=(0, 2),
        ))

    console.print(f"\n  [dim]{len(results)} result{'s' if len(results) != 1 else ''} for[/dim] [yellow]\"{query}\"[/yellow]\n")
