import json

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def test_list_errors_instead_of_silently_empty_when_uninitialized(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no .spec/ anywhere above this — not a tiny-spec project

    result = runner.invoke(app, ["list", "--json"])
    payload = json.loads(result.stdout)

    assert result.exit_code == 1
    assert payload["error"] == "not_initialized"


def test_show_errors_instead_of_silently_not_found_when_uninitialized(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["show", "0001", "--json"])
    payload = json.loads(result.stdout)

    assert result.exit_code == 1
    assert payload["error"] == "not_initialized"


def test_next_errors_instead_of_silently_empty_when_uninitialized(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["next", "--json"])
    payload = json.loads(result.stdout)

    assert result.exit_code == 1
    assert payload["error"] == "not_initialized"


def test_stats_errors_when_uninitialized(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["stats", "--json"])
    payload = json.loads(result.stdout)

    assert result.exit_code == 1
    assert payload["error"] == "not_initialized"


def test_list_still_works_normally_once_initialized(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    runner.invoke(app, ["new", "Thing", "--yes", "--json"])

    result = runner.invoke(app, ["list", "--json"])
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert payload["count"] == 1
