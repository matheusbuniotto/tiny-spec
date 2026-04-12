from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SpecStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    IN_PROGRESS = "in-progress"
    AT_GATE = "at-gate"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"


CLOSE_REASONS = ("descoped", "wont-fix", "superseded", "duplicate")

# Status display: (icon, rich color)
STATUS_STYLE: dict[SpecStatus, tuple[str, str]] = {
    SpecStatus.DRAFT:        ("⬡", "yellow"),
    SpecStatus.APPROVED:     ("◉", "bright_blue"),
    SpecStatus.IN_PROGRESS:  ("▶", "cyan"),
    SpecStatus.AT_GATE:      ("⏸", "magenta"),
    SpecStatus.IMPLEMENTED:  ("✓", "bright_green"),
    SpecStatus.CLOSED:       ("✕", "dim"),
}

# Valid state transitions
TRANSITIONS: dict[SpecStatus, list[SpecStatus]] = {
    SpecStatus.DRAFT:        [SpecStatus.APPROVED],
    SpecStatus.APPROVED:     [SpecStatus.IN_PROGRESS, SpecStatus.DRAFT],
    SpecStatus.IN_PROGRESS:  [SpecStatus.AT_GATE, SpecStatus.APPROVED],
    SpecStatus.AT_GATE:      [SpecStatus.IMPLEMENTED, SpecStatus.IN_PROGRESS],
    SpecStatus.IMPLEMENTED:  [],
    SpecStatus.CLOSED:       [],
}

TRANSITION_LABELS: dict[SpecStatus, str] = {
    SpecStatus.APPROVED:     "approve",
    SpecStatus.IN_PROGRESS:  "start",
    SpecStatus.AT_GATE:      "gate",
    SpecStatus.IMPLEMENTED:  "pass",
    SpecStatus.DRAFT:        "revert to draft",
    SpecStatus.CLOSED:       "close",
}


class Spec(BaseModel):
    id: str
    title: str
    status: SpecStatus = SpecStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    author: str = ""
    assignee: str = ""
    gate_notes: str = ""
    tags: list[str] = Field(default_factory=list)
    template: str = "feature"
    body: str = ""
    file_path: Optional[str] = None

    def can_transition_to(self, new_status: SpecStatus) -> bool:
        return new_status in TRANSITIONS[self.status]

    def status_icon(self) -> str:
        return STATUS_STYLE[self.status][0]

    def status_color(self) -> str:
        return STATUS_STYLE[self.status][1]

    def status_rich(self) -> str:
        icon, color = STATUS_STYLE[self.status]
        return f"[{color}]{icon} {self.status.value}[/{color}]"

    def to_dict(self, include_body: bool = True) -> dict:
        d = {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author,
            "assignee": self.assignee,
            "gate_notes": self.gate_notes,
            "tags": self.tags,
            "template": self.template,
            "file_path": self.file_path,
        }
        if include_body:
            d["body"] = self.body
        return d
