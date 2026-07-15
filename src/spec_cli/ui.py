"""Shared UI helpers — one place for console, panels, errors."""

from __future__ import annotations

import json
from typing import NoReturn

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

from .models import SpecStatus

console = Console()
err_console = Console(stderr=True)

# Bodies above this size get truncated in payloads that dump many specs at once
# (list --full, export) so agents don't blow their context on one giant call.
# ponytail: fixed budget well above a normal scaffolded spec body (~2-3k chars);
# raise if real specs start legitimately exceeding it.
BODY_TRUNCATE_LIMIT = 8000

# Single concrete --json command to run next, given a spec's current status.
# One source of truth for next/show/advance/claim's help[] suggestions —
# each command template is one runnable command, never two joined by "then".
_NEXT_COMMAND: dict[SpecStatus, str] = {
    SpecStatus.DRAFT: "spec advance {id} --yes --json",
    SpecStatus.APPROVED: "spec advance {id} --yes --json",
    SpecStatus.IN_PROGRESS: 'spec advance {id} --note "<summary>" --yes --json',
    SpecStatus.AT_GATE: "spec gate-check {id} --json",
    SpecStatus.IMPLEMENTED: "spec next --json",
    SpecStatus.CLOSED: "spec next --json",
}


def next_command(status: SpecStatus, spec_id: str) -> str:
    """The single next command to suggest for a spec in this status."""
    return _NEXT_COMMAND.get(status, "spec next --json").format(id=spec_id)


def success(title: str, body: str, border: str = "bright_green") -> None:
    console.print(
        Panel(
            body,
            title=f"[bold {border}]{title}[/bold {border}]",
            box=box.ROUNDED,
            border_style=border,
        )
    )


def info(title: str, body: str, border: str = "bright_blue") -> None:
    console.print(Panel(body, title=f"[bold]{title}[/bold]", box=box.ROUNDED, border_style=border))


def error(msg: str, json_out: bool = False, data: dict | None = None) -> NoReturn:
    if json_out:
        typer.echo(json.dumps(data or {"error": msg}))
    else:
        err_console.print(f"[red][!][/red] {msg}")
    raise typer.Exit(1)


def not_found(spec_id: str, json_out: bool) -> NoReturn:
    """Standard not-found error for any command that resolves a spec by id."""
    error(
        f"Spec not found: {spec_id}",
        json_out,
        {"error": "not_found", "id": spec_id, "help": ["spec list"]},
    )


def json_or(data, render_fn, json_out: bool) -> None:
    """If json_out, dump data. Otherwise call render_fn()."""
    if json_out:
        typer.echo(json.dumps(data() if callable(data) else data))
    else:
        render_fn()


def with_help(data: dict, *suggestions: str) -> dict:
    """Attach a help[] array of concrete next-command suggestions (additive-only)."""
    return {**data, "help": [s for s in suggestions if s]}


def truncate_body(body: str, spec_id: str, limit: int = BODY_TRUNCATE_LIMIT) -> str:
    """Truncate a long spec body for multi-spec payloads, with a pointer to the full version."""
    if len(body) <= limit:
        return body
    return f"{body[:limit]}\n\n(truncated, {len(body)} chars — use spec show {spec_id} --json)"
