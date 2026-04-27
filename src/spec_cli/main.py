from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .commands.init import cmd_init
from .commands.greenfield import cmd_greenfield, PROJECT_TYPES
from .commands.new import cmd_new
from .commands.list_cmd import cmd_list
from .commands.show import cmd_show
from .commands.lifecycle import cmd_advance, cmd_revert
from .commands.dashboard import cmd_dashboard
from .commands.config_cmd import cmd_config_show
from .commands.gate_check import cmd_gate_check
from .commands.git_sync import cmd_sync, cmd_git_context
from .commands.assign import cmd_assign
from .commands.close import cmd_close
from .commands.edit import cmd_edit
from .commands.export import cmd_export
from .commands.checks import cmd_run_checks
from .commands.log_cmd import cmd_log
from .commands.next_action import cmd_next
from .commands.claim import cmd_claim
from .commands.search import cmd_search
from .commands.stats import cmd_stats
from .commands.setup_checks import cmd_setup_checks
from .commands.validate import cmd_validate

app = typer.Typer(
    name="spec",
    help="[bold cyan]tiny-spec[/bold cyan] — spec-driven development CLI\n\n"
         "Human and AI friendly. All commands support [cyan]--json[/cyan] and [cyan]--yes[/cyan].",
    no_args_is_help=False,
    invoke_without_command=True,
    rich_markup_mode="rich",
)

_ROOT = typer.Option(Path("."), "--root", "-r", help="Project root", hidden=True)
_JSON = typer.Option(False, "--json", help="JSON output")
_YES  = typer.Option(False, "--yes", "-y", help="Skip prompts")


@app.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    root: Path = _ROOT,
) -> None:
    """[bold cyan]tiny-spec[/bold cyan] — spec-driven development CLI"""
    if ctx.invoked_subcommand is None:
        cmd_next(json_out=False, root=root)


# ── Lifecycle ────────────────────────────────────────────────

