"""Atomically claim an approved spec: assign to self and start work."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from rich import box
from rich.panel import Panel

from ..config import load_config
from ..integrations.git import git_worktree_add
from ..models import SpecStatus
from ..state import transition
from ..storage import find_spec, list_specs, open_blockers, save_spec, slugify
from ..ui import console, error, find_root_or_error, next_command, not_found, with_help


def _worktree_path(root: Path, spec_id: str) -> Path:
    return root.resolve().parent / f"{root.resolve().name}-spec-{spec_id}"


def _branch_name(spec_id: str, title: str) -> str:
    return f"spec/{spec_id}-{slugify(title)}"


_WORKTREE_HINT = "Run your install step in the new worktree — dependencies aren't shared."


def _claim_worktree(root: Path, spec) -> dict:
    """Create (or reuse) an isolated worktree for this spec. Returns fields to merge into output."""
    path = _worktree_path(root, spec.id)
    branch = _branch_name(spec.id, spec.title)
    result = git_worktree_add(root, path, branch)
    if result["error"]:
        return {"worktree_error": result["error"]}
    return {"worktree": str(path), "branch": branch, "worktree_hint": _WORKTREE_HINT}


def _worktree_panel_line(wt_fields: dict) -> str:
    """Human-output line for a worktree result — success, failure, or nothing (flag unset)."""
    if wt_fields.get("worktree_error"):
        return f"\n[red]⚠ Worktree creation failed:[/red] {wt_fields['worktree_error']}"
    if wt_fields:
        return f"\n[dim]Worktree:[/dim] {wt_fields['worktree']}\n[dim]{wt_fields['worktree_hint']}[/dim]"
    return ""


def cmd_claim(
    spec_id: str, agent_name: str, yes: bool, json_out: bool, root: Path, worktree: bool = False
) -> None:
    root = find_root_or_error(root, json_out)
    spec = find_spec(root, spec_id)
    if not spec:
        not_found(spec_id, json_out)

    # Resolve agent name: --as flag > $SPEC_AGENT > "agent"
    if not agent_name:
        agent_name = os.environ.get("SPEC_AGENT", "agent")

    # Idempotent re-claim by same agent
    if spec.status == SpecStatus.IN_PROGRESS and spec.assignee == agent_name:
        wt_fields = _claim_worktree(root, spec) if worktree else {}
        if json_out:
            help_cmd = next_command(spec.status, spec.id)
            typer.echo(
                json.dumps(
                    with_help(
                        {"claimed": True, "idempotent": True, **spec.to_dict(), **wt_fields},
                        help_cmd,
                    )
                )
            )
        else:
            wt_line = _worktree_panel_line(wt_fields)
            console.print(
                Panel(
                    f"[bold]{spec.id}[/bold] — {spec.title}\n"
                    f"[dim]Already claimed by [cyan]{agent_name}[/cyan] and in progress.[/dim]"
                    f"{wt_line}",
                    title="[bold cyan]Already claimed[/bold cyan]",
                    box=box.ROUNDED,
                    border_style="cyan",
                )
            )
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

    blockers = open_blockers(spec, list_specs(root))
    if blockers:
        ids = ", ".join(b.id for b in blockers)
        error(
            f"Spec {spec.id} is blocked by {ids} — not implemented/closed yet",
            json_out,
            {
                "error": "blocked",
                "id": spec.id,
                "blocked_by": [b.id for b in blockers],
                "hint": "Finish or close the blocking specs first, or edit blocked_by if this is stale.",
            },
        )

    # Assign before transition so assignee is persisted in the commit
    spec.assignee = agent_name

    cfg = load_config(root)
    spec, git_sha = transition(
        spec,
        SpecStatus.IN_PROGRESS,
        root,
        notes=f"Claimed by {agent_name}",
        auto_commit=cfg.git_auto_commit,
    )

    wt_fields = _claim_worktree(root, spec) if worktree else {}

    if json_out:
        out = spec.to_dict()
        out["claimed"] = True
        if git_sha:
            out["git_sha"] = git_sha
        out.update(wt_fields)
        help_cmd = next_command(spec.status, spec.id)
        typer.echo(json.dumps(with_help(out, help_cmd)))
        return

    wt_line = _worktree_panel_line(wt_fields)
    console.print(
        Panel(
            f"[bold]{spec.id}[/bold] — {spec.title}\n"
            f"[cyan]▶ in-progress[/cyan]  assigned to [cyan]{agent_name}[/cyan]\n"
            f"{wt_line}\n"
            f'[dim]When done:[/dim] [cyan]spec advance {spec.id} --note "<summary>" --yes --json[/cyan]',
            title="[bold cyan]Claimed[/bold cyan]",
            box=box.ROUNDED,
            border_style="cyan",
        )
    )
