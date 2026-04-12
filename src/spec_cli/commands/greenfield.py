from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.tree import Tree

from ..config import Config, save_config
from ..integrations.git import git_init, git_commit_spec
from ..scaffold.agents import AGENTS
from ..scaffold.claude_md import generate_claude_md
from ..scaffold.project_types import scaffold_project
from ..ui import console, success, error

PROJECT_TYPES = ["blank", "python-api", "typescript-web", "cli-tool"]


def cmd_greenfield(
    folder: str,
    project_type: str,
    author: str,
    spec_only: bool,
    yes: bool,
    json_out: bool,
) -> None:
    root = Path(folder).resolve()

    if root.exists() and any(root.iterdir()):
        error("Folder already exists and is not empty.", json_out, {"error": "folder_not_empty", "path": str(root)})

    root.mkdir(parents=True, exist_ok=True)

    # Gather project details interactively if needed
    project_name = folder
    description = ""
    languages: list[str] = []
    frameworks: list[str] = []
    libraries: list[str] = []
    testing = ""
    architecture = ""
    conventions: list[str] = []
    out_of_bounds: list[str] = []
    resolved_author = author or os.environ.get("SPEC_AUTHOR", "")

    if not yes and not json_out:
        import questionary
        style = questionary.Style([
            ("question", "bold cyan"), ("answer", "bold white"),
            ("pointer", "bold yellow"), ("selected", "bold green"),
        ])
        project_name = questionary.text("Project name:", default=folder, style=style).ask() or folder
        description = questionary.text("Short description:", style=style).ask() or ""
        if not resolved_author:
            resolved_author = questionary.text("Author:", style=style).ask() or ""

        if project_type == "blank":
            project_type = questionary.select(
                "Project type:",
                choices=PROJECT_TYPES,
                default="blank",
                style=style,
            ).ask() or "blank"

        stack_raw = questionary.text(
            "Languages (comma-separated, e.g. python, typescript):",
            style=style,
        ).ask() or ""
        languages = [s.strip() for s in stack_raw.split(",") if s.strip()]

        fw_raw = questionary.text("Frameworks (e.g. fastapi, react):", style=style).ask() or ""
        frameworks = [s.strip() for s in fw_raw.split(",") if s.strip()]

        testing = questionary.text(
            "Testing approach (e.g. pytest, >80% coverage):", style=style
        ).ask() or ""

    # Build config
    cfg = Config(
        author=resolved_author,
        project_name=project_name,
        description=description,
        languages=languages,
        frameworks=frameworks,
        libraries=libraries,
        testing=testing,
        architecture=architecture,
        conventions=conventions,
        out_of_bounds=out_of_bounds,
    )

    created: list[str] = []

    # 1. Git init
    git_init(root)
    created.append(".git/")

    # 2. Initialize .spec/
    _init_spec(root, resolved_author, cfg)
    created += [".spec/config.yaml", ".spec/constitution.md", ".spec/specs/", ".spec/decisions/", ".spec/log.md"]

    # Write placeholder git context (no commits yet in a fresh repo)
    git_context_path = root / ".spec" / "git-context.md"
    git_context_path.write_text(
        "# Git Context\n\n> No commits yet. This file will be enriched as the project grows.\n"
    )
    created.append(".spec/git-context.md")

    if not spec_only:
        # 2. Write CLAUDE.md
        claude_md_content = generate_claude_md(cfg, project_name)
        (root / "CLAUDE.md").write_text(claude_md_content)
        created.append("CLAUDE.md")

        # 3. Write agents
        agents_dir = root / ".claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in AGENTS:
            (agents_dir / filename).write_text(content)
            created.append(f".claude/agents/{filename}")

        # 4. Copy SKILL.md → .claude/skills/spec/SKILL.md
        skill_src = Path(__file__).parent.parent / "SKILL.md"
        if skill_src.exists():
            skill_dir = root / ".claude" / "skills" / "spec"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(skill_src.read_text())
            created.append(".claude/skills/spec/SKILL.md")

        # 5. Project type scaffolding
        if project_type != "blank":
            scaffolded = scaffold_project(root, project_type, project_name)
            created.extend(scaffolded)

    if json_out:
        typer.echo(json.dumps({
            "created": str(root),
            "project_type": project_type,
            "spec_only": spec_only,
            "files": created,
        }))
        return

    # Rich output
    tree = Tree(f"[bold cyan]{folder}/[/bold cyan]", guide_style="dim")
    _populate_tree(tree, created)

    body = f"[bright_green]Project created[/bright_green]  [dim]{root}[/dim]\n\n"
    if not spec_only:
        body += f"  Type   : [cyan]{project_type}[/cyan]\n"
        body += f"  Agents : [cyan]{len(AGENTS)}[/cyan] in .claude/agents/\n"
    body += f"  Specs  : [cyan].spec/[/cyan]\n\n"
    body += ("  [dim]Next:[/dim] edit [cyan].spec/config.yaml[/cyan] then [cyan]spec new \"...\"[/cyan]"
             if spec_only else
             "  [dim]Next:[/dim] edit [cyan].spec/config.yaml[/cyan] and [cyan]CLAUDE.md[/cyan]")

    success("tiny-spec greenfield", body, border="bright_blue")
    console.print(tree)


