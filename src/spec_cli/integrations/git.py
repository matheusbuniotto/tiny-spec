"""Git integration for tiny-spec — keeps spec lifecycle in sync with git."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
        check=check,
    )


def is_git_repo(root: Path) -> bool:
    result = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, check=False)
    return result.returncode == 0


def git_init(root: Path) -> bool:
    """Run git init in root. Returns True on success."""
    result = _run(["git", "init"], cwd=root, check=False)
    return result.returncode == 0


def git_recent_commits(root: Path, n: int = 10) -> list[dict]:
    """Return the last n commits as a list of dicts with sha, author, date, subject."""
    fmt = "%H\x1f%an\x1f%ad\x1f%s"
    result = _run(
        ["git", "log", f"-{n}", f"--format={fmt}", "--date=short"],
        cwd=root,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\x1f", 3)
        if len(parts) == 4:
            commits.append({
                "sha": parts[0][:8],
                "author": parts[1],
                "date": parts[2],
                "subject": parts[3],
            })
    return commits


def git_context_markdown(root: Path, n: int = 10, commits: list[dict] | None = None) -> str:
    """Build a markdown block summarising recent git history for AI context."""
    if commits is None:
        commits = git_recent_commits(root, n)
    if not commits:
        return ""
    lines = ["# Git Context\n", f"Last {len(commits)} commits:\n"]
    for c in commits:
        lines.append(f"- `{c['sha']}` {c['date']} **{c['author']}** — {c['subject']}")
    lines.append("")

    # Branch info
    branch_res = _run(["git", "branch", "--show-current"], cwd=root, check=False)
    if branch_res.returncode == 0 and branch_res.stdout.strip():
        lines.append(f"Current branch: `{branch_res.stdout.strip()}`\n")

    # Remotes
    remote_res = _run(["git", "remote", "-v"], cwd=root, check=False)
    if remote_res.returncode == 0 and remote_res.stdout.strip():
        remotes: set[str] = set()
        for rline in remote_res.stdout.strip().splitlines():
            parts = rline.split()
            if parts:
                remotes.add(f"{parts[0]} {parts[1]}" if len(parts) > 1 else parts[0])
        if remotes:
            lines.append("Remotes:")
            for r in sorted(remotes):
                lines.append(f"  - {r}")

    return "\n".join(lines) + "\n"


def has_staged_or_dirty_specs(root: Path) -> bool:
    """Check if .spec/ has any uncommitted changes."""
    result = _run(["git", "status", "--porcelain", ".spec/"], cwd=root, check=False)
    return bool(result.stdout.strip())


def git_add_specs(root: Path) -> bool:
    """Stage all .spec/ changes. Returns True if anything was staged."""
    if not has_staged_or_dirty_specs(root):
        return False
    _run(["git", "add", ".spec/"], cwd=root)
    return True


def git_commit_spec(root: Path, message: str) -> Optional[str]:
    """Commit staged .spec/ changes. Returns the short SHA or None if nothing to commit."""
    if not git_add_specs(root):
        return None
    result = _run(
        ["git", "commit", "-m", message, "--", ".spec/"],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        return None
    sha_result = _run(["git", "rev-parse", "--short", "HEAD"], cwd=root, check=False)
    return sha_result.stdout.strip() if sha_result.returncode == 0 else "unknown"


def git_status_summary(root: Path) -> str:
    """One-line summary of .spec/ git status."""
    result = _run(["git", "status", "--porcelain", ".spec/"], cwd=root, check=False)
    if not result.stdout.strip():
        return "clean"
    lines = result.stdout.strip().splitlines()
    added = sum(1 for l in lines if l.startswith("A") or l.startswith("?"))
    modified = sum(1 for l in lines if l.startswith("M") or l.startswith(" M"))
    return f"{added} new, {modified} modified"


def auto_commit_transition(
    root: Path,
    spec_id: str,
    title: str,
    old_status: str,
    new_status: str,
) -> Optional[str]:
    """Auto-commit .spec/ after a lifecycle transition. Returns SHA or None."""
    if not is_git_repo(root):
        return None
    message = f"spec({spec_id}): {old_status} → {new_status} — {title}"
    return git_commit_spec(root, message)


def auto_commit_new(root: Path, spec_id: str, title: str, template: str) -> Optional[str]:
    """Auto-commit .spec/ after creating a new spec. Returns SHA or None."""
    if not is_git_repo(root):
        return None
    message = f"spec({spec_id}): create {template} — {title}"
    return git_commit_spec(root, message)
