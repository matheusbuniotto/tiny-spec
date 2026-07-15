import json
import shutil

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def _claimable_spec(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # draft -> approved
    return spec_id


def test_claim_worktree_creates_dir_and_branch(tmp_path, monkeypatch):
    spec_id = _claimable_spec(tmp_path, monkeypatch)

    result = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])
    payload = json.loads(result.stdout)

    try:
        assert result.exit_code == 0
        assert payload["status"] == "in-progress"
        assert payload["branch"] == f"spec/{spec_id}-thing"
        worktree_path = payload["worktree"]
        assert worktree_path.endswith(f"{tmp_path.name}-spec-{spec_id}")
        from pathlib import Path

        assert Path(worktree_path).is_dir()
        assert (Path(worktree_path) / ".spec").exists()
    finally:
        shutil.rmtree(payload["worktree"], ignore_errors=True)


def test_claim_worktree_twice_reuses_instead_of_erroring(tmp_path, monkeypatch):
    spec_id = _claimable_spec(tmp_path, monkeypatch)

    first = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])
    second = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])

    first_payload = json.loads(first.stdout)
    try:
        assert first.exit_code == 0
        assert second.exit_code == 0
        second_payload = json.loads(second.stdout)
        assert second_payload["idempotent"] is True
        assert second_payload["worktree"] == first_payload["worktree"]
        assert second_payload["branch"] == first_payload["branch"]
    finally:
        shutil.rmtree(first_payload["worktree"], ignore_errors=True)


def test_claim_without_worktree_flag_has_no_worktree_fields(tmp_path, monkeypatch):
    spec_id = _claimable_spec(tmp_path, monkeypatch)

    result = runner.invoke(app, ["claim", spec_id, "--yes", "--json"])
    payload = json.loads(result.stdout)

    assert result.exit_code == 0
    assert "worktree" not in payload
    assert "branch" not in payload


def test_advance_to_implemented_reminds_about_leftover_worktree(tmp_path, monkeypatch):
    spec_id = _claimable_spec(tmp_path, monkeypatch)
    claim_result = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])
    worktree_path = json.loads(claim_result.stdout)["worktree"]

    try:
        runner.invoke(app, ["advance", spec_id, "--note", "gate note", "--yes", "--json"])
        result = runner.invoke(app, ["advance", spec_id, "--note", "verified", "--yes", "--json"])
        payload = json.loads(result.stdout)

        assert payload["status"] == "implemented"
        assert payload["worktree"] == worktree_path
        assert "git worktree remove" in payload["worktree_remove_hint"]
    finally:
        shutil.rmtree(worktree_path, ignore_errors=True)
