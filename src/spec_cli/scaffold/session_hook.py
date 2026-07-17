"""Optional Claude Code SessionStart hook that surfaces `spec next` at session open."""

from __future__ import annotations

import json
from pathlib import Path

_HOOK_COMMAND = "spec next --json"


def write_session_start_hook(root: Path) -> bool:
    """Merge a SessionStart hook into .claude/settings.json. Idempotent. Returns True if added."""
    settings_path = root / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    session_start = settings.setdefault("hooks", {}).setdefault("SessionStart", [])

    already_present = any(
        h.get("command") == _HOOK_COMMAND for group in session_start for h in group.get("hooks", [])
    )
    if already_present:
        return False

    session_start.append({"hooks": [{"type": "command", "command": _HOOK_COMMAND}]})
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    return True
