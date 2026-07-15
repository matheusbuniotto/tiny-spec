import json

from typer.testing import CliRunner

from spec_cli.main import app
from spec_cli.storage import find_spec, save_spec

runner = CliRunner()


def _init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])


def _init_and_new(tmp_path, monkeypatch, template="feature", title="Thing"):
    _init(tmp_path, monkeypatch)
    result = runner.invoke(app, ["new", title, "--template", template, "--yes", "--json"])
    return json.loads(result.stdout)["id"]


# AC1 — help[] on next/show/list/advance/claim --json ------------------------


def test_next_json_includes_help(tmp_path, monkeypatch):
    _init_and_new(tmp_path, monkeypatch)
    result = runner.invoke(app, ["next", "--json"])
    out = json.loads(result.stdout)
    assert out["help"]
    assert any("spec" in h for h in out["help"])


def test_show_json_includes_help(tmp_path, monkeypatch):
    spec_id = _init_and_new(tmp_path, monkeypatch)
    result = runner.invoke(app, ["show", spec_id, "--json"])
    out = json.loads(result.stdout)
    assert out["help"]
    assert any("spec" in h for h in out["help"])


def test_list_json_includes_help(tmp_path, monkeypatch):
    _init_and_new(tmp_path, monkeypatch)
    result = runner.invoke(app, ["list", "--json"])
    out = json.loads(result.stdout)
    assert out["help"]


def test_advance_json_includes_help(tmp_path, monkeypatch):
    spec_id = _init_and_new(tmp_path, monkeypatch)
    result = runner.invoke(app, ["advance", spec_id, "--yes", "--json"])
    out = json.loads(result.stdout)
    assert out["help"]


def test_claim_json_includes_help(tmp_path, monkeypatch):
    spec_id = _init_and_new(tmp_path, monkeypatch)
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # draft -> approved
    result = runner.invoke(app, ["claim", spec_id, "--yes", "--json"])
    out = json.loads(result.stdout)
    assert out["help"]


# AC2 — not-found errors include a recovery command --------------------------


def test_show_not_found_json_includes_help(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    result = runner.invoke(app, ["show", "9999", "--json"])
    out = json.loads(result.stdout)
    assert out["error"] == "not_found"
    assert out["help"]


# AC3 — list --json envelope + human filter naming ---------------------------


def test_list_json_empty_envelope(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    result = runner.invoke(app, ["list", "--status", "at-gate", "--json"])
    out = json.loads(result.stdout)
    assert out["count"] == 0
    assert out["specs"] == []


def test_list_json_nonempty_envelope(tmp_path, monkeypatch):
    _init_and_new(tmp_path, monkeypatch)
    result = runner.invoke(app, ["list", "--json"])
    out = json.loads(result.stdout)
    assert out["count"] == 1
    assert len(out["specs"]) == 1


def test_list_human_empty_names_the_active_filter(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    result = runner.invoke(app, ["list", "--status", "at-gate"])
    assert "0 specs match --status at-gate" in result.stdout


def test_list_human_empty_with_no_filter_keeps_generic_message(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    result = runner.invoke(app, ["list"])
    assert "No specs found" in result.stdout


# AC4 — truncation hint on long bodies ---------------------------------------


def test_export_json_truncates_long_body_with_hint(tmp_path, monkeypatch):
    spec_id = _init_and_new(tmp_path, monkeypatch)
    spec = find_spec(tmp_path, spec_id)
    spec.body = "x" * 10000
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["export", "--json"])
    out = json.loads(result.stdout)
    body = next(s["body"] for s in out["specs"] if s["id"] == spec_id)
    assert len(body) < 10000
    assert f"use spec show {spec_id} --json" in body


def test_export_json_does_not_truncate_short_body(tmp_path, monkeypatch):
    spec_id = _init_and_new(tmp_path, monkeypatch)
    result = runner.invoke(app, ["export", "--json"])
    out = json.loads(result.stdout)
    body = next(s["body"] for s in out["specs"] if s["id"] == spec_id)
    assert "truncated" not in body


def test_list_full_json_truncates_long_body_with_hint(tmp_path, monkeypatch):
    spec_id = _init_and_new(tmp_path, monkeypatch)
    spec = find_spec(tmp_path, spec_id)
    spec.body = "x" * 10000
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["list", "--full", "--json"])
    out = json.loads(result.stdout)
    body = out["specs"][0]["body"]
    assert len(body) < 10000
    assert f"use spec show {spec_id} --json" in body
