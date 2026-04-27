"""Validate a spec's structure and AC quality without AI."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import typer
from rich.panel import Panel
from rich import box

from ..storage import find_spec, find_root
from ..ui import console, error

# ── heuristics ────────────────────────────────────────────────

_VAGUE_WORDS = re.compile(
    r"\b(should be|performant|fast|slow|good|bad|reasonable|appropriate|"
    r"easy|simple|better|improve|nice|clean|proper|sufficient|adequate)\b",
    re.IGNORECASE,
)

_PLACEHOLDER = re.compile(
    r"(\[your|\[todo\]|<todo>|<your|\[your |<placeholder>|\bTBD\b|\bTODO\b)",
    re.IGNORECASE,
)

_SECTION = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_LIST_ITEM = re.compile(r"^\s*[-*]|\s*\d+\.", re.MULTILINE)


def _sections(body: str) -> set[str]:
    return {m.group(1).strip().lower() for m in _SECTION.finditer(body)}


def _section_body(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(body)
    if not m:
        return ""
    raw = m.group(1)
    lines = [l for l in raw.splitlines() if l.strip() and not l.strip().startswith(">")]
    return "\n".join(lines)


def _ac_items(ac_body: str) -> list[str]:
    items = []
    for line in ac_body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # strip checkbox and leading bullet
        text = re.sub(r"^-\s*\[[ xX]\]\s*", "", stripped)
        text = re.sub(r"^\*{1,2}AC\d+\*{0,2}:?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^[-*]\s+", "", text)
        if text:
            items.append(text)
    return items


# ── issue dataclass ────────────────────────────────────────────

@dataclass
class Issue:
    code: str
    message: str
    severity: str  # "error" | "warn"


@dataclass
class ValidationResult:
    spec_id: str
    title: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warn"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


# ── core validator ─────────────────────────────────────────────

def validate_spec(spec) -> ValidationResult:
    result = ValidationResult(spec_id=spec.id, title=spec.title)
    body = spec.body
    secs = _sections(body)

    def err(code: str, msg: str) -> None:
        result.issues.append(Issue(code, msg, "error"))

    def warn(code: str, msg: str) -> None:
        result.issues.append(Issue(code, msg, "warn"))

    # Title
    if len(spec.title.split()) < 3:
        warn("TITLE_SHORT", "Title has fewer than 3 words — prefer an action-oriented verb phrase")

    # Acceptance Criteria section
    ac_heading = next((s for s in secs if "acceptance criteria" in s), None)
    if not ac_heading:
        err("NO_AC", "Missing '## Acceptance Criteria' section")
    else:
        ac_raw = _section_body(body, ac_heading.title())
        if not ac_raw:
            ac_raw = _section_body(body, "Acceptance Criteria")
        items = _ac_items(ac_raw)
        if len(items) == 0:
            err("AC_EMPTY", "Acceptance Criteria section has no items")
        elif len(items) < 2:
            warn("AC_FEW", "Only one acceptance criterion — consider whether edge cases are covered")
        for item in items:
            if _VAGUE_WORDS.search(item):
                m = _VAGUE_WORDS.search(item)
                warn("AC_VAGUE", f"Vague language in AC (\"{m.group(0)}\") — use a measurable outcome: {item[:80]}")
            if _PLACEHOLDER.search(item):
                err("AC_PLACEHOLDER", f"Placeholder text in AC — replace before approving: {item[:80]}")

    # Out of Scope
    has_oos = any("out of scope" in s or "out-of-scope" in s for s in secs)
    if not has_oos:
        warn("NO_OOS", "No 'Out of Scope' section — explicitly stating what's excluded prevents scope creep")

    # Human Gate Checklist
    has_gate = any("human gate" in s or "gate checklist" in s for s in secs)
    if not has_gate:
        warn("NO_GATE", "No 'Human Gate Checklist' section")
    else:
        gate_raw = _section_body(body, "Human Gate Checklist")
        if _PLACEHOLDER.search(gate_raw):
            err("GATE_PLACEHOLDER", "Gate checklist contains placeholder text — replace with real commands")

    # Global placeholder check
    if _PLACEHOLDER.search(body):
        already_flagged_ac = any(i.code == "AC_PLACEHOLDER" for i in result.issues)
        already_flagged_gate = any(i.code == "GATE_PLACEHOLDER" for i in result.issues)
        if not already_flagged_ac and not already_flagged_gate:
            warn("PLACEHOLDER", "Spec body contains placeholder text (TBD, TODO, <placeholder>)")

    return result


# ── command ───────────────────────────────────────────────────

def cmd_validate(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    result = validate_spec(spec)

    if json_out:
        typer.echo(json.dumps({
            "id": result.spec_id,
            "title": result.title,
            "passed": result.passed,
            "errors": [{"code": i.code, "message": i.message} for i in result.errors],
            "warnings": [{"code": i.code, "message": i.message} for i in result.warnings],
        }))
        return

    _render(result)
    if not result.passed:
        raise typer.Exit(1)


def _render(result: ValidationResult) -> None:
    lines = []
    for issue in result.issues:
        if issue.severity == "error":
            lines.append(f"[red]✗[/red] [bold]{issue.code}[/bold]  {issue.message}")
        else:
            lines.append(f"[yellow]⚠[/yellow] [dim]{issue.code}[/dim]  {issue.message}")

    if result.passed and not result.warnings:
        body = "[bright_green]✓ All checks passed[/bright_green]"
        title = "[bold bright_green]Valid[/bold bright_green]"
        border = "bright_green"
    elif result.passed:
        body = "\n".join(lines)
        title = "[bold yellow]Warnings[/bold yellow]"
        border = "yellow"
    else:
        body = "\n".join(lines)
        title = "[bold red]Invalid[/bold red]"
        border = "red"

    console.print(Panel(
        f"[bold]{result.spec_id}[/bold] — {result.title}\n\n{body}",
        title=title,
        box=box.ROUNDED,
        border_style=border,
    ))
