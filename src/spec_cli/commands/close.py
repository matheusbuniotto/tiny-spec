"""Close a spec without implementing it — descoped, wont-fix, superseded, duplicate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich import box

from ..models import SpecStatus, STATUS_STYLE, CLOSE_REASONS
from ..storage import find_spec, find_root, save_spec, append_log
from ..ui import console, error

from datetime import datetime


def cmd_close(spec_id: str, reason: str, note: Optional[str], yes: bool, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    if spec.status == SpecStatus.CLOSED:
        error("Spec is already closed.", json_out, {"error": "already_closed", "id": spec_id})

    if spec.status == SpecStatus.IMPLEMENTED:
        error(
            "Cannot close an already-implemented spec.",
            json_out, {"error": "already_implemented", "id": spec_id},
        )

    if reason not in CLOSE_REASONS:
        valid = ", ".join(CLOSE_REASONS)
        error(
            f"Invalid reason '{reason}'. Valid: {valid}",
            json_out, {"error": "invalid_reason", "valid": list(CLOSE_REASONS)},
        )

    resolved_note = note or ""
    if not resolved_note and not yes and not json_out:
        import questionary
        style = questionary.Style([("question", "bold cyan"), ("answer", "bold white")])
        resolved_note = questionary.text(
            f"Close note (why is this being {reason}?):", style=style
        ).ask() or ""

    old_status = spec.status
    spec.status = SpecStatus.CLOSED
    spec.updated_at = datetime.utcnow()
    if resolved_note:
        close_line = f"[closed: {reason}] {resolved_note}"
        spec.gate_notes = (spec.gate_notes.rstrip() + f"\n\n---\n{close_line}") if spec.gate_notes else close_line

    save_spec(spec, root)
    append_log(root, f"✕ CLOSED `{spec.id}` **{spec.title}** ({reason}){' — ' + resolved_note if resolved_note else ''}")

    from ..config import load_config
    cfg = load_config(root)
    git_sha = None
    if cfg.git_auto_commit:
        try:
            from ..integrations.git import git_commit_spec, git_add_specs
            git_add_specs(root)
            git_sha = git_commit_spec(root, f"spec({spec.id}): close [{reason}] — {spec.title}")
        except Exception:
            pass

    if json_out:
        out = spec.to_dict()
        out["close_reason"] = reason
        if git_sha:
            out["git_commit"] = git_sha
        typer.echo(json.dumps(out))
        return

    old_icon, old_color = STATUS_STYLE[old_status]
    git_line = f"\n  [dim]Git:[/dim] [green]{git_sha}[/green]" if git_sha else ""
    console.print(Panel(
        f"[bold]{spec.id}[/bold] — {spec.title}\n\n"
        f"  [{old_color}]{old_icon} {old_status.value}[/{old_color}]"
        f"  [dim]→[/dim]  "
        f"[dim]✕ closed ({reason})[/dim]"
        f"{git_line}"
        + (f"\n  [dim]Note:[/dim] {resolved_note}" if resolved_note else ""),
        title="[bold dim]Spec closed[/bold dim]",
        box=box.ROUNDED, border_style="dim",
    ))
