from __future__ import annotations

import json
import os
from pathlib import Path

import typer
import yaml

from ..integrations.git import is_git_repo, git_init, git_context_markdown
from ..ui import console, success, error


def cmd_init(root: Path, author: str, json_out: bool) -> None:
    sd = root / ".spec"

    if sd.exists():
        error("Already initialized.", json_out, {"error": "already_initialized", "path": str(sd)})

    # --- Git handling ---
    git_was_repo = is_git_repo(root)
    git_initialized = False
    if not git_was_repo:
        if not json_out:
            import questionary
            style = questionary.Style([("question", "bold cyan"), ("answer", "bold white")])
            do_init = questionary.confirm(
                "Not a git repository. Run git init?", default=True, style=style
            ).ask()
            if do_init:
                git_initialized = git_init(root)
        # In --json / --yes mode: silently init
        else:
            git_initialized = git_init(root)

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

# --- Kata harness (must pass before spec can enter at-gate) ---
# katas:
#   - name: tests
#     command: pytest
#     description: Full test suite must pass
#   - name: lint
#     command: ruff check .
#     description: No linting errors
#   - name: typecheck
#     command: mypy src
#     description: No type errors
katas: []

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

    # Write git context if the repo has commits
    git_context = git_context_markdown(root)
    if git_context:
        (sd / "git-context.md").write_text(git_context)
    else:
        (sd / "git-context.md").write_text(
            "# Git Context\n\n> No commits yet. This file will be enriched as the project grows.\n"
        )

    if json_out:
        typer.echo(json.dumps({
            "initialized": True,
            "path": str(sd),
            "author": resolved_author,
            "git_initialized": git_initialized,
            "git_context": bool(git_context),
        }))
    else:
        git_line = ""
        if git_initialized:
            git_line = "\n  [dim]Git:[/dim]  [green]git init[/green] [dim]done[/dim]"
        elif git_was_repo and git_context:
            git_line = "\n  [dim]Git:[/dim]  [green]context captured[/green] [dim]→ .spec/git-context.md[/dim]"
        success("tiny-spec", (
            f"[bright_green]Initialized[/bright_green] [dim]{sd}[/dim]{git_line}\n\n"
            f"  [dim]Edit[/dim] [cyan].spec/config.yaml[/cyan] [dim]to set project context[/dim]\n"
            f"  [dim]Run [/dim] [cyan]spec new \"My first spec\"[/cyan] [dim]to create a spec[/dim]"
        ), border="bright_blue")
