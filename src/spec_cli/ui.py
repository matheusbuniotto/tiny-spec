"""Shared UI helpers — one place for console, panels, errors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NoReturn

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

from .models import SpecStatus
from .storage import find_root, spec_dir

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


def find_root_or_error(root: Path, json_out: bool) -> Path:
    """find_root, but errors clearly instead of silently treating an uninitialized
    directory as an empty project — the ambiguity `spec list`/`spec show`/etc. used
    to have, mirrored across every read command except `spec new`."""
    resolved = find_root(root)
    if not spec_dir(resolved).exists():
        error(
            "Not initialized. Run [cyan]spec init[/cyan] first.",
            json_out,
            {"error": "not_initialized"},
        )
    return resolved


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


def worktree_reminder_fields(path: str) -> dict:
    """JSON fields for a leftover-worktree reminder on a terminal transition."""
    return {"worktree": path, "worktree_remove_hint": f"git worktree remove {path}"}


def print_worktree_reminder(path: str) -> None:
    console.print(
        f"\n  [yellow]⚠ Worktree still exists:[/yellow] {path}\n"
        f"  [dim]Remove it:[/dim] [cyan]git worktree remove {path}[/cyan]\n"
    )
