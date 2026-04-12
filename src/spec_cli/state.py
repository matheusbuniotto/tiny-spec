from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from .models import Spec, SpecStatus, TRANSITIONS
from .storage import save_spec, append_log


def transition(
    spec: Spec,
    new_status: SpecStatus,
    root: Path,
    notes: str = "",
    auto_commit: bool = True,
) -> tuple[Spec, Optional[str]]:
    """Transition a spec. Returns (spec, git_sha_or_None)."""
    if not spec.can_transition_to(new_status):
        allowed = [s.value for s in TRANSITIONS[spec.status]]
        raise typer.BadParameter(
            f"Cannot move '{spec.id}' from [{spec.status.value}] → [{new_status.value}]. "
            f"Allowed: {allowed or ['none (terminal state)']}"
        )

    old_status = spec.status
    spec.status = new_status
    spec.updated_at = datetime.utcnow()

    if notes:
        if spec.gate_notes:
            spec.gate_notes = spec.gate_notes.rstrip() + f"\n\n---\n{notes}"
        else:
            spec.gate_notes = notes

    save_spec(spec, root)

    if new_status == SpecStatus.AT_GATE:
        log_entry = f"🔵 GATE OPENED `{spec.id}` **{spec.title}** — {notes}"
    elif new_status == SpecStatus.IMPLEMENTED:
        log_entry = f"✅ GATE PASSED `{spec.id}` **{spec.title}** — {notes}"
    elif new_status == SpecStatus.DRAFT and notes:
        log_entry = f"↩ REVERTED `{spec.id}` **{spec.title}** — {notes}"
    else:
        log_entry = f"`{spec.id}` **{spec.title}** → `{new_status.value}`"
        if notes:
            log_entry += f" — {notes}"

    append_log(root, log_entry)

    git_sha = None
    if auto_commit:
        try:
            from .integrations.git import auto_commit_transition
            git_sha = auto_commit_transition(
                root, spec.id, spec.title,
                old_status.value, new_status.value,
            )
        except Exception:
            pass

    return spec, git_sha
