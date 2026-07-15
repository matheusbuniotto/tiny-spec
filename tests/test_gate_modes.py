import json

from typer.testing import CliRunner

from spec_cli.config import load_config
from spec_cli.main import app

runner = CliRunner()


def _write_yaml(tmp_path, text):
    sd = tmp_path / ".spec"
    sd.mkdir()
    (sd / "config.yaml").write_text(text)


def test_load_config_defaults_gate_to_local(tmp_path):
    _write_yaml(tmp_path, "author: someone\n")
    cfg = load_config(tmp_path)
    assert cfg.gate == "local"


def test_load_config_reads_explicit_gate(tmp_path):
    _write_yaml(tmp_path, "gate: pr\n")
    cfg = load_config(tmp_path)
    assert cfg.gate == "pr"


def test_spec_frontmatter_round_trips_gate_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    new_result = runner.invoke(app, ["new", "Thing", "--yes", "--json"])
    spec_id = json.loads(new_result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = find_spec(tmp_path, spec_id)
    spec.gate = "pr"
    save_spec(spec, tmp_path)

    reloaded = find_spec(tmp_path, spec_id)
    assert reloaded.gate == "pr"


def _project_at_in_progress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    new_result = runner.invoke(app, ["new", "Thing", "--yes", "--json"])
    spec_id = json.loads(new_result.stdout)["id"]
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # draft -> approved
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # approved -> in-progress
    return spec_id


def test_advance_with_note_unaffected_under_default_local_gate(tmp_path, monkeypatch):
    spec_id = _project_at_in_progress(tmp_path, monkeypatch)

    result = runner.invoke(
        app, ["advance", spec_id, "--note", "reviewed by hand", "--yes", "--json"]
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "at-gate"


def _project_at_in_progress_with_pr_gate(tmp_path, monkeypatch):
    spec_id = _project_at_in_progress(tmp_path, monkeypatch)
    from spec_cli.config import load_config, save_config

    cfg = load_config(tmp_path)
    cfg.gate = "pr"
    save_config(cfg, tmp_path)
    return spec_id


def test_advance_with_pr_flag_satisfies_gate_without_note(tmp_path, monkeypatch):
    spec_id = _project_at_in_progress_with_pr_gate(tmp_path, monkeypatch)

    result = runner.invoke(app, ["advance", spec_id, "--pr", "123", "--yes", "--json"])

    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert out["status"] == "at-gate"
    assert out["pr"] == "123"


def test_advance_neither_pr_nor_note_under_pr_gate_names_both_flags(tmp_path, monkeypatch):
    spec_id = _project_at_in_progress_with_pr_gate(tmp_path, monkeypatch)

    result = runner.invoke(app, ["advance", spec_id, "--yes", "--json"])

    assert result.exit_code == 1
    out = json.loads(result.stdout)
    assert out["error"] == "notes_required"
    assert "--pr" in out["hint"]
    assert "--note" in out["hint"]


def test_advance_neither_pr_nor_note_under_default_local_gate_unaffected(tmp_path, monkeypatch):
    spec_id = _project_at_in_progress(tmp_path, monkeypatch)

    result = runner.invoke(app, ["advance", spec_id, "--yes", "--json"])

    assert result.exit_code == 1
    out = json.loads(result.stdout)
    assert out["error"] == "notes_required"
    assert "hint" not in out


def test_gate_check_reports_effective_gate_mode(tmp_path, monkeypatch):
    spec_id = _project_at_in_progress_with_pr_gate(tmp_path, monkeypatch)

    result = runner.invoke(app, ["gate-check", spec_id, "--json"])

    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert out["gate_mode"] == "pr"


def test_show_reports_effective_gate_mode(tmp_path, monkeypatch):
    spec_id = _project_at_in_progress_with_pr_gate(tmp_path, monkeypatch)

    result = runner.invoke(app, ["show", spec_id, "--json"])

    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert out["gate_mode"] == "pr"
