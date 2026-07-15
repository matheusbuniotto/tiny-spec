import json
from datetime import datetime, timedelta

from typer.testing import CliRunner

from spec_cli.main import app
from spec_cli.models import SpecStatus
from spec_cli.storage import find_spec, save_spec

runner = CliRunner()


def _init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])


def _new_spec(template="feature", parent=""):
    args = ["new", "Thing", "--template", template, "--yes", "--json"]
    if parent:
        args += ["--parent", parent]
    result = runner.invoke(app, args)
    return json.loads(result.stdout)["id"]


def test_clean_project_has_no_issues(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    _new_spec()

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "no issues" in result.stdout


def test_clean_project_json_has_zero_count(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    _new_spec()

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"count": 0, "findings": [], "help": ["spec list"]}


def test_dangling_blocked_by_is_flagged(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _new_spec()
    spec = find_spec(tmp_path, spec_id)
    spec.blocked_by = ["9999"]
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert spec_id in result.stdout
    assert "9999" in result.stdout


def test_dangling_blocked_by_json_shape(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _new_spec()
    spec = find_spec(tmp_path, spec_id)
    spec.blocked_by = ["9999"]
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["count"] == 1
    finding = payload["findings"][0]
    assert finding["type"] == "dangling_blocked_by"
    assert finding["spec_id"] == spec_id
    assert "hint" in finding and finding["hint"]
    assert payload["help"] == ["spec list"]


def test_dangling_parent_is_flagged(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _new_spec()
    spec = find_spec(tmp_path, spec_id)
    spec.parent = "9999"
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    types = [f["type"] for f in json.loads(result.stdout)["findings"]]
    assert "dangling_parent" in types


def test_in_progress_with_no_assignee_is_flagged(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _new_spec()
    spec = find_spec(tmp_path, spec_id)
    spec.status = SpecStatus.IN_PROGRESS
    spec.assignee = ""
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    findings = json.loads(result.stdout)["findings"]
    assert any(f["type"] == "unassigned_in_progress" and f["spec_id"] == spec_id for f in findings)


def test_stale_claim_is_flagged(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _new_spec()
    spec = find_spec(tmp_path, spec_id)
    spec.status = SpecStatus.IN_PROGRESS
    spec.assignee = "agent"
    spec.updated_at = datetime.utcnow() - timedelta(days=4)
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    findings = json.loads(result.stdout)["findings"]
    assert any(f["type"] == "stale_claim" and f["spec_id"] == spec_id for f in findings)


def test_at_gate_missing_checklist_is_flagged(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _new_spec()
    spec = find_spec(tmp_path, spec_id)
    spec.status = SpecStatus.AT_GATE
    spec.body = spec.body.split("## Human Gate Checklist")[0]
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    findings = json.loads(result.stdout)["findings"]
    assert any(f["type"] == "missing_gate_checklist" and f["spec_id"] == spec_id for f in findings)


def test_map_with_all_children_done_is_flagged(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    map_id = _new_spec(template="map")
    child_id = _new_spec(parent=map_id)
    child = find_spec(tmp_path, child_id)
    child.status = SpecStatus.IMPLEMENTED
    save_spec(child, tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    findings = json.loads(result.stdout)["findings"]
    assert any(f["type"] == "map_ready_to_close" and f["spec_id"] == map_id for f in findings)


def test_circular_blocked_by_is_flagged(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    a_id = _new_spec()
    b_id = _new_spec()
    a = find_spec(tmp_path, a_id)
    a.blocked_by = [b_id]
    save_spec(a, tmp_path)
    b = find_spec(tmp_path, b_id)
    b.blocked_by = [a_id]
    save_spec(b, tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    findings = json.loads(result.stdout)["findings"]
    assert any(f["type"] == "circular_blocked_by" for f in findings)