def _init_spec(root: Path, author: str, cfg: Config) -> None:
    """Write .spec/ structure and config."""
    sd = root / ".spec"
    sd.mkdir(exist_ok=True)
    (sd / "specs").mkdir(exist_ok=True)
    (sd / "decisions").mkdir(exist_ok=True)

    (sd / "README.md").write_text(
        "# Specs\n\nManaged by tiny-spec.\n\n"
        "- `specs/` — active specs\n"
        "- `decisions/` — ADRs\n"
        "- `log.md` — event log\n"
        "- `constitution.md` — project principles\n"
        "- `git-context.md` — recent git history (auto-updated)\n"
    )

    config_content = f"""\
# tiny-spec configuration

author: {author or ""}
ai_provider: claude-code
ai_model: ""
ai_base_url: ""
default_template: feature
git_auto_commit: true

# Kata harness — commands that must pass before entering at-gate
# katas:
#   - name: tests
#     command: pytest
#     description: Full test suite must pass
#   - name: lint
#     command: ruff check .
#     description: No linting errors
katas: []

project_name: "{cfg.project_name}"
description: "{cfg.description}"

languages: {_yaml_list(cfg.languages)}
frameworks: {_yaml_list(cfg.frameworks)}
libraries: {_yaml_list(cfg.libraries)}

testing: "{cfg.testing}"
architecture: "{cfg.architecture}"

conventions: {_yaml_list(cfg.conventions)}
out_of_bounds: {_yaml_list(cfg.out_of_bounds)}
"""
    (sd / "config.yaml").write_text(config_content)

    (sd / "constitution.md").write_text(
        f"# {cfg.project_name or 'Project'} Constitution\n\n"
        "> Define your project's governing principles here.\n\n"
        "## Principles\n\n- \n\n## Standards\n\n- \n\n## Out of Bounds\n\n- \n"
    )


def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(f'"{i}"' for i in items) + "]"


def _populate_tree(tree: Tree, paths: list[str]) -> None:
    """Add paths to a rich Tree, grouping by directory."""
    dirs: dict[str, list[str]] = {}
    files: list[str] = []
    for p in paths:
        parts = p.split("/", 1)
        if len(parts) == 2:
            dirs.setdefault(parts[0], []).append(parts[1])
        else:
            files.append(p)

    for f in sorted(files):
        tree.add(f"[dim]{f}[/dim]")
    for d, children in sorted(dirs.items()):
        branch = tree.add(f"[cyan]{d}/[/cyan]")
        for c in sorted(children):
            branch.add(f"[dim]{c}[/dim]")
