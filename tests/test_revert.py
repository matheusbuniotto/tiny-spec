"""spec revert must actually be able to send an in-progress spec back to draft.

Previously TRANSITIONS[IN_PROGRESS] didn't include DRAFT, so `spec revert`
always failed with invalid_transition once a spec was claimed — silently,
in spec-loop.sh, since its `handle_failure()` swallows the command's exit
code. A failed implementation attempt was left stuck in-progress forever
with no failure reason recorded anywhere.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def _new_spec(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--yes", "--json"])
    return json.loads(result.stdout)["id"]


def test_revert_from_in_progress_succeeds(tmp_path, monkeypatch):
    spec_id = _new_spec(tmp_path, monkeypatch)
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # draft -> approved
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # approved -> in-progress

    result = runner.invoke(app, ["revert", spec_id, "--note", "agent failed", "--yes", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "draft"


def test_revert_from_approved_still_works(tmp_path, monkeypatch):
    spec_id = _new_spec(tmp_path, monkeypatch)
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # draft -> approved

    result = runner.invoke(app, ["revert", spec_id, "--yes", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "draft"


def test_revert_from_draft_is_rejected(tmp_path, monkeypatch):
    spec_id = _new_spec(tmp_path, monkeypatch)

    result = runner.invoke(app, ["revert", spec_id, "--yes", "--json"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"] == "invalid_transition"
