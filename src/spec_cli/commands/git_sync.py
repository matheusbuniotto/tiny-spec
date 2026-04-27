"""Manual git sync command — commit all .spec/ changes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from ..integrations.git import is_git_repo, git_commit_spec, git_status_summary, git_context_markdown
from ..storage import find_root
from ..ui import console, error


def _refresh_git_context(root: Path) -> bool:
    """Regenerate .spec/git-context.md. Returns True if content changed."""
    ctx_path = root / ".spec" / "git-context.md"
    new_content = git_context_markdown(root)
    if not new_content:
        return False
    old_content = ctx_path.read_text() if ctx_path.exists() else ""
    if old_content == new_content:
        return False
    ctx_path.write_text(new_content)
    return True


def cmd_sync(message: Optional[str], json_out: bool, root: Path) -> None:
    root = find_root(root)

    if not is_git_repo(root):
        error(
            "Not a git repository. Run [cyan]git init[/cyan] first.",
            json_out, {"error": "not_git_repo"},
        )

    # Refresh git context before checking status
    _refresh_git_context(root)

    status = git_status_summary(root)
    if status == "clean":
        if json_out:
            typer.echo(json.dumps({"status": "clean", "committed": False}))
        else:
            console.print("[dim]Nothing to commit — .spec/ is clean.[/dim]")
        return

    commit_msg = message or "spec: sync .spec/ changes"
    sha = git_commit_spec(root, commit_msg)

    if json_out:
        typer.echo(json.dumps({"status": "committed", "sha": sha, "message": commit_msg}))
    else:
        if sha:
            console.print(f"[green]✓[/green] Committed .spec/ changes — [green]{sha}[/green]")
        else:
            console.print("[yellow]⚠ Nothing was committed (changes may already be staged elsewhere).[/yellow]")


def cmd_git_context(json_out: bool, root: Path) -> None:
    """Refresh .spec/git-context.md and display a summary."""
    root = find_root(root)

    if not is_git_repo(root):
        error(
            "Not a git repository. Run [cyan]git init[/cyan] first.",
            json_out, {"error": "not_git_repo"},
        )

    from ..integrations.git import git_recent_commits
    commits = git_recent_commits(root, n=10)
    ctx_path = root / ".spec" / "git-context.md"
    new_content = git_context_markdown(root, commits=commits)
    if new_content and ctx_path.exists():
        ctx_path.write_text(new_content)

    if json_out:
        typer.echo(json.dumps({"commits": commits, "written": str(ctx_path)}))
        return

    if not commits:
        console.print("[dim]No commits found in this repository yet.[/dim]")
        return

    from rich.table import Table
    from rich import box as rbox
    table = Table(box=rbox.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("SHA", style="green", no_wrap=True)
    table.add_column("Date", style="dim", no_wrap=True)
    table.add_column("Author", style="cyan")
    table.add_column("Message")
    for c in commits:
        table.add_row(c["sha"], c["date"], c["author"], c["subject"])

    console.print(table)
    if new_content:
        console.print(f"[dim]↳ Context written to[/dim] [cyan]{ctx_path}[/cyan]")
