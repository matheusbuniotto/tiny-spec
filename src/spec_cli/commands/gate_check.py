"""Show the Human Gate Checklist for a spec — standalone command."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
from rich import box
from rich.markdown import Markdown
from rich.panel import Panel

from ..config import effective_gate, load_config
from ..storage import find_spec
from ..ui import console, find_root_or_error, not_found

_GATE_CHECKLIST_RE = re.compile(
    r"## Human Gate Checklist\s*\n(.*?)(?=\n## |\Z)",
    re.DOTALL,
)

# Only lowercase [agent] or [human] at the very start of the item text
# (after the checkbox) is a class marker. Anything else — [Agent], [bot],
# a bracket mid-text — is plain text and the item defaults to human.
_CLASS_MARKER_RE = re.compile(r"^\[(agent|human)\]\s*")

_CHECKBOX_PREFIX_RE = re.compile(r"^(\s*-\s*(?:\[[ xX]\]\s*)?)(.*)$")


def extract_gate_checklist(body: str) -> str:
    m = _GATE_CHECKLIST_RE.search(body)
    if not m:
        return ""
    raw = m.group(1).strip()
    lines = [ln for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith(">")]
    return "\n".join(lines)


def classify_checklist_item(item: str) -> tuple[str, str]:
    """Split a checklist item's class marker from its display text.

    Returns ("agent" | "human", text with the marker stripped). Unmarked
    items default to "human" — the safe direction — with text untouched.
    """
    m = _CLASS_MARKER_RE.match(item)
    if m:
        return m.group(1), item[m.end() :]
    return "human", item


def strip_class_markers(checklist: str) -> str:
    """Remove [agent]/[human] markers from checklist markdown for display."""
    out = []
    for line in checklist.splitlines():
        m = _CHECKBOX_PREFIX_RE.match(line)
        if m:
            _, text = classify_checklist_item(m.group(2))
            out.append(m.group(1) + text)
        else:
            out.append(line)
    return "\n".join(out)


def _parse_checklist_items(checklist: str) -> list[str]:
    items = []
    for line in checklist.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        item = re.sub(r"^-\s*\[[ xX]\]\s*", "", stripped)
        item = re.sub(r"^-\s+", "", item)
        if item:
            items.append(item)
    return items


def _split_checklist_items(checklist: str) -> tuple[list[str], list[str], list[str]]:
    """Parse items into (flat, agent_verifiable, human_only), markers stripped."""
    flat: list[str] = []
    agent_verifiable: list[str] = []
    human_only: list[str] = []
    for item in _parse_checklist_items(checklist):
        cls, text = classify_checklist_item(item)
        flat.append(text)
        (agent_verifiable if cls == "agent" else human_only).append(text)
    return flat, agent_verifiable, human_only


def cmd_gate_check(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root_or_error(root, json_out)
    spec = find_spec(root, spec_id)
    if not spec:
        not_found(spec_id, json_out)

    checklist = extract_gate_checklist(spec.body)
    gate_mode = effective_gate(spec, load_config(root))

    if json_out:
        items, agent_verifiable, human_only = _split_checklist_items(checklist)
        typer.echo(
            json.dumps(
                {
                    "id": spec.id,
                    "title": spec.title,
                    "status": spec.status.value,
                    "gate_mode": gate_mode,
                    "has_gate_checklist": bool(checklist),
                    "gate_checklist": checklist,
                    "gate_checklist_items": items,
                    "agent_verifiable": agent_verifiable,
                    "human_only": human_only,
                }
            )
        )
        return

    if not checklist:
        console.print(
            Panel(
                f"[bold]{spec.id}[/bold] — {spec.title}\n\n"
                "[yellow]⚠ No Human Gate Checklist found.[/yellow]\n"
                "[dim]Add a '## Human Gate Checklist' section to the spec file.[/dim]",
                title="[bold yellow]No Checklist[/bold yellow]",
                box=box.ROUNDED,
                border_style="yellow",
            )
        )
        return

    console.print(
        Panel(
            Markdown(f"**{spec.id}** — {spec.title}\n\n{strip_class_markers(checklist)}"),
            title="[bold magenta]⏸ Human Gate Checklist[/bold magenta]",
            box=box.ROUNDED,
            border_style="magenta",
        )
    )
