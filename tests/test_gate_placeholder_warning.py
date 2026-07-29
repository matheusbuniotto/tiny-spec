"""Gate checklist items with unfilled `<...>`/`[...]` template placeholders
should be flagged — a checklist full of dead template text can't verify
anything, but nothing caught that before."""

import json

from typer.testing import CliRunner

from spec_cli.commands.gate_check import find_placeholder_items
from spec_cli.main import app
from spec_cli.storage import find_spec, save_spec

runner = CliRunner()


def _spec_with_checklist(tmp_path, monkeypatch, checklist_md):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]
    spec = find_spec(tmp_path, spec_id)
    spec.body = f"## Overview\n\nStuff.\n\n## Human Gate Checklist\n\n{checklist_md}\n"
    save_spec(spec, tmp_path)
    return spec_id


def test_find_placeholder_items_flags_unfilled_template_text():
    checklist = (
        "- [ ] [agent] **Run the tests**: `<test command>` — all pass?\n"
        "- [ ] [agent] **Walk the happy path**: [describe exact steps]\n"
        "- [ ] [human] **Re-read AC**: each is demonstrably met\n"
    )
    flagged = find_placeholder_items(checklist)
    assert len(flagged) == 2
    assert any("test command" in f for f in flagged)
    assert any("describe exact steps" in f for f in flagged)


def test_find_placeholder_items_ignores_real_commands():
    checklist = (
        "- [ ] [agent] **Run the tests**: `pytest -v` — all pass?\n"
        "- [ ] [human] **Check the diff**: `git diff main` — no debug code?\n"
    )
    assert find_placeholder_items(checklist) == []


def test_gate_check_json_reports_placeholder_items(tmp_path, monkeypatch):
    spec_id = _spec_with_checklist(
        tmp_path,
        monkeypatch,
        "- [ ] [agent] **Run the tests**: `<test command>` — all pass?\n"
        "- [ ] [human] **Re-read AC**: each is demonstrably met\n",
    )

    result = runner.invoke(app, ["gate-check", spec_id, "--json"])

    out = json.loads(result.stdout)
    assert len(out["placeholder_items"]) == 1
    assert "test command" in out["placeholder_items"][0]


def test_gate_check_human_view_warns_on_placeholders(tmp_path, monkeypatch):
    spec_id = _spec_with_checklist(
        tmp_path,
        monkeypatch,
        "- [ ] [agent] **Run the tests**: `<test command>` — all pass?\n",
    )

    result = runner.invoke(app, ["gate-check", spec_id])

    assert "unfilled template placeholders" in result.stdout
