from pathlib import Path

from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()

_TEMPLATES_DIR = Path(__file__).parent.parent / "src" / "spec_cli" / "templates"

_ORDERING_PHRASES = ("thinnest end-to-end slice", "one increment")


def test_feature_template_has_tracer_bullet_guidance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    import json

    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec

    spec = find_spec(tmp_path, spec_id)
    for phrase in _ORDERING_PHRASES:
        assert phrase in spec.body


def test_api_template_has_tracer_bullet_guidance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    result = runner.invoke(app, ["new", "Thing", "--template", "api", "--yes", "--json"])
    import json

    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec

    spec = find_spec(tmp_path, spec_id)
    for phrase in _ORDERING_PHRASES:
        assert phrase in spec.body


def test_other_templates_have_no_tracer_bullet_guidance():
    unaffected = ["bug", "adr", "data-pipeline", "experiment"]
    for name in unaffected:
        body = (_TEMPLATES_DIR / f"{name}.md").read_text()
        for phrase in _ORDERING_PHRASES:
            assert phrase not in body


def test_review_prompt_includes_ac_ordering_check_for_feature_template(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    import json

    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    captured = {}

    def fake_call_ai(prompt, provider, model, base_url):
        captured["prompt"] = prompt
        return "### Verdict\n**APPROVE** — looks fine."

    monkeypatch.setattr("spec_cli.commands.review._call_ai", fake_call_ai)

    result = runner.invoke(app, ["review", spec_id])

    assert result.exit_code == 0
    assert "AC ordering" in captured["prompt"]


def test_review_prompt_excludes_ac_ordering_check_for_bug_template(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    import json

    result = runner.invoke(app, ["new", "Thing", "--template", "bug", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    captured = {}

    def fake_call_ai(prompt, provider, model, base_url):
        captured["prompt"] = prompt
        return "### Verdict\n**APPROVE** — looks fine."

    monkeypatch.setattr("spec_cli.commands.review._call_ai", fake_call_ai)

    result = runner.invoke(app, ["review", spec_id])

    assert result.exit_code == 0
    assert "AC ordering" not in captured["prompt"]
