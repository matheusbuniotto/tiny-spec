"""Agent-first protocol commands: boot, context, route, and explicit lifecycle verbs."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.markdown import Markdown
from rich.panel import Panel

from ..config import load_config
from ..models import SpecStatus, STATUS_STYLE
from ..storage import append_log, find_root, find_spec, list_specs, save_spec
from ..ui import age_days, console, error
from .gate_check import _extract_gate_checklist, _parse_checklist_items
from .lifecycle import _do_transition


_AC_RE = re.compile(r"##\s+Acceptance Criteria\s*\n(.*?)(?=\n##\s|\Z)", re.IGNORECASE | re.DOTALL)
_REQUIRED_FILES_RE = re.compile(
    r"\*\*Required files:\*\*\s*\n(.*?)(?=\n\*\*|\n##\s|\Z)", re.IGNORECASE | re.DOTALL
)
_RELATED_SPECS_RE = re.compile(
    r"\*\*Related specs:\*\*\s*\n(.*?)(?=\n\*\*|\n##\s|\Z)", re.IGNORECASE | re.DOTALL
)


def _json(data: dict) -> None:
    typer.echo(json.dumps(data))


def _active_specs(root: Path) -> list:
    return [
        s for s in list_specs(root) if s.status not in (SpecStatus.IMPLEMENTED, SpecStatus.CLOSED)
    ]


def _spec_summary(spec) -> dict:
    return {
        "id": spec.id,
        "title": spec.title,
        "summary": spec.summary,
        "status": spec.status.value,
        "agent": spec.agent,
        "assignee": spec.assignee,
        "age_days": age_days(spec.updated_at),
    }


def _claimable(specs: list, agent: str = "") -> list[dict]:
    rows = []
    for spec in specs:
        agent_matches = not agent or not spec.agent or spec.agent == agent
        if spec.status == SpecStatus.APPROVED and not spec.assignee and agent_matches:
            row = _spec_summary(spec)
            row["command"] = f"spec claim {spec.id} --yes --json"
            rows.append(row)
    rows.sort(key=lambda r: -r["age_days"])
    return rows


def _next_for_agent(specs: list, agent: str = "") -> Optional[dict]:
    queue = _claimable(specs, agent)
    if queue:
        top = queue[0]
        top["actor"] = "agent"
        top["action"] = "Claim approved work"
        return top

    at_gate = [s for s in specs if s.status == SpecStatus.AT_GATE]
    if at_gate:
        spec = sorted(at_gate, key=lambda s: -age_days(s.updated_at))[0]
        row = _spec_summary(spec)
        row.update(
            {
                "actor": "human",
                "blocked_for_agent": True,
                "action": "Human must review gate",
                "command": f"spec gate {spec.id}",
            }
        )
        return row

    in_progress = [
        s
        for s in specs
        if s.status == SpecStatus.IN_PROGRESS and (not agent or not s.agent or s.agent == agent)
    ]
    if in_progress:
        spec = sorted(in_progress, key=lambda s: -age_days(s.updated_at))[0]
        row = _spec_summary(spec)
        row.update(
            {
                "actor": "agent",
                "action": "Continue in-progress work",
                "command": f"spec context {spec.id} --json",
            }
        )
        return row
    return None


def _parse_bullets(raw: str) -> list[str]:
    items = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        line = re.sub(r"^-\s*", "", line)
        line = re.sub(r"^\[\s*\]\s*", "", line)
        if line:
            items.append(line)
    return items


def _acceptance_criteria(body: str) -> list[str]:
    match = _AC_RE.search(body)
    if not match:
        return []
    return _parse_bullets(match.group(1))


def _section_items(body: str, regex: re.Pattern[str]) -> list[str]:
    match = regex.search(body)
    if not match:
        return []
    return _parse_bullets(match.group(1))


def _delivery_warning(note: Optional[str]) -> Optional[str]:
    if note and re.search(r"\bAC\d*\b|acceptance criteria", note, re.IGNORECASE):
        return None
    return "delivery_note_missing_ac_evidence"


def _deliver_extra(spec, note: Optional[str]) -> dict:
    checklist = _extract_gate_checklist(spec.body)
    warning = _delivery_warning(note)
    data = {
        "delivered": True,
        "agent_must_stop": True,
        "human_next": {
            "action": "Human reviews gate and passes or rejects",
            "command": f"spec gate {spec.id}",
        },
        "gate_checklist_items": _parse_checklist_items(checklist),
        "delivery_note_warning": warning,
    }
    if warning:
        data["delivery_note_recommendation"] = (
            "Include AC evidence: AC1 → code/test evidence; AC2 → code/test evidence."
        )
    return data


def cmd_boot(agent: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    cfg = load_config(root)
    specs = _active_specs(root)
    data = {
        "protocol_version": "0.1",
        "agent": agent,
        "project": {
            "name": cfg.project_name or root.name,
            "languages": cfg.languages,
            "frameworks": cfg.frameworks,
            "checks": [c.to_dict() for c in cfg.checks],
            "out_of_bounds": cfg.out_of_bounds,
        },
        "rules": {
            "agent_may_claim": True,
            "agent_may_deliver": True,
            "agent_may_pass_gate": False,
            "must_run_checks_before_deliver": True,
        },
        "next": _next_for_agent(specs, agent),
        "claimable_queue": _claimable(specs, agent)[:5],
        "active_summary": [_spec_summary(s) for s in specs],
        "commands": {
            "claim": "spec claim <id> --yes --json",
            "context": "spec context <id> --json",
            "checks": "spec run-checks <id> --json",
            "deliver": 'spec deliver <id> --note "..." --yes --json',
        },
    }
    if json_out:
        _json(data)
        return
    console.print(
        Panel(
            f"[bold]Agent:[/bold] {agent or 'any'}\n"
            f"[bold]Next:[/bold] {(data['next'] or {}).get('action', 'none')}\n"
            f"[bold]Claimable:[/bold] {len(data['claimable_queue'])}",
            title="[bold cyan]Agent boot packet[/bold cyan]",
            box=box.ROUNDED,
            border_style="cyan",
        )
    )


def cmd_context(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    cfg = load_config(root)
    data = {
        "id": spec.id,
        "title": spec.title,
        "summary": spec.summary,
        "status": spec.status.value,
        "agent": spec.agent,
        "assignee": spec.assignee,
        "context_mode": spec.context_mode,
        "spec": spec.to_dict(include_body=True),
        "acceptance_criteria": _acceptance_criteria(spec.body),
        "required_files": _section_items(spec.body, _REQUIRED_FILES_RE),
        "related_specs": _section_items(spec.body, _RELATED_SPECS_RE),
        "rules": {
            "may_edit": True,
            "must_run_checks": True,
            "must_deliver_not_pass": True,
            "out_of_bounds": cfg.out_of_bounds,
        },
        "checks": [c.to_dict() for c in cfg.checks],
        "commands": {
            "run_checks": f"spec run-checks {spec.id} --json",
            "deliver": f'spec deliver {spec.id} --note "..." --yes --json',
        },
    }
    if json_out:
        _json(data)
        return
    console.print(
        Panel(Markdown(spec.body), title=f"[bold]{spec.id} — {spec.title}[/bold]", box=box.ROUNDED)
    )


def cmd_route(spec_id: str, agent: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    old_agent = spec.agent
    spec.agent = agent.strip()
    spec.updated_at = datetime.utcnow()
    save_spec(spec, root)
    append_log(root, f"🧭 ROUTED `{spec.id}` **{spec.title}** → {spec.agent or '(any agent)'}")
    if json_out:
        _json(spec.to_dict(include_body=False))
        return
    console.print(
        Panel(
            f"[bold]{spec.id}[/bold] — {spec.title}\n\n[dim]Agent:[/dim] {old_agent or '(any)'} → [cyan]{spec.agent or '(any)'}[/cyan]",
            title="[bold cyan]Routed[/bold cyan]",
            box=box.ROUNDED,
            border_style="cyan",
        )
    )


def cmd_approve(spec_id: str, yes: bool, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    if spec.status != SpecStatus.DRAFT:
        error(
            "Only draft specs can be approved.",
            json_out,
            {"error": "not_approvable", "status": spec.status.value},
        )
    _do_transition(spec_id, SpecStatus.APPROVED, None, yes, json_out, root, _spec=spec)


def cmd_deliver(
    spec_id: str,
    note: Optional[str],
    yes: bool,
    json_out: bool,
    root: Path,
    skip_checks: bool = False,
) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    if spec.status != SpecStatus.IN_PROGRESS:
        error(
            "Only in-progress specs can be delivered.",
            json_out,
            {"error": "not_deliverable", "status": spec.status.value},
        )
    warning = _delivery_warning(note)
    if warning and not json_out:
        console.print(
            Panel(
                "[yellow]Delivery note does not include AC evidence.[/yellow]\n"
                "[dim]Recommended: AC1 → code/test evidence; AC2 → code/test evidence.[/dim]",
                title="[bold yellow]Delivery note warning[/bold yellow]",
                box=box.ROUNDED,
                border_style="yellow",
            )
        )
    _do_transition(
        spec_id,
        SpecStatus.AT_GATE,
        note,
        yes,
        json_out,
        root,
        skip_checks=skip_checks,
        skip_checks_reason=note or "",
        _spec=spec,
        extra_json=_deliver_extra(spec, note),
    )


def cmd_pass(spec_id: str, note: Optional[str], yes: bool, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    if spec.status != SpecStatus.AT_GATE:
        error(
            "Only at-gate specs can be passed.",
            json_out,
            {"error": "not_passable", "status": spec.status.value},
        )
    _do_transition(spec_id, SpecStatus.IMPLEMENTED, note, yes, json_out, root, _spec=spec)


def cmd_reject(
    spec_id: str,
    note: Optional[str],
    category: str,
    correction: str,
    yes: bool,
    json_out: bool,
    root: Path,
) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    if spec.status != SpecStatus.AT_GATE:
        error(
            "Only at-gate specs can be rejected.",
            json_out,
            {"error": "not_rejectable", "status": spec.status.value},
        )
    if not note or not note.strip():
        error(
            "Reject requires --note explaining what failed.", json_out, {"error": "notes_required"}
        )
    reason = note
    _do_transition(spec_id, SpecStatus.IN_PROGRESS, reason, yes, json_out, root, _spec=spec)
    if category or correction:
        from .corrections import write_correction

        write_correction(
            root,
            spec,
            category or "human-preference",
            correction or reason,
            reason,
            "at-gate",
            "in-progress",
        )


def cmd_gate(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})
    checklist = _extract_gate_checklist(spec.body)
    data = {
        "id": spec.id,
        "title": spec.title,
        "status": spec.status.value,
        "assignee": spec.assignee,
        "agent": spec.agent,
        "delivery_note": spec.gate_notes,
        "acceptance_criteria": _acceptance_criteria(spec.body),
        "gate_checklist_items": _parse_checklist_items(checklist),
        "commands": {
            "pass": f'spec pass {spec.id} --note "what you verified"',
            "reject": f'spec reject {spec.id} --note "what failed"',
        },
    }
    if json_out:
        _json(data)
        return
    icon, color = STATUS_STYLE[spec.status]
    ac = "\n".join(f"- {x}" for x in data["acceptance_criteria"]) or "[dim](none found)[/dim]"
    items = (
        "\n".join(f"- [ ] {x}" for x in data["gate_checklist_items"]) or "[dim](none found)[/dim]"
    )
    console.print(
        Panel(
            f"[{color}]{icon} {spec.status.value}[/{color}]  [dim]Assignee:[/dim] {spec.assignee or '—'}  [dim]Agent:[/dim] {spec.agent or '—'}\n\n"
            f"[bold]Delivery note[/bold]\n{spec.gate_notes or '[dim](none)[/dim]'}\n\n"
            f"[bold]Acceptance criteria[/bold]\n{ac}\n\n"
            f"[bold]Human checklist[/bold]\n{items}\n\n"
            f"[bold]Pass[/bold]   [cyan]{data['commands']['pass']}[/cyan]\n"
            f"[bold]Reject[/bold] [cyan]{data['commands']['reject']}[/cyan]",
            title=f"[bold magenta]Gate review: {spec.id} — {spec.title}[/bold magenta]",
            box=box.ROUNDED,
            border_style="magenta",
        )
    )
