"""spec init / greenfield must gitignore .spec/logs/ — otherwise spec-loop.sh's
agent transcripts get swept into `git add -A` and bury real code diffs under
thousands of log lines (seen in the wild: a 230-line real diff buried under
28,906 lines of log noise)."""

import json

from typer.testing import CliRunner

from spec_cli.integrations.git import ensure_gitignore_entries
from spec_cli.main import app

runner = CliRunner()


def test_ensure_gitignore_entries_creates_file(tmp_path):
    changed = ensure_gitignore_entries(tmp_path, [".spec/logs/"])
    assert changed is True
    assert ".spec/logs/" in (tmp_path / ".gitignore").read_text()


def test_ensure_gitignore_entries_appends_to_existing(tmp_path):
    (tmp_path / ".gitignore").write_text("node_modules/\n")
    changed = ensure_gitignore_entries(tmp_path, [".spec/logs/"])
    assert changed is True
    content = (tmp_path / ".gitignore").read_text()
    assert "node_modules/" in content
    assert ".spec/logs/" in content


def test_ensure_gitignore_entries_is_idempotent(tmp_path):
    ensure_gitignore_entries(tmp_path, [".spec/logs/"])
    changed_again = ensure_gitignore_entries(tmp_path, [".spec/logs/"])
    assert changed_again is False
    content = (tmp_path / ".gitignore").read_text()
    assert content.count(".spec/logs/") == 1


def test_init_writes_gitignore_entry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--yes", "--json", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert ".spec/logs/" in (tmp_path / ".gitignore").read_text()


def test_greenfield_writes_gitignore_entry(tmp_path):
    target = tmp_path / "newproj"
    result = runner.invoke(app, ["init", str(target), "--yes", "--json"])
    assert result.exit_code == 0
    assert ".gitignore" in json.loads(result.stdout)["files"]
    assert ".spec/logs/" in (target / ".gitignore").read_text()