@app.command(rich_help_panel="Lifecycle")
def init(
    folder: Optional[str] = typer.Argument(None, help="Folder name (greenfield). Omit to init current dir."),
    project_type: str = typer.Option("blank", "--type", "-t", help="blank, python-api, typescript-web, cli-tool"),
    author: str = typer.Option("", "--author", "-a"),
    spec_only: bool = typer.Option(False, "--spec-only", help="Only .spec/, skip agents + CLAUDE.md"),
    yes: bool = _YES,
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Init tiny-spec. Pass a folder to scaffold a greenfield project."""
    if folder:
        cmd_greenfield(folder, project_type, author, spec_only, yes, json_out)
    else:
        cmd_init(root, author, yes, json_out)


@app.command(rich_help_panel="Lifecycle")
def new(
    title: str = typer.Argument("", help="Spec title"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="feature | bug | adr | api"),
    author: Optional[str] = typer.Option(None, "--author", "-a"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated"),
    ai: bool = typer.Option(False, "--ai", help="Draft with AI"),
    yes: bool = _YES,
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Create a new spec."""
    cmd_new(title, template, author, tags, yes, json_out, ai, root)


@app.command(rich_help_panel="Lifecycle")
def advance(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    note: Optional[str] = typer.Option(None, "--note", "-n", help="Required at gate transitions"),
    skip_checks: bool = typer.Option(False, "--skip-checks", help="Skip pre-gate checks (requires --note explaining why)"),
    yes: bool = _YES,
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Advance to next state: draft → approved → in-progress → at-gate → implemented"""
    cmd_advance(spec_id, note, yes, json_out, root, skip_checks=skip_checks, skip_checks_reason=note or "")


@app.command(rich_help_panel="Lifecycle")
def revert(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    note: Optional[str] = typer.Option(None, "--note", "-n"),
    yes: bool = _YES,
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Revert a spec back to draft."""
    cmd_revert(spec_id, note, yes, json_out, root)


@app.command(rich_help_panel="Lifecycle")
def close(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    reason: str = typer.Option(..., "--reason", help="descoped | wont-fix | superseded | duplicate"),
    note: Optional[str] = typer.Option(None, "--note", "-n", help="Explain why"),
    yes: bool = _YES,
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Close a spec without implementing it."""
    cmd_close(spec_id, reason, note, yes, json_out, root)


@app.command(rich_help_panel="Lifecycle")
def claim(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    as_agent: str = typer.Option("", "--as", help="Agent name (default: $SPEC_AGENT or 'agent')"),
    yes: bool = _YES,
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Claim an approved spec: assign to self and advance to in-progress atomically."""
    cmd_claim(spec_id, as_agent, yes, json_out, root)


@app.command(rich_help_panel="Lifecycle")
def assign(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    assignee: str = typer.Argument(..., help="Person or agent name (empty string to unassign)"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Assign a spec to a person or agent."""
    cmd_assign(spec_id, assignee, json_out, root)


# ── View ─────────────────────────────────────────────────────

@app.command("list", rich_help_panel="View")
def list_specs(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    stale: bool = typer.Option(False, "--stale", help="Only show specs stuck for 3+ days"),
    full: bool = typer.Option(False, "--full", help="Include spec body in JSON output"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    claimable: bool = typer.Option(False, "--claimable", help="Only show unclaimed approved specs"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """List all specs."""
    cmd_list(status, stale, json_out, root, full, assignee, claimable)


@app.command(rich_help_panel="View")
def show(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    full: bool = typer.Option(False, "--full", "-f", help="Include full spec body"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Show a spec in detail."""
    cmd_show(spec_id, json_out, root, full=full)


@app.command("next", rich_help_panel="View")
def next_action(
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Show the most important thing to do right now."""
    cmd_next(json_out, root)


@app.command(rich_help_panel="View")
def dashboard(
    watch: bool = typer.Option(False, "--watch", "-w", help="Live-refresh"),
    root: Path = _ROOT,
) -> None:
    """Pipeline dashboard."""
    cmd_dashboard(root, watch)


@app.command(rich_help_panel="View")
def stats(
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Pipeline health: counts, cycle time, blockers."""
    cmd_stats(json_out, root)


@app.command(rich_help_panel="View")
def search(
    query: str = typer.Argument(..., help="Search term"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Search specs by title and body content."""
    cmd_search(query, status, json_out, root)


@app.command("log", rich_help_panel="View")
def log(
    last: int = typer.Option(20, "--last", "-n", help="Number of entries to show"),
    spec_id: Optional[str] = typer.Option(None, "--spec", "-s", help="Filter by spec ID"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search within log entries"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Show the spec event log."""
    cmd_log(last, spec_id, query, json_out, root)


# ── Quality ──────────────────────────────────────────────────

@app.command(rich_help_panel="Quality")
def validate(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Check spec structure and AC quality before approving."""
    cmd_validate(spec_id, json_out, root)


@app.command("gate-check", rich_help_panel="Quality")
def gate_check(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Show the Human Gate Checklist for a spec."""
    cmd_gate_check(spec_id, json_out, root)


@app.command("setup-checks", rich_help_panel="Quality")
def setup_checks(
    yes: bool = _YES,
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Scan project and auto-configure pre-gate checks (test, lint, typecheck)."""
    cmd_setup_checks(yes, json_out, root)


@app.command("run-checks", rich_help_panel="Quality")
def run_checks(
    spec_id: Optional[str] = typer.Argument(None, help="Spec ID for context (optional)"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Run all configured pre-gate checks. Exits 1 if any fail."""
    cmd_run_checks(spec_id, json_out, root)


# ── Setup ────────────────────────────────────────────────────

@app.command(rich_help_panel="Setup")
def edit(
    spec_id: str = typer.Argument(..., help="Spec ID or prefix"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Open a spec in $EDITOR."""
    cmd_edit(spec_id, json_out, root)


@app.command(rich_help_panel="Setup")
def config(
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Show project config."""
    cmd_config_show(json_out, root)


@app.command(rich_help_panel="Setup")
def sync(
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Custom commit message"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Commit all .spec/ changes to git."""
    cmd_sync(message, json_out, root)


@app.command("git-context", rich_help_panel="Setup")
def git_context(
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Show recent git commits and refresh .spec/git-context.md."""
    cmd_git_context(json_out, root)


@app.command(rich_help_panel="Setup")
def export(
    active_only: bool = typer.Option(False, "--active", help="Only export active specs"),
    json_out: bool = _JSON,
    root: Path = _ROOT,
) -> None:
    """Export all spec context as a single AI-ingestible payload."""
    cmd_export(json_out, active_only, root)
