"""spec-loop.sh scaffold — copies the bundled reference agent loop into a project."""

from __future__ import annotations

import stat
from pathlib import Path

_SCRIPT = Path(__file__).parent.parent / "spec-loop.sh"


def write_loop_script(root: Path) -> bool:
    """Write scripts/spec-loop.sh at project root. Returns False (untouched) if it exists."""
    target = root / "scripts" / "spec-loop.sh"
    if target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_SCRIPT.read_text())
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return True
