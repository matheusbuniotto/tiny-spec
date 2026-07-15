import json

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()


def _new_spec(tmp_path, monkeypatch, template="feature"):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", template, "--yes", "--json"])
    return json.loads(result.stdout)["id"]


def test_pr_body_prints_intent_risk_evidence_headings(tmp_path, monkeypatch):
    spec_id = _new_spec(tmp_path, monkeypatch)

    result = runner.invoke(app, ["pr-body", spec_id])

    assert result.exit_code == 0
    assert "## Intent" in result.stdout
    assert "## Risk" in result.stdout
    assert "## Evidence" in result.stdout


def test_pr_body_intent_derives_from_problem_and_solution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = find_spec(tmp_path, spec_id)
    spec.body = spec.body.replace(
        "> What specific problem does this solve? Who is affected and how often?\n"
        "> Bad: \"Users can't find things.\" Good: \"New users abandon onboarding at step 3 because the next action isn't obvious.\"",
        "Users can't tell why their build failed.",
    ).replace(
        "> High-level approach in 2–4 sentences. What will exist after this is implemented that doesn't exist now?",
        "Surface the failing step name in the CLI output.",
    )
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["pr-body", spec_id])

    assert "Users can't tell why their build failed." in result.stdout
    assert "Surface the failing step name in the CLI output." in result.stdout


def test_pr_body_risk_derives_from_out_of_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = find_spec(tmp_path, spec_id)
    spec.body = spec.body.replace(
        "> What are we explicitly NOT doing in this spec? This prevents scope creep.\n"
        "> Example: \"Pagination is out of scope — we'll add it in spec 0007.\"",
        "No mobile support in this pass.",
    )
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["pr-body", spec_id])

    assert "No mobile support in this pass." in result.stdout


def test_pr_body_evidence_lists_ac_checkbox_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = find_spec(tmp_path, spec_id)
    spec.body = spec.body.replace(
        "- [ ] **AC1**: [Observable outcome — not an implementation detail]",
        "- [x] **AC1**: Widget renders on load",
    )
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["pr-body", spec_id])

    assert "[x] AC1: Widget renders on load" in result.stdout


def test_pr_body_json_emits_structured_fields(tmp_path, monkeypatch):
    spec_id = _new_spec(tmp_path, monkeypatch)

    result = runner.invoke(app, ["pr-body", spec_id, "--json"])

    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert set(["intent", "risk", "evidence"]).issubset(out.keys())


def test_pr_body_handles_bare_spec_gracefully(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = find_spec(tmp_path, spec_id)
    spec.body = "## Acceptance Criteria\n\n"  # strip everything else
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["pr-body", spec_id])

    assert result.exit_code == 0
    assert "No Out of Scope section" in result.stdout
    assert "No Acceptance Criteria or gate notes recorded yet" in result.stdout


def test_pr_body_intent_keeps_content_written_as_blockquote(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = find_spec(tmp_path, spec_id)
    spec.body = spec.body.replace(
        "> As a **[type of user]**, I want **[goal]** so that **[reason/value]**.",
        "> As a **user**, I want **fast search** so that **I find things quickly**.",
    )
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["pr-body", spec_id])

    assert "As a **user**, I want **fast search** so that **I find things quickly**." in result.stdout
