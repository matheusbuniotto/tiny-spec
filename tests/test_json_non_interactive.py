import json

import pytest
import typer
from typer.testing import CliRunner

from spec_cli.commands.init import cmd_init
from spec_cli.commands.lifecycle import cmd_advance
from spec_cli.commands.new import cmd_new
from spec_cli.main import app

runner = CliRunner()


def _init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cmd_init(tmp_path, author="", yes=True, json_out=True)


def test_new_json_mode_never_prompts(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    capsys.readouterr()  # discard init's JSON line

    cmd_new(
        "Add widget picker", None, None, None, yes=False, json_out=True, ai=False, root=tmp_path
    )

    out = json.loads(capsys.readouterr().out)
    assert out["title"] == "Add widget picker"
    assert out["status"] == "draft"


def test_new_json_mode_missing_title_errors_cleanly(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    capsys.readouterr()

    with pytest.raises(typer.Exit) as exc_info:
        cmd_new("", None, None, None, yes=False, json_out=True, ai=False, root=tmp_path)

    assert exc_info.value.exit_code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"] == "title_required"


def test_advance_to_gate_json_mode_without_note_errors_cleanly(tmp_path, monkeypatch, capsys):
    _init(tmp_path, monkeypatch)
    capsys.readouterr()
    cmd_new("Add widget picker", None, None, None, yes=True, json_out=True, ai=False, root=tmp_path)
    capsys.readouterr()
    cmd_advance("0001", None, yes=True, json_out=True, root=tmp_path)  # draft -> approved
    capsys.readouterr()
    cmd_advance("0001", None, yes=True, json_out=True, root=tmp_path)  # approved -> in-progress
    capsys.readouterr()

    with pytest.raises(typer.Exit) as exc_info:
        cmd_advance("0001", None, yes=False, json_out=True, root=tmp_path)

    assert exc_info.value.exit_code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"] == "notes_required"


def test_exit_code_contract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "--yes", "--json"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["new", "A spec", "--yes", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["title"] == "A spec"

    result = runner.invoke(app, ["show", "9999", "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"] == "not_found"

    result = runner.invoke(app, ["not-a-real-command"])
    assert result.exit_code == 2
