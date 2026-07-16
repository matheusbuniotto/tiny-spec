import json
import shutil
import subprocess
from pathlib import Path

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


def test_claim_worktree_includes_install_step_hint(tmp_path, monkeypatch):
    spec_id = _claimable_spec(tmp_path, monkeypatch)

    result = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])
    payload = json.loads(result.stdout)

    try:
        assert "install step" in payload["worktree_hint"]
    finally:
        shutil.rmtree(payload["worktree"], ignore_errors=True)


def test_claim_worktree_failure_is_not_reported_as_success(tmp_path, monkeypatch):
    spec_id = _claimable_spec(tmp_path, monkeypatch)
    blocking_path = tmp_path.parent / f"{tmp_path.name}-spec-{spec_id}"
    blocking_path.mkdir()  # not a git worktree — `git worktree add` will refuse this path
    (blocking_path / "keep.txt").write_text("pre-existing, unrelated directory")

    try:
        result = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])
        payload = json.loads(result.stdout)

        assert "worktree_error" in payload
        assert "worktree" not in payload
        assert payload["status"] == "in-progress"  # the claim itself still succeeded

        human = runner.invoke(
            app, ["assign", spec_id, "other"]
        )  # reset assignee for a clean re-run
        assert human.exit_code == 0
    finally:
        shutil.rmtree(blocking_path, ignore_errors=True)


def test_claim_worktree_reuses_branch_after_worktree_manually_removed(tmp_path, monkeypatch):
    spec_id = _claimable_spec(tmp_path, monkeypatch)

    first = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])
    worktree_path = json.loads(first.stdout)["worktree"]

    # Simulate an agent tidying up its worktree by hand, leaving the branch behind.
    subprocess.run(
        ["git", "worktree", "remove", "--force", worktree_path], cwd=tmp_path, check=True
    )

    result = runner.invoke(app, ["claim", spec_id, "--worktree", "--yes", "--json"])
    payload = json.loads(result.stdout)

    try:
        assert result.exit_code == 0
        assert "worktree_error" not in payload
        assert payload["worktree"] == worktree_path
        assert Path(worktree_path).is_dir()
    finally:
        shutil.rmtree(worktree_path, ignore_errors=True)
