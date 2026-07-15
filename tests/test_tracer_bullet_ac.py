import re
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spec_cli.main import app

runner = CliRunner()

_NO_CLAUDE_CLI = shutil.which("claude") is None


def _blockers_section(review_text: str) -> str:
    m = re.search(r"### .*Blockers\s*\n(.*?)(?=\n### |\Z)", review_text, re.DOTALL)
    return m.group(1) if m else ""


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
    from spec_cli.commands.new import AVAILABLE_TEMPLATES
    from spec_cli.commands.review import TRACER_BULLET_TEMPLATES

    unaffected = [t for t in AVAILABLE_TEMPLATES if t not in TRACER_BULLET_TEMPLATES and t != "map"]
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


def _flatten_ac(spec, unrelated_criteria):
    lines = ["## Acceptance Criteria", ""]
    for i, text in enumerate(unrelated_criteria, start=1):
        lines.append(f"- [ ] **AC{i}**: {text}")
    spec.body = re.sub(
        r"## Acceptance Criteria\n.*?(?=\n## |\Z)",
        "\n".join(lines) + "\n",
        spec.body,
        flags=re.DOTALL,
    )
    return spec


@pytest.mark.integration
@pytest.mark.skipif(_NO_CLAUDE_CLI, reason="claude CLI not installed")
def test_review_flags_flat_ac_ordering_via_real_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    import json

    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = _flatten_ac(
        find_spec(tmp_path, spec_id),
        [
            "Admin dashboard shows total revenue",
            "Search results are paginated",
            "Login page has a 'forgot password' link",
        ],
    )
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["review", spec_id, "--json"])

    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert "ordering" in _blockers_section(out["review"]).lower()


@pytest.mark.integration
@pytest.mark.skipif(_NO_CLAUDE_CLI, reason="claude CLI not installed")
def test_review_does_not_flag_properly_ordered_ac_via_real_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])
    import json

    result = runner.invoke(app, ["new", "Thing", "--template", "feature", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]

    from spec_cli.storage import find_spec, save_spec

    spec = _flatten_ac(
        find_spec(tmp_path, spec_id),
        [
            "Typing a query into the search box filters the catalog grid to items whose "
            "name contains the query (case-insensitive substring match)",
            "Clearing the search box restores the full catalog grid",
            "A query matching zero items shows a 'No widgets found' empty state instead "
            "of a blank grid",
        ],
    )
    save_spec(spec, tmp_path)

    result = runner.invoke(app, ["review", spec_id, "--json"])

    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert "ordering" not in _blockers_section(out["review"]).lower()


def test_review_quick_flag_sends_a_shorter_prompt(tmp_path, monkeypatch):
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

    full_result = runner.invoke(app, ["review", spec_id])
    full_prompt = captured["prompt"]

    quick_result = runner.invoke(app, ["review", spec_id, "--quick"])
    quick_prompt = captured["prompt"]

    assert full_result.exit_code == 0
    assert quick_result.exit_code == 0
    assert len(quick_prompt) < len(full_prompt)
    assert "Constitution compliance" not in quick_prompt
