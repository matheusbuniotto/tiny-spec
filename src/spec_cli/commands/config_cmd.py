from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table
from rich import box

from ..config import load_config
from ..storage import find_root
from ..ui import console


def cmd_config_show(json_out: bool, root: Path) -> None:
    root = find_root(root)
    cfg = load_config(root)

    if json_out:
        typer.echo(json.dumps({
            "author": cfg.author, "ai_provider": cfg.ai_provider,
            "ai_model": cfg.ai_model, "ai_base_url": cfg.ai_base_url,
            "default_template": cfg.default_template,
            "project_name": cfg.project_name, "description": cfg.description,
            "languages": cfg.languages, "frameworks": cfg.frameworks,
            "libraries": cfg.libraries, "testing": cfg.testing,
            "architecture": cfg.architecture, "conventions": cfg.conventions,
            "out_of_bounds": cfg.out_of_bounds,
        }))
        return

    table = Table(box=box.ROUNDED, border_style="dim", show_header=False, pad_edge=True)
    table.add_column("Key", style="bold cyan", no_wrap=True)
    table.add_column("Value")

    def row(k, v):
        if isinstance(v, list):
            v = ", ".join(v) if v else "[dim]—[/dim]"
        elif not v:
            v = "[dim]—[/dim]"
        table.add_row(k, str(v))

    row("author", cfg.author)
    row("ai_provider", cfg.ai_provider)
    row("ai_model", cfg.ai_model or "(default)")
    row("default_template", cfg.default_template)
    table.add_section()
    row("project_name", cfg.project_name)
    row("description", cfg.description)
    row("languages", cfg.languages)
    row("frameworks", cfg.frameworks)
    row("libraries", cfg.libraries)
    row("testing", cfg.testing)
    row("architecture", cfg.architecture)
    row("conventions", cfg.conventions)
    row("out_of_bounds", cfg.out_of_bounds)

    console.print(Panel(table, title="[bold].spec/config.yaml[/bold]", box=box.ROUNDED, border_style="bright_blue"))
