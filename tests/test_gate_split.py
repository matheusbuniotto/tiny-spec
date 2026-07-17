"""Spec 0012 — gate checklist split: [agent] vs [human] items."""

import json
from pathlib import Path

from typer.testing import CliRunner

from spec_cli.commands.gate_check import classify_checklist_item, strip_class_markers
from spec_cli.main import app
from spec_cli.storage import find_spec, save_spec

runner = CliRunner()

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "src" / "spec_cli" / "templates"


def _init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--yes", "--json"])


def _spec_with_checklist(tmp_path, checklist_md):
    result = runner.invoke(app, ["new", "Thing", "--yes", "--json"])
    spec_id = json.loads(result.stdout)["id"]
    spec = find_spec(tmp_path, spec_id)
    spec.body = f"## Overview\n\nStuff.\n\n## Human Gate Checklist\n\n{checklist_md}\n"
    save_spec(spec, tmp_path)
    return spec_id


def _gate_check_json(spec_id):
    result = runner.invoke(app, ["gate-check", spec_id, "--json"])
    assert result.exit_code == 0
    return json.loads(result.stdout)


# --- AC1: marked items land in the right array, markers stripped ---


def test_agent_marked_item_lands_in_agent_verifiable(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _spec_with_checklist(
        tmp_path,
        "- [ ] [agent] Run the tests: pytest -q\n- [ ] [human] Judge the UX",
    )

    out = _gate_check_json(spec_id)

    assert out["agent_verifiable"] == ["Run the tests: pytest -q"]
    assert out["human_only"] == ["Judge the UX"]


# --- AC2: unmarked items default to human_only ---


def test_unmarked_items_default_to_human_only(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _spec_with_checklist(tmp_path, "- [ ] Run the tests\n- [ ] Walk the happy path")

    out = _gate_check_json(spec_id)

    assert out["agent_verifiable"] == []
    assert out["human_only"] == ["Run the tests", "Walk the happy path"]


def test_marker_grammar_rejects_case_unknown_and_midtext(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _spec_with_checklist(
        tmp_path,
        "- [ ] [Agent] Uppercase marker\n"
        "- [ ] [bot] Unknown marker\n"
        "- [ ] Check the [agent] flow mid-text",
    )

    out = _gate_check_json(spec_id)

    assert out["agent_verifiable"] == []
    # not a marker → item text stays untouched, bracket included
    assert out["human_only"] == [
        "[Agent] Uppercase marker",
        "[bot] Unknown marker",
        "Check the [agent] flow mid-text",
    ]


# --- AC3: flat list keeps its shape with markers stripped; raw string verbatim ---


def test_flat_items_keep_order_with_markers_stripped(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _spec_with_checklist(
        tmp_path,
        "- [ ] [agent] Run the tests\n- [ ] Unmarked item\n- [ ] [human] Judge it",
    )

    out = _gate_check_json(spec_id)

    assert out["gate_checklist_items"] == ["Run the tests", "Unmarked item", "Judge it"]


def test_raw_gate_checklist_string_keeps_markers_verbatim(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _spec_with_checklist(tmp_path, "- [ ] [agent] Run the tests")

    out = _gate_check_json(spec_id)

    assert out["gate_checklist"] == "- [ ] [agent] Run the tests"


def test_gate_check_panel_strips_markers(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _spec_with_checklist(tmp_path, "- [ ] [agent] Run tests\n- [ ] [human] Judge it")

    result = runner.invoke(app, ["gate-check", spec_id])

    assert result.exit_code == 0
    assert "[agent]" not in result.stdout
    assert "[human]" not in result.stdout
    assert "Run tests" in result.stdout
    assert "Judge it" in result.stdout


def test_at_gate_transition_panel_strips_markers(tmp_path, monkeypatch):
    _init(tmp_path, monkeypatch)
    spec_id = _spec_with_checklist(tmp_path, "- [ ] [agent] Run tests")
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # draft -> approved
    runner.invoke(app, ["advance", spec_id, "--yes", "--json"])  # approved -> in-progress

    result = runner.invoke(app, ["advance", spec_id, "--note", "done", "--yes"])

    assert result.exit_code == 0
    assert "[agent]" not in result.stdout
    assert "Run tests" in result.stdout


def test_legacy_unmarked_checklist_is_unchanged_end_to_end(tmp_path, monkeypatch):
    """Backward compat: an unmarked legacy checklist parses exactly as before."""
    _init(tmp_path, monkeypatch)
    checklist = "- [ ] Run the tests: pytest -q\n- [ ] Check the diff: git diff main"
    spec_id = _spec_with_checklist(tmp_path, checklist)

    out = _gate_check_json(spec_id)

    assert out["gate_checklist"] == checklist
    assert out["gate_checklist_items"] == [
        "Run the tests: pytest -q",
        "Check the diff: git diff main",
    ]
    assert out["agent_verifiable"] == []
    assert out["human_only"] == out["gate_checklist_items"]


# --- unit level: classify + strip helpers ---


def test_classify_checklist_item_grammar():
    assert classify_checklist_item("[agent] Run tests") == ("agent", "Run tests")
    assert classify_checklist_item("[human] Judge it") == ("human", "Judge it")
    assert classify_checklist_item("Plain item") == ("human", "Plain item")
    assert classify_checklist_item("[Agent] Nope") == ("human", "[Agent] Nope")
    assert classify_checklist_item("[ci] Nope") == ("human", "[ci] Nope")


def test_strip_class_markers_only_touches_marked_list_lines():
    md = "- [ ] [agent] Run tests\n- [x] [human] Judged\n- [ ] Plain\nNot a list [agent] line"
    assert strip_class_markers(md) == (
        "- [ ] Run tests\n- [x] Judged\n- [ ] Plain\nNot a list [agent] line"
    )


# --- AC5: feature/api/bug templates are born classified ---


def test_templates_ship_with_classified_examples():
    for name in ("feature", "api", "bug"):
        content = (TEMPLATES_DIR / f"{name}.md").read_text()
        checklist = content.split("## Human Gate Checklist", 1)[1]
        assert "- [ ] [agent]" in checklist, f"{name}.md has no [agent] example"
        assert "- [ ] [human]" in checklist, f"{name}.md has no [human] example"


# --- AC4: skill.md at-gate section instructs pre-verify + verbatim relay ---


def test_skill_md_instructs_agent_preverify_and_verbatim_relay():
    for path in (REPO_ROOT / "skill.md", REPO_ROOT / "src" / "spec_cli" / "SKILL.md"):
        content = path.read_text()
        assert "agent_verifiable" in content, f"{path} missing agent_verifiable guidance"
        assert "human_only" in content, f"{path} missing human_only guidance"
        assert "verbatim" in content, f"{path} missing verbatim-relay rule"


def test_skill_md_copies_are_in_sync():
    root_copy = (REPO_ROOT / "skill.md").read_text()
    packaged_copy = (REPO_ROOT / "src" / "spec_cli" / "SKILL.md").read_text()
    assert root_copy == packaged_copy
