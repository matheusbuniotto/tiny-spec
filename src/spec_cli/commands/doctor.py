"""Read-only readiness checks for the agentic harness."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..config import load_config
from ..integrations.git import is_git_repo
from ..storage import find_root, spec_dir
from ..ui import console


def _constitution_status(root: Path) -> tuple[str, str]:
    path = spec_dir(root) / "constitution.md"
    if not path.exists():
        return "warn", "missing .spec/constitution.md"
    text = path.read_text(encoding="utf-8").strip()
    placeholder_bits = [
        "Define your project's governing principles",
        "## Principles\n\n-",
        "## Standards\n\n-",
    ]
    if len(text) < 120 or any(bit in text for bit in placeholder_bits):
        return "warn", "constitution looks sparse or placeholder-like"
    return "ok", "constitution has project-specific content"


def _project_context_status(root: Path) -> tuple[str, str]:
    cfg = load_config(root)
    filled = [
        bool(cfg.project_name),
        bool(cfg.description),
        bool(cfg.languages),
        bool(cfg.frameworks),
        bool(cfg.testing),
        bool(cfg.conventions),
        bool(cfg.out_of_bounds),
    ]
    count = sum(filled)
    if count >= 3:
        return "ok", f"{count} project context fields filled"
    return "warn", f"only {count} project context fields filled"


def _checks_status(root: Path) -> tuple[str, str]:
    cfg = load_config(root)
    if cfg.checks:
        names = ", ".join(c.name for c in cfg.checks)
        return "ok", f"configured: {names}"
    return "warn", "no checks configured; run spec setup-checks"


def _claude_status(root: Path) -> tuple[str, str]:
    skill = root / ".claude" / "skills" / "spec" / "SKILL.md"
    claude_md = root / "CLAUDE.md"
    if skill.exists() and claude_md.exists():
        return "ok", "CLAUDE.md and spec skill installed"
    if skill.exists() or claude_md.exists():
        return "warn", "partial Claude setup"
    return "warn", "Claude docs/skill not installed"


def cmd_doctor(json_out: bool, root: Path) -> None:
    root = find_root(root)
    checks = {
        "spec_dir": ("ok", ".spec exists")
        if spec_dir(root).exists()
        else ("error", ".spec missing"),
        "git_repo": ("ok", "git repo detected")
        if is_git_repo(root)
        else ("warn", "not a git repo"),
        "checks_configured": _checks_status(root),
        "constitution": _constitution_status(root),
        "project_context": _project_context_status(root),
        "claude_setup": _claude_status(root),
    }
    next_actions = []
    if checks["checks_configured"][0] != "ok":
        next_actions.append("spec setup-checks")
    if checks["constitution"][0] != "ok":
        next_actions.append("edit .spec/constitution.md")
    if checks["project_context"][0] != "ok":
        next_actions.append("edit .spec/config.yaml")

    ok = all(status != "error" for status, _ in checks.values())
    data = {
        "ok": ok,
        "checks": {
            name: {"status": status, "message": message}
            for name, (status, message) in checks.items()
        },
        "next_actions": next_actions,
    }
    if json_out:
        typer.echo(json.dumps(data))
        return

    table = Table(box=box.ROUNDED, border_style="dim", header_style="bold")
    table.add_column("Check")
    table.add_column("Status", width=8)
    table.add_column("Message")
    for name, (status, message) in checks.items():
        icon = "✓ ok" if status == "ok" else "⚠ warn" if status == "warn" else "✕ error"
        style = "bright_green" if status == "ok" else "yellow" if status == "warn" else "red"
        table.add_row(name, f"[{style}]{icon}[/{style}]", message)
    next_text = "\n".join(f"- {item}" for item in next_actions) or "[dim]none[/dim]"
    console.print(
        Panel(
            table,
            title="[bold cyan]tiny-spec doctor[/bold cyan]",
            box=box.ROUNDED,
            border_style="cyan",
        )
    )
    console.print(
        Panel(next_text, title="[bold]Next actions[/bold]", box=box.ROUNDED, border_style="dim")
    )
