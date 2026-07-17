"""Spec 0005 — AGENTS.md scaffold + opt-in SessionStart hook."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def _init(tmp_path, *extra):
    return runner.invoke(app, ["init", "--yes", "--json", "--root", str(tmp_path), *extra])


def test_init_writes_agents_md(tmp_path):
    result = _init(tmp_path)
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["agents_md"] is True
    content = (tmp_path / "AGENTS.md").read_text()
    assert "tiny-spec" in content
    assert "spec next --json" in content  # golden-path commands present
    assert "constitution.md" in content


def test_greenfield_writes_agents_md(tmp_path):
    target = tmp_path / "newproj"
    result = runner.invoke(app, ["init", str(target), "--yes", "--json"])
    assert result.exit_code == 0
    assert "AGENTS.md" in json.loads(result.stdout)["files"]
    assert (target / "AGENTS.md").exists()


def test_existing_agents_md_left_untouched(tmp_path):
    handwritten = "# my own agents file\n"
    (tmp_path / "AGENTS.md").write_text(handwritten)
    result = _init(tmp_path)
    assert result.exit_code == 0
    assert json.loads(result.stdout)["agents_md"] is False
    assert (tmp_path / "AGENTS.md").read_text() == handwritten


def test_sessionstart_hook_is_opt_in(tmp_path):
    result = _init(tmp_path)
    assert json.loads(result.stdout)["sessionstart_hook"] is False
    assert not (tmp_path / ".claude" / "settings.json").exists()


def test_sessionstart_hook_with_flag(tmp_path):
    result = _init(tmp_path, "--hooks")
    assert json.loads(result.stdout)["sessionstart_hook"] is True
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    hook = settings["hooks"]["SessionStart"][0]["hooks"][0]
    assert hook["command"] == "spec next --json"
