from __future__ import annotations

import json
import os
from pathlib import Path

import typer

from ..integrations.git import is_git_repo, git_init, git_context_markdown
from ..ui import console, success, error


def cmd_init(root: Path, author: str, yes: bool, json_out: bool) -> None:
    sd = root / ".spec"
    already_had_spec = sd.exists()

    # --- Git handling ---
    git_was_repo = is_git_repo(root)
    git_initialized = False
    if not git_was_repo:
        if not json_out and not yes:
            import questionary
            style = questionary.Style([("question", "bold cyan"), ("answer", "bold white")])
            do_init = questionary.confirm(
                "Not a git repository. Run git init?", default=True, style=style
            ).ask()
            if do_init:
                git_initialized = git_init(root)
        else:
            git_initialized = git_init(root)

    created: list[str] = []
    skipped: list[str] = []

    # --- .spec/ ---
    if already_had_spec:
        skipped.append(".spec/")
    else:
        sd.mkdir(parents=True)
        (sd / "specs").mkdir()
        (sd / "decisions").mkdir()
        (sd / "README.md").write_text(
            "# Specs\n\nManaged by tiny-spec.\n\n"
            "- `specs/` — active specs\n"
            "- `decisions/` — ADRs\n"
            "- `log.md` — event log\n"
            "- `constitution.md` — project principles\n"
            "- `git-context.md` — recent git history (auto-updated)\n"
        )

        resolved_author = author or os.environ.get("SPEC_AUTHOR", "")
        config_template = f"""\
# tiny-spec configuration

author: {resolved_author or ""}
ai_provider: claude-code          # claude-code | anthropic | openai
ai_model: ""                      # leave blank for provider default
ai_base_url: ""                   # openai provider only (Ollama, Groq, etc.)
default_template: feature         # feature | bug | adr | api
git_auto_commit: true             # auto-commit .spec/ on lifecycle transitions

# --- Pre-gate checks (must pass before spec can enter at-gate) ---
# checks:
#   - name: tests
#     command: pytest
#     description: Full test suite must pass
#   - name: lint
#     command: ruff check .
#     description: No linting errors
#   - name: typecheck
#     command: mypy src
#     description: No type errors
checks: []

# --- Project context (enriches AI drafts) ---
project_name: ""
description: ""
languages: []                     # e.g. [python, typescript]
frameworks: []                    # e.g. [fastapi, react]
libraries: []                     # e.g. [pydantic, sqlalchemy]
testing: ""                       # e.g. "pytest, >80% coverage"
architecture: ""                  # e.g. "hexagonal, event-driven"
conventions: []                   # e.g. [snake_case, REST not GraphQL]
out_of_bounds: []                 # e.g. [no jQuery, no raw SQL]
"""
        (sd / "config.yaml").write_text(config_template)
        (sd / "constitution.md").write_text(
            "# Project Constitution\n\n"
            "> Define your project's governing principles here.\n\n"
            "## Principles\n\n- \n\n## Standards\n\n- \n\n## Out of Bounds\n\n- \n"
        )

        git_context = git_context_markdown(root)
        if git_context:
            (sd / "git-context.md").write_text(git_context)
        else:
            (sd / "git-context.md").write_text(
                "# Git Context\n\n> No commits yet. This file will be enriched as the project grows.\n"
            )
        created.append(".spec/")

    # --- CLAUDE.md ---
    claude_md = root / "CLAUDE.md"
    if claude_md.exists():
        skipped.append("CLAUDE.md")
    else:
        from ..scaffold.claude_md import generate_claude_md
        from ..config import load_config, Config
        cfg = load_config(root) if already_had_spec else Config()
        claude_md.write_text(generate_claude_md(cfg, root.name))
        created.append("CLAUDE.md")

    # --- agents (skip existing, write missing) ---
    from ..scaffold.agents import AGENTS
    agents_dir = root / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in AGENTS:
        dest = agents_dir / filename
        if dest.exists():
            skipped.append(f".claude/agents/{filename}")
        else:
            dest.write_text(content)
            created.append(f".claude/agents/{filename}")

    # --- SKILL.md ---
    skill_src = Path(__file__).parent.parent / "SKILL.md"
    if skill_src.exists():
        skill_dir = root / ".claude" / "skills" / "spec"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_dest = skill_dir / "SKILL.md"
        if skill_dest.exists():
            skipped.append(".claude/skills/spec/SKILL.md")
        else:
            skill_dest.write_text(skill_src.read_text())
            created.append(".claude/skills/spec/SKILL.md")

    if json_out:
        typer.echo(json.dumps({
            "initialized": True,
            "path": str(sd),
            "git_initialized": git_initialized,
            "created": created,
            "skipped": skipped,
        }))
        return

    git_line = ""
    if git_initialized:
        git_line = "\n  [dim]Git:[/dim]  [green]git init[/green] [dim]done[/dim]"
    elif git_was_repo and not already_had_spec:
        git_line = "\n  [dim]Git:[/dim]  [green]context captured[/green] [dim]→ .spec/git-context.md[/dim]"

    created_line = ""
    if created:
        created_line = "\n\n  [dim]Created:[/dim]  " + "  ".join(f"[cyan]{c}[/cyan]" for c in created)
    skipped_line = ""
    if skipped:
        skipped_line = "\n  [dim]Skipped (already exist):[/dim]  " + "  ".join(f"[dim]{s}[/dim]" for s in skipped)

    success("tiny-spec", (
        f"[bright_green]Initialized[/bright_green] [dim]{root}[/dim]{git_line}"
        f"{created_line}{skipped_line}\n\n"
        f"  [dim]Edit[/dim] [cyan].spec/config.yaml[/cyan] [dim]to set project context[/dim]\n"
        f"  [dim]Run [/dim] [cyan]spec new \"My first spec\"[/cyan] [dim]to create a spec[/dim]"
    ), border="bright_blue")
