"""Atomically claim an approved spec: assign to self and start work."""
from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from rich.panel import Panel
from rich import box

from ..models import SpecStatus
from ..storage import find_spec, find_root, save_spec
from ..state import transition
from ..config import load_config
from ..ui import console, error


def cmd_claim(spec_id: str, agent_name: str, yes: bool, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    # Resolve agent name: --as flag > $SPEC_AGENT > "agent"
    if not agent_name:
        agent_name = os.environ.get("SPEC_AGENT", "agent")

    # Idempotent re-claim by same agent
    if spec.status == SpecStatus.IN_PROGRESS and spec.assignee == agent_name:
        if json_out:
            typer.echo(json.dumps({"claimed": True, "idempotent": True, **spec.to_dict()}))
        else:
            console.print(Panel(
                f"[bold]{spec.id}[/bold] — {spec.title}\n"
                f"[dim]Already claimed by [cyan]{agent_name}[/cyan] and in progress.[/dim]",
                title="[bold cyan]Already claimed[/bold cyan]",
                box=box.ROUNDED, border_style="cyan",
            ))
        return

    # Claimed by someone else
    if spec.status == SpecStatus.IN_PROGRESS and spec.assignee != agent_name:
        error(
            f"Spec {spec.id} is already in-progress and claimed by '{spec.assignee}'",
            json_out,
            {"error": "already_claimed", "id": spec.id, "assignee": spec.assignee},
        )

    # Wrong state
    if spec.status != SpecStatus.APPROVED:
        error(
            f"Spec {spec.id} is '{spec.status.value}' — only approved specs can be claimed",
            json_out,
            {
                "error": "not_claimable",
                "id": spec.id,
                "status": spec.status.value,
                "hint": "Only approved specs can be claimed. Use 'spec advance <id>' to approve first.",
            },
        )

    # Assign before transition so assignee is persisted in the commit
    spec.assignee = agent_name

    cfg = load_config(root)
    spec, git_sha = transition(
        spec, SpecStatus.IN_PROGRESS, root,
        notes=f"Claimed by {agent_name}",
        auto_commit=cfg.git_auto_commit,
    )

    if json_out:
        out = spec.to_dict()
        out["claimed"] = True
        if git_sha:
            out["git_sha"] = git_sha
        typer.echo(json.dumps(out))
        return

    console.print(Panel(
        f"[bold]{spec.id}[/bold] — {spec.title}\n"
        f"[cyan]▶ in-progress[/cyan]  assigned to [cyan]{agent_name}[/cyan]\n\n"
        f"[dim]When done:[/dim] [cyan]spec advance {spec.id} --note \"<summary>\" --yes --json[/cyan]",
        title="[bold cyan]Claimed[/bold cyan]",
        box=box.ROUNDED, border_style="cyan",
    ))
