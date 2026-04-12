from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.rule import Rule
from rich.markdown import Markdown
from rich import box

from ..models import SpecStatus, STATUS_STYLE, TRANSITIONS
from ..state import transition
from ..storage import find_spec, find_root
from ..ui import console, err_console, error
from .kata import run_katas_for_spec

# Gate states require notes
_NOTES_REQUIRED = {SpecStatus.AT_GATE, SpecStatus.IMPLEMENTED}
_NOTES_PROMPTS = {
    SpecStatus.AT_GATE:     "Gate notes (what needs human review?): ",
    SpecStatus.IMPLEMENTED: "Approval notes (what was verified?): ",
}

_GATE_CHECKLIST_RE = re.compile(
    r"## Human Gate Checklist\s*\n(.*?)(?=\n## |\Z)",
    re.DOTALL,
)


def _extract_gate_checklist(body: str) -> str:
    """Pull the Human Gate Checklist section from the spec body."""
    m = _GATE_CHECKLIST_RE.search(body)
    if not m:
        return ""
    raw = m.group(1).strip()
    lines = [l for l in raw.splitlines() if l.strip() and not l.strip().startswith(">")]
    return "\n".join(lines)


def _resolve(spec_id: str, root: Path, json_out: bool):
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    return spec


def _get_notes(target: SpecStatus, note: Optional[str], yes: bool, json_out: bool) -> str:
    if note and note.strip():
        return note
    if target not in _NOTES_REQUIRED:
        return note or ""
    if yes:
        error(
            f"Notes required to advance to [magenta]{target.value}[/magenta]. Use [cyan]--note[/cyan]",
            json_out, {"error": "notes_required", "advancing_to": target.value},
        )
    import questionary
    style = questionary.Style([("question", "bold cyan"), ("answer", "bold white")])
    notes = questionary.text(_NOTES_PROMPTS[target], style=style).ask() or ""
    if not notes.strip():
        error("Notes are required for this transition.", json_out)
    return notes


def _check_drift(spec, root: Path) -> bool:
    """Return True if the spec file was hand-edited since last CLI transition."""
    if not spec.file_path:
        return False
    p = Path(spec.file_path)
    if not p.exists():
        return False
    from datetime import datetime, timezone
    file_mtime = datetime.utcfromtimestamp(p.stat().st_mtime)
    delta = (file_mtime - spec.updated_at).total_seconds()
    return delta > 5


def _do_transition(
    spec_id: str, target: SpecStatus, note: Optional[str], yes: bool,
    json_out: bool, root: Path, skip_kata: bool = False, skip_kata_reason: str = "",
) -> None:
    from ..config import load_config
    root = find_root(root)
    spec = _resolve(spec_id, root, json_out)
    old_status = spec.status
    notes = _get_notes(target, note, yes, json_out)

    if old_status in (SpecStatus.IN_PROGRESS, SpecStatus.APPROVED) and _check_drift(spec, root):
        if not json_out:
            console.print(Panel(
                "[yellow]⚠ Spec file was modified since last transition.[/yellow]\n"
                "[dim]The spec may have drifted from what was approved. "
                "Consider reviewing changes before advancing.[/dim]",
                box=box.ROUNDED, border_style="yellow",
            ))

    # Kata gate enforcement — runs before entering at-gate
    if target == SpecStatus.AT_GATE:
        cfg = load_config(root)
        if cfg.katas and not skip_kata:
            if not json_out:
                console.print(f"[dim]Running {len(cfg.katas)} kata{'s' if len(cfg.katas) != 1 else ''} before gate...[/dim]\n")
            results, all_passed = run_katas_for_spec(root, spec_id)
            if not all_passed:
                failed = [r["name"] for r in results if not r["passed"]]
                if json_out:
                    error(
                        f"Kata failures block gate: {', '.join(failed)}",
                        json_out,
                        {"error": "kata_failed", "failed": failed, "results": results,
                         "hint": "Run spec run-kata to see details, or use --skip-kata --note 'reason' to override"},
                    )
                console.print()
                from .kata import _render_results
                _render_results(results, spec_id, root)
                raise typer.Exit(1)
            if not json_out and results:
                passed_count = sum(1 for r in results if r["passed"])
                console.print(f"  [bright_green]✓[/bright_green] [dim]{passed_count}/{len(results)} katas passed[/dim]\n")
        elif skip_kata and cfg.katas:
            if not json_out:
                reason_str = f" — {skip_kata_reason}" if skip_kata_reason else ""
                console.print(f"  [yellow]⚠ Katas skipped{reason_str}[/yellow]\n")

    cfg = load_config(root)
    try:
        spec, git_sha = transition(spec, target, root, notes, auto_commit=cfg.git_auto_commit)
    except typer.BadParameter as e:
        error(str(e), json_out, {"error": "invalid_transition", "detail": str(e)})

    if json_out:
        out = spec.to_dict()
        if git_sha:
            out["git_commit"] = git_sha
        typer.echo(json.dumps(out))
        return

    old_icon, old_color = STATUS_STYLE[old_status]
    new_icon, new_color = STATUS_STYLE[spec.status]
    git_line = f"\n  [dim]Git:[/dim] [green]{git_sha}[/green]" if git_sha else ""
    console.print(Panel(
        f"[bold]{spec.id}[/bold] — {spec.title}\n\n"
        f"  [{old_color}]{old_icon} {old_status.value}[/{old_color}]"
        f"  [dim]→[/dim]  "
        f"[{new_color}]{new_icon} {spec.status.value}[/{new_color}]"
        f"{git_line}",
        title="[bold bright_green]Transition complete[/bold bright_green]",
        box=box.ROUNDED, border_style="bright_green",
    ))
    if target == SpecStatus.AT_GATE:
        checklist = _extract_gate_checklist(spec.body)
        if checklist:
            console.print(Panel(
                Markdown(f"**Before you pass this gate, verify each item:**\n\n{checklist}"),
                title="[bold magenta]⏸ Human Gate Checklist[/bold magenta]",
                box=box.ROUNDED, border_style="magenta",
            ))
        else:
            console.print(Panel(
                "[magenta]⏸ Waiting for human review.[/magenta]\n"
                "[yellow]⚠ No Human Gate Checklist found in this spec. "
                "Consider adding one for clear verification steps.[/yellow]",
                box=box.ROUNDED, border_style="magenta",
            ))
        console.print(
            f"\n  [dim]Once verified, run[/dim] [cyan]spec advance {spec_id} "
            f"--note \"<what you verified>\"[/cyan]\n"
        )
    elif target == SpecStatus.IMPLEMENTED:
        console.print(Rule("[bright_green]Spec implemented[/bright_green]", style="bright_green"))


def cmd_advance(
    spec_id: str, note: Optional[str], yes: bool, json_out: bool, root: Path,
    skip_kata: bool = False, skip_kata_reason: str = "",
) -> None:
    root = find_root(root)
    spec = _resolve(spec_id, root, json_out)
    next_states = TRANSITIONS[spec.status]
    if not next_states:
        error(
            "Already at terminal state — nothing to advance.",
            json_out, {"error": "terminal_state", "status": spec.status.value},
        )
    _do_transition(spec_id, next_states[0], note, yes, json_out, root, skip_kata, skip_kata_reason)


def cmd_revert(spec_id: str, note: Optional[str], yes: bool, json_out: bool, root: Path) -> None:
    _do_transition(spec_id, SpecStatus.DRAFT, note, yes, json_out, root)
