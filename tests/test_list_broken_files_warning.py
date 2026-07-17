import json

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def _orphan_spec_file(tmp_path):
    # Mimics a spec file dropped in by hand or a different tool — plausible markdown
    # content, right directory, but no YAML frontmatter, so id/title/status are missing.
    path = tmp_path / ".spec" / "specs" / "0001-orphan.md"
    path.write_text("# Orphan spec\n\n## Status: draft\n\nNo frontmatter here.\n")
    return path


def test_list_json_warns_when_specs_exist_but_all_fail_to_parse(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    _orphan_spec_file(tmp_path)

    result = runner.invoke(app, ["list", "--json"])
    payload = json.loads(result.stdout)

    assert payload["count"] == 0
    assert "warnings" in payload
    assert "1 spec file(s)" in payload["warnings"][0]


def test_list_human_warns_when_specs_exist_but_all_fail_to_parse(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    _orphan_spec_file(tmp_path)

    result = runner.invoke(app, ["list"])

    assert "failed to load" in result.stdout
    assert "spec doctor" in result.stdout


def test_list_json_has_no_warnings_key_for_a_genuinely_empty_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])

    result = runner.invoke(app, ["list", "--json"])
    payload = json.loads(result.stdout)

    assert payload["count"] == 0
    assert "warnings" not in payload
