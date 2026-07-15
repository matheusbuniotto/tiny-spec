import json

from typer.testing import CliRunner

from spec_cli.config import Config, Kata, load_config, save_config
from spec_cli.main import app

runner = CliRunner()


def _write_yaml(tmp_path, text):
    sd = tmp_path / ".spec"
    sd.mkdir()
    (sd / "config.yaml").write_text(text)


def test_load_config_reads_checks_key(tmp_path):
    _write_yaml(
        tmp_path,
        "checks:\n  - name: tests\n    command: pytest\n    description: Full suite\n",
    )
    cfg = load_config(tmp_path)
    assert cfg.katas == [Kata(name="tests", command="pytest", description="Full suite")]


def test_load_config_still_reads_legacy_katas_key(tmp_path):
    _write_yaml(
        tmp_path,
        "katas:\n  - name: lint\n    command: ruff check .\n    description: Linter\n",
    )
    cfg = load_config(tmp_path)
    assert cfg.katas == [Kata(name="lint", command="ruff check .", description="Linter")]


def test_save_config_writes_checks_key_not_katas(tmp_path):
    sd = tmp_path / ".spec"
    sd.mkdir()
    cfg = Config(katas=[Kata(name="tests", command="pytest")])
    save_config(cfg, tmp_path)

    raw = (sd / "config.yaml").read_text()
    assert "checks:" in raw
    assert "katas:" not in raw


def _init_with_one_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    cfg = load_config(tmp_path)
    cfg.katas = [Kata(name="tests", command='python -c "import sys; sys.exit(0)"')]
    save_config(cfg, tmp_path)


def test_verify_runs_configured_checks(tmp_path, monkeypatch):
    _init_with_one_check(tmp_path, monkeypatch)

    result = runner.invoke(app, ["verify", "--json"])

    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert out["all_passed"] is True
    assert out["total"] == 1
    assert out["checks"][0]["name"] == "tests"
    assert "katas" not in out


def test_run_kata_still_works_but_is_hidden(tmp_path, monkeypatch):
    _init_with_one_check(tmp_path, monkeypatch)

    result = runner.invoke(app, ["run-kata", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["all_passed"] is True

    help_result = runner.invoke(app, ["--help"])
    assert "run-kata" not in help_result.stdout
    assert "verify" in help_result.stdout


def _failing_check_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    cfg = load_config(tmp_path)
    cfg.katas = [Kata(name="tests", command='python -c "import sys; sys.exit(1)"')]
    save_config(cfg, tmp_path)
    new_result = runner.invoke(app, ["new", "Thing", "--yes", "--json"])
    spec_id = json.loads(new_result.stdout)["id"]
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # draft -> approved
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # approved -> in-progress
    return spec_id


def test_advance_skip_checks_flag_bypasses_failing_checks(tmp_path, monkeypatch):
    spec_id = _failing_check_project(tmp_path, monkeypatch)

    result = runner.invoke(
        app, ["advance", spec_id, "--skip-checks", "--note", "known flaky", "--yes", "--json"]
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "at-gate"


def test_advance_skip_kata_alias_still_works(tmp_path, monkeypatch):
    spec_id = _failing_check_project(tmp_path, monkeypatch)

    result = runner.invoke(
        app, ["advance", spec_id, "--skip-kata", "--note", "known flaky", "--yes", "--json"]
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "at-gate"


def test_advance_blocked_by_failing_checks_reports_checks_failed(tmp_path, monkeypatch):
    spec_id = _failing_check_project(tmp_path, monkeypatch)

    result = runner.invoke(app, ["advance", spec_id, "--note", "trying anyway", "--yes", "--json"])

    assert result.exit_code == 1
    out = json.loads(result.stdout)
    assert out["error"] == "checks_failed"
