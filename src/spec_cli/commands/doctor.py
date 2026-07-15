"""spec doctor — deterministic linter for the spec graph."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich import box
from rich.panel import Panel

from ..models import Spec, SpecStatus
from ..storage import children_of, find_root, list_specs
from ..ui import console, with_help
from .gate_check import extract_gate_checklist

STALE_DAYS = 3


def _age_days(dt: datetime) -> int:
    return (datetime.utcnow() - dt).days


def _finding(kind: str, spec_id: str, message: str, hint: str) -> dict:
    return {"type": kind, "spec_id": spec_id, "message": message, "hint": hint}


def _find_cycles(by_id: dict[str, Spec]) -> list[list[str]]:
    """DFS over blocked_by edges; returns each distinct cycle once."""
    cycles: list[list[str]] = []
    seen: set[frozenset] = set()

    def dfs(node: str, path: list[str], visiting: set[str]) -> None:
        if node in visiting:
            cycle = path[path.index(node) :]
            key = frozenset(cycle)
            if key not in seen:
                seen.add(key)
                cycles.append(cycle)
            return
        if node not in by_id:
            return
        for b in by_id[node].blocked_by:
            dfs(b, path + [node], visiting | {node})

    for spec_id in by_id:
        dfs(spec_id, [], set())
    return cycles


def _findings(all_specs: list[Spec]) -> list[dict]:
    by_id: dict[str, Spec] = {}
    dupes: set[str] = set()
    for s in all_specs:
        if s.id in by_id:
            dupes.add(s.id)
        else:
            by_id[s.id] = s

    findings: list[dict] = []

    for dupe_id in sorted(dupes):
        findings.append(
            _finding(
                "duplicate_id",
                dupe_id,
                f"Spec ID {dupe_id} is used by more than one file",
                f"Renumber one of the duplicate {dupe_id} files to a free ID",
            )
        )

    for s in all_specs:
        for b in s.blocked_by:
            if b not in by_id:
                findings.append(
                    _finding(
                        "dangling_blocked_by",
                        s.id,
                        f"{s.id} is blocked_by '{b}', which doesn't exist",
                        f"Edit {s.id}'s blocked_by to remove or fix '{b}'",
                    )
                )
        if s.parent and s.parent not in by_id:
            findings.append(
                _finding(
                    "dangling_parent",
                    s.id,
                    f"{s.id} has parent '{s.parent}', which doesn't exist",
                    f"Edit {s.id}'s parent to remove or fix '{s.parent}'",
                )
            )
        if s.status == SpecStatus.IN_PROGRESS and not s.assignee:
            findings.append(
                _finding(
                    "unassigned_in_progress",
                    s.id,
                    f"{s.id} is in-progress with no assignee",
                    f"spec assign {s.id} <name>, or revert to approved",
                )
            )
        if (
            s.status == SpecStatus.IN_PROGRESS
            and s.assignee
            and _age_days(s.updated_at) >= STALE_DAYS
        ):
            findings.append(
                _finding(
                    "stale_claim",
                    s.id,
                    f"{s.id} claimed by {s.assignee}, no movement for {_age_days(s.updated_at)}d",
                    f"Finish and advance {s.id}, or release the claim if it's abandoned",
                )
            )
        if s.status == SpecStatus.AT_GATE and not extract_gate_checklist(s.body):
            findings.append(
                _finding(
                    "missing_gate_checklist",
                    s.id,
                    f"{s.id} is at-gate but has no Human Gate Checklist section",
                    f"Add a '## Human Gate Checklist' section to {s.id}",
                )
            )
        if s.template == "map" and s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED):
            children = children_of(s.id, all_specs)
            if children and all(
                c.status in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED) for c in children
            ):
                findings.append(
                    _finding(
                        "map_ready_to_close",
                        s.id,
                        f"{s.id} is a map whose children are all done, but it's still "
                        f"{s.status.value}",
                        f"spec advance {s.id} --yes",
                    )
                )

    for cycle in _find_cycles(by_id):
        ids = " → ".join(cycle + [cycle[0]])
        findings.append(
            _finding(
                "circular_blocked_by",
                cycle[0],
                f"Circular blocked_by chain: {ids}",
                f"Remove one blocked_by link in the cycle, e.g. edit {cycle[0]}",
            )
        )

    return findings


def cmd_doctor(json_out: bool, root: Path) -> None:
    root = find_root(root)
    all_specs = list_specs(root)
    findings = _findings(all_specs)

    if json_out:
        typer.echo(
            json.dumps(with_help({"count": len(findings), "findings": findings}, "spec list"))
        )
        if findings:
            raise typer.Exit(1)
        return

    if not findings:
        console.print(
            Panel(
                "[bright_green]✓ no issues[/bright_green]",
                box=box.ROUNDED,
                border_style="bright_green",
            )
        )
        return

    lines = [
        f"[bold]{f['spec_id']}[/bold] [dim]({f['type']})[/dim]\n  {f['message']}\n  [dim]→ {f['hint']}[/dim]"
        for f in findings
    ]
    console.print(
        Panel(
            "\n\n".join(lines),
            title=f"[bold red]✕ {len(findings)} issue{'s' if len(findings) != 1 else ''}[/bold red]",
            box=box.ROUNDED,
            border_style="red",
        )
    )
    raise typer.Exit(1)
