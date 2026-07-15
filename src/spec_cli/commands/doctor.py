"""spec doctor — deterministic linter for the spec graph."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich import box
from rich.panel import Panel

from ..models import SpecStatus
from ..storage import find_root, list_specs
from ..ui import console, with_help
from .gate_check import _extract_gate_checklist

STALE_DAYS = 3


def _age_days(dt: datetime) -> int:
    return (datetime.utcnow() - dt).days


def _find_cycles(by_id: dict) -> list[list[str]]:
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


def _findings(all_specs: list) -> list[dict]:
    by_id: dict = {}
    dupes: set[str] = set()
    for s in all_specs:
        if s.id in by_id:
            dupes.add(s.id)
        else:
            by_id[s.id] = s

    findings: list[dict] = []

    for dupe_id in sorted(dupes):
        findings.append(
            {
                "type": "duplicate_id",
                "spec_id": dupe_id,
                "message": f"Spec ID {dupe_id} is used by more than one file",
                "hint": f"Renumber one of the duplicate {dupe_id} files to a free ID",
            }
        )

    for s in all_specs:
        for b in s.blocked_by:
            if b not in by_id:
                findings.append(
                    {
                        "type": "dangling_blocked_by",
                        "spec_id": s.id,
                        "message": f"{s.id} is blocked_by '{b}', which doesn't exist",
                        "hint": f"Edit {s.id}'s blocked_by to remove or fix '{b}'",
                    }
                )
        if s.parent and s.parent not in by_id:
            findings.append(
                {
                    "type": "dangling_parent",
                    "spec_id": s.id,
                    "message": f"{s.id} has parent '{s.parent}', which doesn't exist",
                    "hint": f"Edit {s.id}'s parent to remove or fix '{s.parent}'",
                }
            )
        if s.status == SpecStatus.IN_PROGRESS and not s.assignee:
            findings.append(
                {
                    "type": "unassigned_in_progress",
                    "spec_id": s.id,
                    "message": f"{s.id} is in-progress with no assignee",
                    "hint": f"spec assign {s.id} <name>, or revert to approved",
                }
            )
        if (
            s.status == SpecStatus.IN_PROGRESS
            and s.assignee
            and _age_days(s.updated_at) >= STALE_DAYS
        ):
            findings.append(
                {
                    "type": "stale_claim",
                    "spec_id": s.id,
                    "message": f"{s.id} claimed by {s.assignee}, no movement for "
                    f"{_age_days(s.updated_at)}d",
                    "hint": f"Finish and advance {s.id}, or release the claim if it's abandoned",
                }
            )
        if s.status == SpecStatus.AT_GATE and not _extract_gate_checklist(s.body):
            findings.append(
                {
                    "type": "missing_gate_checklist",
                    "spec_id": s.id,
                    "message": f"{s.id} is at-gate but has no Human Gate Checklist section",
                    "hint": f"Add a '## Human Gate Checklist' section to {s.id}",
                }
            )
        if s.template == "map" and s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED):
            children = [c for c in all_specs if c.parent == s.id]
            if children and all(
                c.status in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED) for c in children
            ):
                findings.append(
                    {
                        "type": "map_ready_to_close",
                        "spec_id": s.id,
                        "message": f"{s.id} is a map whose children are all done, but it's still "
                        f"{s.status.value}",
                        "hint": f"spec advance {s.id} --yes",
                    }
                )

    for cycle in _find_cycles(by_id):
        ids = " → ".join(cycle + [cycle[0]])
        findings.append(
            {
                "type": "circular_blocked_by",
                "spec_id": cycle[0],
                "message": f"Circular blocked_by chain: {ids}",
                "hint": f"Remove one blocked_by link in the cycle, e.g. edit {cycle[0]}",
            }
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
