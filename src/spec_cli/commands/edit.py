"""Open a spec file in $EDITOR."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import typer

from ..storage import find_spec, find_root
from ..ui import console, error


def cmd_edit(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    if not spec.file_path:
        error("Spec has no file path.", json_out, {"error": "no_file_path"})

    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", ""))
    if not editor:
        if json_out:
            typer.echo(json.dumps({"file_path": spec.file_path}))
        else:
            console.print(f"[yellow]$EDITOR not set.[/yellow] Open manually: [cyan]{spec.file_path}[/cyan]")
        return

    if json_out:
        typer.echo(json.dumps({"file_path": spec.file_path, "editor": editor}))
        return

    console.print(f"[dim]Opening[/dim] [cyan]{spec.file_path}[/cyan] [dim]in {editor}...[/dim]")
    subprocess.run([editor, spec.file_path])
