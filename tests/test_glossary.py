import json

from spec_cli import constitution
from spec_cli.commands.new import cmd_new
from spec_cli.integrations.ai import extract_glossary_proposals
from spec_cli.storage import find_root


def test_extract_glossary_proposals_present():
    body = (
        "## Overview\n\nSome content.\n\n"
        "<!-- GLOSSARY-PROPOSALS\n"
        "- **Widget**: a reusable UI component\n"
        "- **Sprocket**: a backend processing unit\n"
        "-->\n"
    )
    clean, terms = extract_glossary_proposals(body)
    assert "GLOSSARY-PROPOSALS" not in clean
    assert "Some content." in clean
    assert terms == [
        "**Widget**: a reusable UI component",
        "**Sprocket**: a backend processing unit",
    ]


def test_extract_glossary_proposals_absent():
    body = "## Overview\n\nNo proposals here.\n"
    clean, terms = extract_glossary_proposals(body)
    assert clean == body
    assert terms == []


def test_approved_glossary_excludes_proposed(tmp_path):
    sd = tmp_path / ".spec"
    sd.mkdir()
    (sd / "constitution.md").write_text(
        "# Constitution\n\n"
        "## Glossary\n\n- **Widget**: a thing\n\n"
        "## Glossary — Proposed (review before promoting)\n\n- **Sprocket**: not yet approved\n"
    )
    text = constitution.approved_glossary(tmp_path)
    assert "Widget" in text
    assert "Sprocket" not in text


def test_propose_glossary_terms_dedups(tmp_path):
    sd = tmp_path / ".spec"
    sd.mkdir()
    (sd / "constitution.md").write_text("# Constitution\n\n## Glossary\n\n- **Widget**: a thing\n")

    added = constitution.propose_glossary_terms(
        tmp_path, ["**Widget**: a thing", "**Sprocket**: new term"]
    )
    assert added == ["**Sprocket**: new term"]

    text = constitution.read_constitution(tmp_path)
    assert "Glossary — Proposed" in text
    assert "Sprocket" in text

    # second proposal of the same term is skipped
    added_again = constitution.propose_glossary_terms(tmp_path, ["**Sprocket**: new term"])
    assert added_again == []


def test_cmd_new_ai_proposes_glossary_terms(tmp_path, monkeypatch):
    from spec_cli.commands.init import cmd_init

    monkeypatch.chdir(tmp_path)
    cmd_init(tmp_path, author="", yes=True, json_out=True)

    def fake_draft(*args, **kwargs):
        return (
            "## User Story\n\nAs a user...\n\n"
            "<!-- GLOSSARY-PROPOSALS\n- **Widget**: a reusable UI component\n-->\n"
        )

    monkeypatch.setattr("spec_cli.integrations.ai.draft_spec_content", fake_draft)

    cmd_new(
        "Add widget picker",
        "feature",
        None,
        None,
        yes=True,
        json_out=True,
        ai=True,
        root=tmp_path,
    )

    root = find_root(tmp_path)
    text = constitution.read_constitution(root)
    assert "Widget" in text
    assert "Glossary — Proposed" in text

    spec_path = next((root / ".spec" / "specs").glob("0001-*.md"))
    assert "GLOSSARY-PROPOSALS" not in spec_path.read_text()
