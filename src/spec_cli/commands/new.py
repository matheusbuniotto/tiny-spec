from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from ..config import load_config
from ..models import Spec, STATUS_STYLE, SpecStatus
from ..storage import next_id, save_spec, find_root, append_log
from ..ui import console, err_console, success, error

AVAILABLE_TEMPLATES = ["feature", "bug", "adr", "api", "data-pipeline", "experiment"]


def _load_template(name: str) -> str:
    path = Path(__file__).parent.parent / "templates" / f"{name}.md"
    return path.read_text() if path.exists() else f"## Overview\n\n> {name} spec\n"


def _prompt_style():
    import questionary
    return questionary.Style([
        ("question", "bold cyan"), ("answer", "bold white"),
        ("pointer", "bold yellow"), ("selected", "bold green"),
    ])


def cmd_new(
    title: str, template: Optional[str], author: Optional[str],
    tags: Optional[str], yes: bool, json_out: bool, ai: bool, root: Path,
) -> None:
    root = find_root(root)
    if not (root / ".spec").exists():
        error("Not initialized. Run [cyan]spec init[/cyan] first.", json_out, {"error": "not_initialized"})

    cfg = load_config(root)
    resolved_template = template or cfg.default_template
    if resolved_template not in AVAILABLE_TEMPLATES:
        resolved_template = "feature"
    resolved_author = author or cfg.author or ""
    resolved_tags: list[str] = []
    use_ai = ai

    if not yes:
        import questionary
        style = _prompt_style()

        if not title:
            title = questionary.text("Spec title:", style=style).ask()
            if not title:
                raise typer.Exit(0)

        resolved_template = questionary.select(
            "Template:", choices=AVAILABLE_TEMPLATES, default=resolved_template, style=style,
        ).ask() or resolved_template

        tags_raw = questionary.text("Tags (comma-separated, optional):", style=style).ask() or ""
        resolved_tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        if not resolved_author:
            resolved_author = questionary.text("Author (optional):", style=style).ask() or ""

        if not ai:
            use_ai = questionary.confirm("Generate draft with AI?", default=False, style=style).ask()
    else:
        if tags:
            resolved_tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Build body
    if use_ai:
        try:
            from ..integrations.ai import draft_spec_content
            with console.status(f"[cyan]Drafting via {cfg.ai_provider}...[/cyan]", spinner="dots"):
                body = draft_spec_content(
                    title, resolved_template, context=cfg.context_summary(),
                    provider=cfg.ai_provider, model=cfg.ai_model, base_url=cfg.ai_base_url,
                )
        except Exception as e:
            err_console.print(f"[yellow]AI draft failed:[/yellow] {e}\n[dim]Using template.[/dim]")
            body = _load_template(resolved_template)
    else:
        body = _load_template(resolved_template)

    spec_id = next_id(root)
    spec = Spec(id=spec_id, title=title, template=resolved_template, author=resolved_author, tags=resolved_tags, body=body)
    path = save_spec(spec, root)
    append_log(root, f"`{spec_id}` **{title}** created (template: {resolved_template})")

    git_sha = None
    if cfg.git_auto_commit:
        try:
            from ..integrations.git import auto_commit_new
            git_sha = auto_commit_new(root, spec_id, title, resolved_template)
        except Exception:
            pass

    if json_out:
        out = {**spec.to_dict(), "file_path": str(path)}
        if git_sha:
            out["git_commit"] = git_sha
        typer.echo(json.dumps(out))
    else:
        icon, color = STATUS_STYLE[SpecStatus.DRAFT]
        git_line = f"\n  Git      : [green]{git_sha}[/green]" if git_sha else ""
        success("Spec created", (
            f"[bold]{spec_id}[/bold] — {title}\n\n"
            f"  Template : [cyan]{resolved_template}[/cyan]\n"
            f"  Status   : [{color}]{icon} draft[/{color}]\n"
            f"  File     : [dim]{path.relative_to(root)}[/dim]"
            f"{git_line}\n\n"
            f"  [dim]Next:[/dim] [cyan]spec advance {spec_id}[/cyan]"
        ))
