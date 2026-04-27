"""Scan the project and auto-configure pre-gate checks in config.yaml."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table
from rich import box

from ..config import load_config, save_config, Check
from ..ui import console, success, error


# Each detector: (name, description, detect_fn, command)
# detect_fn takes root Path, returns True if this tool is present

def _has_file(root: Path, *names: str) -> bool:
    return any((root / n).exists() for n in names)


def _has_dep(root: Path, dep: str) -> bool:
    """Check if dep appears in pyproject.toml, package.json, or requirements*.txt."""
    for f in ["pyproject.toml", "setup.cfg", "setup.py"]:
        p = root / f
        if p.exists() and dep in p.read_text():
            return True
    for f in root.glob("requirements*.txt"):
        if dep in f.read_text():
            return True
    pkg = root / "package.json"
    if pkg.exists() and dep in pkg.read_text():
        return True
    return False


def _cmd_exists(cmd: str) -> bool:
    """Check if a command is available on PATH."""
    try:
        subprocess.run(
            ["which", cmd], capture_output=True, timeout=5
        )
        return True
    except Exception:
        return False


# Detectors ordered by priority (tests first, then lint, then types)
_DETECTORS: list[dict] = [
    # Python tests
    {
        "name": "tests",
        "description": "Test suite must pass",
        "detect": lambda r: _has_dep(r, "pytest") or (r / "pytest.ini").exists() or (r / "conftest.py").exists(),
        "command": "pytest",
        "category": "test",
    },
    {
        "name": "tests",
        "description": "Test suite must pass",
        "detect": lambda r: (r / "manage.py").exists() and _has_dep(r, "django"),
        "command": "python manage.py test",
        "category": "test",
    },
    # JS/TS tests
    {
        "name": "tests",
        "description": "Test suite must pass",
        "detect": lambda r: _has_dep(r, "vitest"),
        "command": "npx vitest run",
        "category": "test",
    },
    {
        "name": "tests",
        "description": "Test suite must pass",
        "detect": lambda r: _has_dep(r, "jest"),
        "command": "npx jest",
        "category": "test",
    },
    {
        "name": "tests",
        "description": "Test suite must pass",
        "detect": lambda r: _has_dep(r, "mocha"),
        "command": "npx mocha",
        "category": "test",
    },
    # Go tests
    {
        "name": "tests",
        "description": "Test suite must pass",
        "detect": lambda r: (r / "go.mod").exists(),
        "command": "go test ./...",
        "category": "test",
    },
    # Rust tests
    {
        "name": "tests",
        "description": "Test suite must pass",
        "detect": lambda r: (r / "Cargo.toml").exists(),
        "command": "cargo test",
        "category": "test",
    },
    # Python linters
    {
        "name": "lint",
        "description": "No linting errors",
        "detect": lambda r: _has_dep(r, "ruff") or (r / "ruff.toml").exists(),
        "command": "ruff check .",
        "category": "lint",
    },
    {
        "name": "lint",
        "description": "No linting errors",
        "detect": lambda r: _has_dep(r, "flake8") or (r / ".flake8").exists(),
        "command": "flake8 .",
        "category": "lint",
    },
    # JS/TS linters
    {
        "name": "lint",
        "description": "No linting errors",
        "detect": lambda r: _has_file(r, ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml", "eslint.config.js", "eslint.config.mjs") or _has_dep(r, "eslint"),
        "command": "npx eslint .",
        "category": "lint",
    },
    # Go lint
    {
        "name": "lint",
        "description": "No linting errors",
        "detect": lambda r: (r / "go.mod").exists() and _has_file(r, ".golangci.yml", ".golangci.yaml"),
        "command": "golangci-lint run",
        "category": "lint",
    },
    # Rust lint
    {
        "name": "lint",
        "description": "No linting errors",
        "detect": lambda r: (r / "Cargo.toml").exists(),
        "command": "cargo clippy -- -D warnings",
        "category": "lint",
    },
    # Python type checking
    {
        "name": "typecheck",
        "description": "No type errors",
        "detect": lambda r: _has_dep(r, "mypy") or (r / "mypy.ini").exists(),
        "command": "mypy .",
        "category": "typecheck",
    },
    {
        "name": "typecheck",
        "description": "No type errors",
        "detect": lambda r: _has_dep(r, "pyright") or (r / "pyrightconfig.json").exists(),
        "command": "pyright",
        "category": "typecheck",
    },
    # JS/TS type checking
    {
        "name": "typecheck",
        "description": "No type errors",
        "detect": lambda r: (r / "tsconfig.json").exists(),
        "command": "npx tsc --noEmit",
        "category": "typecheck",
    },
    # Formatting
    {
        "name": "format",
        "description": "Code is formatted",
        "detect": lambda r: _has_dep(r, "ruff") or (r / "ruff.toml").exists(),
        "command": "ruff format --check .",
        "category": "format",
    },
    {
        "name": "format",
        "description": "Code is formatted",
        "detect": lambda r: _has_dep(r, "prettier") or _has_file(r, ".prettierrc", ".prettierrc.js", ".prettierrc.json"),
        "command": "npx prettier --check .",
        "category": "format",
    },
    {
        "name": "format",
        "description": "Code is formatted",
        "detect": lambda r: (r / "Cargo.toml").exists(),
        "command": "cargo fmt -- --check",
        "category": "format",
    },
    # Build check
    {
        "name": "build",
        "description": "Project builds without errors",
        "detect": lambda r: (r / "Cargo.toml").exists(),
        "command": "cargo build",
        "category": "build",
    },
    {
        "name": "build",
        "description": "Project builds without errors",
        "detect": lambda r: (r / "go.mod").exists(),
        "command": "go build ./...",
        "category": "build",
    },
]


def _detect_checks(root: Path) -> list[Check]:
    """Scan project and return detected checks, one per category."""
    seen_categories: set[str] = set()
    results: list[Check] = []

    for d in _DETECTORS:
        cat = d["category"]
        if cat in seen_categories:
            continue
        try:
            if d["detect"](root):
                results.append(Check(name=d["name"], command=d["command"], description=d["description"]))
                seen_categories.add(cat)
        except Exception:
            continue

    return results


def cmd_setup_checks(yes: bool, json_out: bool, root: Path) -> None:
    from ..storage import find_root
    root = find_root(root)
    cfg = load_config(root)

    detected = _detect_checks(root)

    if not detected:
        if json_out:
            typer.echo(json.dumps({"detected": [], "written": False, "message": "No checks detected"}))
        else:
            console.print(
                "[dim]No test/lint/typecheck tools detected.[/dim]\n\n"
                "[dim]Manually add checks to[/dim] [cyan].spec/config.yaml[/cyan]:\n\n"
                "[dim]checks:\n"
                "  - name: tests\n"
                "    command: pytest\n"
                "    description: Test suite must pass[/dim]"
            )
        return

    if json_out:
        if cfg.checks and not yes:
            typer.echo(json.dumps({
                "detected": [c.to_dict() for c in detected],
                "existing": [c.to_dict() for c in cfg.checks],
                "written": False,
                "message": "Checks already configured. Use --yes to overwrite.",
            }))
            return

        cfg.checks = detected
        save_config(cfg, root)
        typer.echo(json.dumps({
            "detected": [c.to_dict() for c in detected],
            "written": True,
        }))
        return

    # Human-facing output
    table = Table(box=box.ROUNDED, border_style="dim", header_style="bold")
    table.add_column("Check", style="bold", min_width=12)
    table.add_column("Command", style="cyan", min_width=20)
    table.add_column("Description", style="dim")

    for c in detected:
        table.add_row(c.name, c.command, c.description)

    console.print(Panel(
        table,
        title="[bold bright_blue]Detected checks[/bold bright_blue]",
        box=box.ROUNDED, border_style="bright_blue",
    ))

    if cfg.checks:
        existing_cmds = ", ".join(c.command for c in cfg.checks)
        console.print(f"\n[yellow]Existing checks:[/yellow] {existing_cmds}")

    if not yes:
        import questionary
        style = questionary.Style([("question", "bold cyan"), ("answer", "bold white")])
        do_write = questionary.confirm(
            "Write these checks to .spec/config.yaml?",
            default=True, style=style,
        ).ask()
        if not do_write:
            console.print("[dim]Cancelled.[/dim]")
            return

    cfg.checks = detected
    save_config(cfg, root)
    success("checks", (
        f"[bright_green]Wrote {len(detected)} check{'s' if len(detected) != 1 else ''}[/bright_green] "
        f"to [cyan].spec/config.yaml[/cyan]\n\n"
        f"  [dim]Run them:[/dim] [cyan]spec run-checks[/cyan]\n"
        f"  [dim]They auto-run before[/dim] [magenta]at-gate[/magenta]"
    ), border="bright_blue")
