"""Shared UI helpers — one place for console, panels, errors."""
from __future__ import annotations

import json
from datetime import datetime
from typing import NoReturn

import typer
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()
err_console = Console(stderr=True)


def success(title: str, body: str, border: str = "bright_green") -> None:
    console.print(Panel(body, title=f"[bold {border}]{title}[/bold {border}]", box=box.ROUNDED, border_style=border))


def info(title: str, body: str, border: str = "bright_blue") -> None:
    console.print(Panel(body, title=f"[bold]{title}[/bold]", box=box.ROUNDED, border_style=border))


def error(msg: str, json_out: bool = False, data: dict | None = None) -> NoReturn:
    if json_out:
        typer.echo(json.dumps(data or {"error": msg}))
    else:
        err_console.print(f"[red][!][/red] {msg}")
    raise typer.Exit(1)


def json_or(data, render_fn, json_out: bool) -> None:
    """If json_out, dump data. Otherwise call render_fn()."""
    if json_out:
        typer.echo(json.dumps(data() if callable(data) else data))
    else:
        render_fn()


def age_days(dt: datetime) -> int:
    return (datetime.utcnow() - dt).days
