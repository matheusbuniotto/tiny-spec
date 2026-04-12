from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter

from .models import Spec, SpecStatus

SPEC_DIR_NAME = ".spec"


def find_root(start: Path = Path(".")) -> Path:
    """Walk up from start until .spec/ is found. Falls back to start."""
    current = start.resolve()
    while True:
        if (current / SPEC_DIR_NAME).exists():
            return current
        parent = current.parent
        if parent == current:
            return start.resolve()
        current = parent


def spec_dir(root: Path) -> Path:
    return root / SPEC_DIR_NAME


def specs_dir(root: Path) -> Path:
    return spec_dir(root) / "specs"


def decisions_dir(root: Path) -> Path:
    return spec_dir(root) / "decisions"


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:50].strip("-")


def filename_for(spec_id: str, title: str) -> str:
    return f"{spec_id}-{_slugify(title)}.md"


def _storage_dir(root: Path, template: str) -> Path:
    """ADRs go to decisions/, everything else to specs/."""
    if template == "adr":
        return decisions_dir(root)
    return specs_dir(root)


def save_spec(spec: Spec, root: Path) -> Path:
    sd = _storage_dir(root, spec.template)
    sd.mkdir(parents=True, exist_ok=True)

    # Find existing file (may be in specs/ or decisions/)
    existing = _find_file_by_id(spec.id, root)
    target = sd / filename_for(spec.id, spec.title)
    if existing and existing != target:
        existing.rename(target)  # handles title change or template change
        existing = target

    path = sd / filename_for(spec.id, spec.title)
    meta = {
        "id": spec.id,
        "title": spec.title,
        "status": spec.status.value,
        "created_at": spec.created_at.isoformat(),
        "updated_at": spec.updated_at.isoformat(),
        "author": spec.author,
        "assignee": spec.assignee,
        "gate_notes": spec.gate_notes,
        "tags": spec.tags,
        "template": spec.template,
    }
    post = frontmatter.Post(spec.body, **meta)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    return path


def _find_file_by_id(spec_id: str, root: Path) -> Optional[Path]:
    """Search both specs/ and decisions/ for a spec by ID."""
    for search_dir in (specs_dir(root), decisions_dir(root)):
        for p in search_dir.glob(f"{spec_id}-*.md"):
            return p
    return None


def load_spec(path: Path) -> Spec:
    post = frontmatter.load(str(path))
    data = dict(post.metadata)
    data["body"] = post.content
    data["file_path"] = str(path)

    for field in ("created_at", "updated_at"):
        if isinstance(data.get(field), str):
            data[field] = datetime.fromisoformat(data[field])

    if isinstance(data.get("tags"), str):
        data["tags"] = [t.strip() for t in data["tags"].split(",") if t.strip()]

    return Spec(**data)


def _iter_spec_files(root: Path):
    for d in (specs_dir(root), decisions_dir(root)):
        if d.exists():
            yield from sorted(d.glob("*.md"))


def list_specs(root: Path, status: Optional[SpecStatus] = None) -> list[Spec]:
    specs = []
    for p in _iter_spec_files(root):
        try:
            specs.append(load_spec(p))
        except Exception:
            pass
    specs.sort(key=lambda s: s.id)
    if status:
        specs = [s for s in specs if s.status == status]
    return specs


def next_id(root: Path) -> str:
    existing = list_specs(root)
    if not existing:
        return "0001"
    try:
        max_id = max(int(s.id) for s in existing)
    except ValueError:
        max_id = len(existing)
    return str(max_id + 1).zfill(4)


def find_spec(root: Path, id_or_prefix: str) -> Optional[Spec]:
    padded = id_or_prefix.zfill(4)
    for spec in list_specs(root):
        if spec.id == padded or spec.id.startswith(id_or_prefix):
            return spec
    return None


# ── Event log ────────────────────────────────────────────────────────────────

def append_log(root: Path, entry: str) -> None:
    """Append a timestamped entry to .spec/log.md."""
    log_path = spec_dir(root) / "log.md"
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    line = f"- **{ts}** — {entry}\n"
    if not log_path.exists():
        log_path.write_text("# Spec Log\n\nAppend-only record of spec events.\n\n")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)
