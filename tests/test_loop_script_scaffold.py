"""spec-loop.sh scaffold — opt-in via `spec init --loop-script`."""

from __future__ import annotations

import json
import os
import stat

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def _init(tmp_path, *extra):
    return runner.invoke(app, ["init", "--yes", "--json", "--root", str(tmp_path), *extra])


def test_loop_script_is_opt_in(tmp_path):
    result = _init(tmp_path)
    assert json.loads(result.stdout)["loop_script"] is False
    assert not (tmp_path / "scripts" / "spec-loop.sh").exists()


def test_loop_script_with_flag(tmp_path):
    result = _init(tmp_path, "--loop-script")
    assert result.exit_code == 0
    assert json.loads(result.stdout)["loop_script"] is True
    target = tmp_path / "scripts" / "spec-loop.sh"
    assert target.exists()
    assert "spec-loop.sh" in target.read_text()
    assert os.stat(target).st_mode & stat.S_IXUSR


def test_greenfield_loop_script_with_flag(tmp_path):
    target_dir = tmp_path / "newproj"
    result = runner.invoke(app, ["init", str(target_dir), "--yes", "--json", "--loop-script"])
    assert result.exit_code == 0
    assert "scripts/spec-loop.sh" in json.loads(result.stdout)["files"]
    assert (target_dir / "scripts" / "spec-loop.sh").exists()


def test_existing_loop_script_left_untouched(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    handwritten = "#!/usr/bin/env bash\necho custom\n"
    (scripts_dir / "spec-loop.sh").write_text(handwritten)
    result = _init(tmp_path, "--loop-script")
    assert json.loads(result.stdout)["loop_script"] is False
    assert (scripts_dir / "spec-loop.sh").read_text() == handwritten
