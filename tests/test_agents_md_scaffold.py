import json

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def test_generate_agents_md_extracts_both_skill_md_sections():
    # Regression guard: _section() string-matches SKILL.md heading text. If a heading
    # there is ever renamed, extraction silently degrades to an empty section instead
    # of erroring — this test is the tripwire.
    from spec_cli.scaffold.agents_md import generate_agents_md

    content = generate_agents_md()

    assert "## Start of every session" in content
    assert "## Golden-path commands" in content
    assert "spec claim <id>" in content  # from the Lifecycle section of SKILL.md


def test_init_writes_agents_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--yes", "--json"])

    assert result.exit_code == 0
    agents_md = tmp_path / "AGENTS.md"
    assert agents_md.exists()
    content = agents_md.read_text()
    assert "spec next --json" in content
    assert ".spec/constitution.md" in content or "constitution.md" in content


def test_greenfield_writes_agents_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "myproj", "--yes", "--json"])

    assert result.exit_code == 0
    agents_md = tmp_path / "myproj" / "AGENTS.md"
    assert agents_md.exists()
    assert "spec next --json" in agents_md.read_text()


def test_greenfield_spec_only_still_writes_agents_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "myproj", "--spec-only", "--yes", "--json"])

    assert result.exit_code == 0
    assert (tmp_path / "myproj" / "AGENTS.md").exists()


def test_init_does_not_overwrite_hand_authored_agents_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# Hand-written, do not touch\n")

    result = runner.invoke(app, ["init", "--yes", "--json"])

    assert result.exit_code == 0
    assert (tmp_path / "AGENTS.md").read_text() == "# Hand-written, do not touch\n"


def test_init_json_output_reports_agents_md_written(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--yes", "--json"])
    payload = json.loads(result.stdout)

    assert payload["agents_md_written"] is True


def test_hooks_flag_off_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])

    assert not (tmp_path / ".claude" / "settings.json").exists()


def test_hooks_flag_installs_session_start_hook(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--hooks", "--yes", "--json"])

    assert result.exit_code == 0
    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.exists()
    settings = json.loads(settings_path.read_text())
    commands = [h["command"] for group in settings["hooks"]["SessionStart"] for h in group["hooks"]]
    assert "spec next --json" in commands


def test_hooks_flag_merges_into_existing_settings_without_clobbering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text(
        json.dumps({"otherSetting": "keep-me", "hooks": {"Stop": [{"hooks": []}]}})
    )

    result = runner.invoke(app, ["init", "--hooks", "--yes", "--json"])

    assert result.exit_code == 0
    settings = json.loads((claude_dir / "settings.json").read_text())
    assert settings["otherSetting"] == "keep-me"
    assert "Stop" in settings["hooks"]
    commands = [h["command"] for group in settings["hooks"]["SessionStart"] for h in group["hooks"]]
    assert "spec next --json" in commands


def test_session_start_hook_writer_is_idempotent(tmp_path, monkeypatch):
    # `spec init --hooks` twice can't be exercised through the CLI: a second `spec init`
    # in the same dir always hard-errors with "already initialized" before reaching the
    # hook writer. So call the writer directly, twice, to prove *it* dedupes.
    from spec_cli.scaffold.session_hook import write_session_start_hook

    write_session_start_hook(tmp_path)
    write_session_start_hook(tmp_path)

    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    commands = [h["command"] for group in settings["hooks"]["SessionStart"] for h in group["hooks"]]
    assert commands.count("spec next --json") == 1
