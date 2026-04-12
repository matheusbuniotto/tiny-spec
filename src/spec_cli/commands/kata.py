"""Kata harness — run named verification scripts before a spec can enter at-gate."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table
from rich import box

from ..config import load_config, Kata
from ..storage import find_spec, find_root
from ..ui import console, error


def run_kata(kata: Kata, root: Path) -> dict:
    """Execute a single kata. Returns a result dict."""
    start = time.monotonic()
    try:
        result = subprocess.run(
            kata.command,
            shell=True,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300,
        )
        elapsed = time.monotonic() - start
        passed = result.returncode == 0
        return {
            "name": kata.name,
            "command": kata.command,
            "description": kata.description,
            "passed": passed,
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "elapsed_s": round(elapsed, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "name": kata.name,
            "command": kata.command,
            "description": kata.description,
            "passed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Kata timed out after 300s",
            "elapsed_s": 300.0,
        }
    except Exception as e:
        return {
            "name": kata.name,
            "command": kata.command,
            "description": kata.description,
            "passed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "elapsed_s": 0.0,
        }


def run_katas_for_spec(root: Path, spec_id: Optional[str] = None) -> tuple[list[dict], bool]:
    """
    Run all configured katas.
    Returns (results, all_passed).
    spec_id is used only for display context.
    """
    cfg = load_config(root)
    if not cfg.katas:
        return [], True

    results = []
    for kata in cfg.katas:
        if not cfg.katas:
            break
        r = run_kata(kata, root)
        results.append(r)

    all_passed = all(r["passed"] for r in results)
    return results, all_passed


def _render_results(results: list[dict], spec_id: Optional[str], root: Path) -> None:
    table = Table(box=box.ROUNDED, border_style="dim", header_style="bold", show_lines=True)
    table.add_column("Kata", style="bold", min_width=16)
    table.add_column("Command", style="dim", min_width=20)
    table.add_column("Result", width=10, no_wrap=True)
    table.add_column("Time", width=8, no_wrap=True)
    table.add_column("Output", min_width=30)

    for r in results:
        icon = "[bright_green]✓ pass[/bright_green]" if r["passed"] else "[red]✕ fail[/red]"
        output = r["stderr"] if not r["passed"] and r["stderr"] else r["stdout"]
        output_lines = output.splitlines()
        output_preview = "\n".join(output_lines[-5:]) if output_lines else "[dim](no output)[/dim]"
        table.add_row(
            r["name"],
            r["command"],
            icon,
            f"{r['elapsed_s']}s",
            f"[dim]{output_preview}[/dim]",
        )

    all_passed = all(r["passed"] for r in results)
    passed_count = sum(1 for r in results if r["passed"])
    title_color = "bright_green" if all_passed else "red"
    title = f"[bold {title_color}]{'✓ All katas passed' if all_passed else '✕ Kata failures'}[/bold {title_color}]"
    if spec_id:
        title += f"  [dim]spec {spec_id}[/dim]"

    console.print(Panel(table, title=title, box=box.ROUNDED,
                        border_style="bright_green" if all_passed else "red"))
    console.print(f"  [dim]{passed_count}/{len(results)} katas passed[/dim]")

    if not all_passed:
        console.print(
            "\n  [red]⚠[/red] Fix failing katas before advancing to [magenta]at-gate[/magenta].\n"
            "  [dim]To override:[/dim] [cyan]spec advance <id> --skip-kata --note \"reason\"[/cyan]"
        )


def cmd_run_kata(spec_id: Optional[str], json_out: bool, root: Path) -> None:
    root = find_root(root)
    cfg = load_config(root)

    if spec_id:
        spec = find_spec(root, spec_id)
        if not spec:
            error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    if not cfg.katas:
        if json_out:
            typer.echo(json.dumps({"katas": [], "all_passed": True, "message": "No katas configured"}))
        else:
            console.print(
                "[dim]No katas configured.[/dim]\n"
                "Add katas to [cyan].spec/config.yaml[/cyan]:\n\n"
                "[dim]katas:\n"
                "  - name: tests\n"
                "    command: pytest\n"
                "    description: Full test suite\n"
                "  - name: lint\n"
                "    command: ruff check .\n"
                "    description: Linter[/dim]"
            )
        return

    if not json_out:
        total = len(cfg.katas)
        console.print()
        console.print(Panel(
            f"[bold cyan]◈ Kata harness[/bold cyan]  [dim]running {total} kata{'s' if total != 1 else ''}[/dim]"
            + (f"  [dim]for spec[/dim] [bold]{spec_id}[/bold]" if spec_id else ""),
            box=box.ROUNDED, border_style="cyan", padding=(0, 2),
        ))
        console.print()

    results = []
    for i, kata in enumerate(cfg.katas):
        if not json_out:
            label = f"  [{i + 1}/{len(cfg.katas)}] [bold]{kata.name}[/bold]  [dim]{kata.command}[/dim]"
            with console.status(label, spinner="dots"):
                r = run_kata(kata, root)
            icon = "[bright_green]✓[/bright_green]" if r["passed"] else "[red]✕[/red]"
            time_str = f"[dim]{r['elapsed_s']}s[/dim]"
            desc = f"  [dim]{kata.description}[/dim]" if kata.description else ""
            console.print(f"  {icon}  [bold]{kata.name}[/bold]{desc}  {time_str}")
            if not r["passed"] and r["stderr"]:
                for line in r["stderr"].splitlines()[-3:]:
                    console.print(f"     [red dim]{line}[/red dim]")
        else:
            r = run_kata(kata, root)
        results.append(r)

    all_passed = all(r["passed"] for r in results)

    if json_out:
        typer.echo(json.dumps({
            "spec_id": spec_id,
            "katas": results,
            "all_passed": all_passed,
            "passed": sum(1 for r in results if r["passed"]),
            "total": len(results),
        }))
        if not all_passed:
            raise typer.Exit(1)
        return

    console.print()
    passed_count = sum(1 for r in results if r["passed"])
    if all_passed:
        console.print(Panel(
            f"[bright_green]✓ All {len(results)} katas passed[/bright_green]",
            box=box.ROUNDED, border_style="bright_green", padding=(0, 2),
        ))
    else:
        failed = [r["name"] for r in results if not r["passed"]]
        console.print(Panel(
            f"[red]✕ {len(failed)} kata{'s' if len(failed) != 1 else ''} failed:[/red] "
            + "  ".join(f"[bold]{n}[/bold]" for n in failed)
            + f"\n[dim]{passed_count}/{len(results)} passed[/dim]\n\n"
            + f"[dim]Fix failures, then run:[/dim] [cyan]spec run-kata[/cyan]\n"
            + f"[dim]To skip:[/dim] [cyan]spec advance <id> --skip-kata --note \"reason\"[/cyan]",
            box=box.ROUNDED, border_style="red", padding=(0, 2),
        ))
        raise typer.Exit(1)
    console.print()
