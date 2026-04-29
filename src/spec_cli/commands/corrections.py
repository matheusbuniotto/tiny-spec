"""Human correction memory for improving the harness."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..storage import find_root, find_spec, spec_dir
from ..ui import console, error

CATEGORIES = {
    "missed-ac",
    "scope-creep",
    "wrong-approach",
    "weak-tests",
    "ignored-context",
    "bad-handoff",
    "spec-unclear",
    "human-preference",
}


def _path(root: Path) -> Path:
    return spec_dir(root) / "corrections.jsonl"


def write_correction(
    root: Path,
    spec,
    category: str,
    correction: str,
    human_input: str = "",
    status_before: str = "",
    status_after: str = "",
) -> dict:
    resolved_category = category if category in CATEGORIES else "human-preference"
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "spec_id": spec.id,
        "spec_title": spec.title,
        "agent": spec.agent,
        "assignee": spec.assignee,
        "category": resolved_category,
        "human_input": human_input,
        "correction": correction,
        "status_before": status_before,
        "status_after": status_after,
    }
    path = _path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")
    return record


def _read_corrections(root: Path) -> list[dict]:
    path = _path(root)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _suggestions(rows: list[dict]) -> list[str]:
    counts = Counter(row.get("category", "human-preference") for row in rows)
    suggestions = []
    if counts["missed-ac"]:
        suggestions.append(
            "Implementer prompt: before delivery, map every AC to code/test evidence."
        )
    if counts["bad-handoff"]:
        suggestions.append(
            "Deliver command/prompt: require exact test commands, results, and changed files."
        )
    if counts["weak-tests"]:
        suggestions.append(
            "Checks/templates: require at least one failure-path test for each feature spec."
        )
    if counts["spec-unclear"]:
        suggestions.append(
            "Templates: make AC and Agent Context sections more explicit before approval."
        )
    if counts["scope-creep"]:
        suggestions.append(
            "Agent context: repeat Out of Scope in task packet and delivery self-review."
        )
    return suggestions[:5]


def cmd_correction(
    spec_id: str,
    category: str,
    note: str,
    json_out: bool,
    root: Path,
) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    record = write_correction(
        root, spec, category, note, note, spec.status.value, spec.status.value
    )
    if json_out:
        typer.echo(json.dumps(record))
        return
    console.print(
        Panel(
            f"[bold]{spec.id}[/bold] — {spec.title}\n\n[dim]Category:[/dim] {record['category']}\n{note}",
            title="[bold yellow]Correction logged[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )


def cmd_corrections(
    category: Optional[str],
    agent: Optional[str],
    last: int,
    suggest: bool,
    json_out: bool,
    root: Path,
) -> None:
    root = find_root(root)
    rows = _read_corrections(root)
    if category:
        rows = [row for row in rows if row.get("category") == category]
    if agent:
        rows = [row for row in rows if row.get("agent") == agent]
    rows = rows[-last:]
    counts = Counter(row.get("category", "human-preference") for row in rows)
    data = {
        "total": len(rows),
        "counts": dict(counts),
        "corrections": rows,
        "suggestions": _suggestions(rows) if suggest else [],
    }
    if json_out:
        typer.echo(json.dumps(data))
        return

    table = Table(box=box.ROUNDED, border_style="dim", header_style="bold")
    table.add_column("Category", style="yellow")
    table.add_column("Count", justify="right")
    for name, count in counts.most_common():
        table.add_row(name, str(count))
    body = table if rows else "[dim]No corrections logged yet.[/dim]"
    console.print(
        Panel(
            body,
            title="[bold yellow]Correction patterns[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )
    if suggest:
        suggestions = _suggestions(rows)
        text = "\n".join(f"- {item}" for item in suggestions) or "[dim]No suggestions yet.[/dim]"
        console.print(
            Panel(
                text,
                title="[bold cyan]Suggested harness fixes[/bold cyan]",
                box=box.ROUNDED,
                border_style="cyan",
            )
        )
