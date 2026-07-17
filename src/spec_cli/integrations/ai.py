from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

DRAFT_PROMPT = """\
You are a senior software architect writing a production-quality spec for: "{title}"

{context_section}{glossary_section}Use this template structure exactly — preserve all section headings:
{template_body}

## Filling instructions

**General rules:**
- Replace every `>` blockquote instruction with real content for "{title}". Remove the instruction text.
- Replace every `[placeholder]` with specific content. Never leave brackets in the output.
- Be concrete. Avoid "should be fast", "good UX", "handle errors". State measurable outcomes.
- Keep the spec focused. If something is uncertain, say so explicitly rather than making it up.

**Section-specific rules:**

For `feature` specs:
- User Story: name a real persona (e.g. "admin user", "new subscriber"), not "user".
- Acceptance Criteria: each must be independently testable and binary (pass/fail).
  Bad: "The UI should feel responsive."
  Good: "Search returns results in < 300 ms for inputs up to 50 characters."
- Technical Notes: call out schema changes, new dependencies, and anything touching shared infrastructure.
- Out of Scope: always list at least one thing explicitly excluded to prevent scope creep.

For `bug` specs:
- Reproduction Steps: write a deterministic recipe. Include exact inputs and environment.
- Minimal repro: write a real curl command or code snippet if possible.
- Root Cause: write "Under investigation" if not known — do not invent a root cause.
- Fix Plan: be specific enough that an engineer can implement without guessing.

For `api` specs:
- Data Models: define every shared type used across endpoints.
- Each endpoint: include real JSON shapes with typed fields, not `{{}}`.
- Errors table: list at least 3 realistic error conditions per endpoint.
- Pagination: specify cursor-based or offset-based, with exact response shape.

For `adr` specs:
- Decision Drivers: list 2–4 explicit criteria that constrain the choice.
- Alternatives: each rejected option must have a specific reason tied to a driver.
- Consequences — Negative: list at least one honest downside. ADRs without negatives are not credible.
- Review date: always set a trigger condition or calendar date.

**Human Gate Checklist — CRITICAL:**
This section is what the human uses to decide pass/fail. It must be specific to "{title}".
- Replace every placeholder with a REAL command or scenario for this exact spec.
- Use the project's actual test commands from context (e.g. `pytest`, `npm test`, `cargo test`).
- The happy path step must name exact inputs/endpoints/actions and expected outputs.
- The edge case must be specific — not "try an invalid input" but "send an email without @domain — expect 422".
- Every item must be completable in under 5 minutes.
- If the test command is unknown, write a reasonable default and append `# VERIFY`.
- Classify every item with a lowercase marker at the start of the item text: `[agent]` for mechanical checks an agent can run and prove (test/lint/diff commands, deterministic curl calls), `[human]` for judgment calls (product behavior, UX quality, intent-vs-done). When in doubt, use `[human]` — unmarked items default to human anyway.

**Glossary — shared vocabulary:**
- Reuse the project's existing terms below exactly as defined. Don't invent a new name for something already named.
- If this spec introduces a genuinely new domain term that other specs will need to reuse (not a one-off implementation detail), propose it by appending — after the spec body, nothing else after it — a block exactly like:
  <!-- GLOSSARY-PROPOSALS
  - **Term**: one-line definition
  -->
- Omit that block entirely if there's nothing worth proposing. Most specs won't need it.

Return only the markdown content (plus the optional glossary block at the very end) — no preamble, no explanation, no code fences wrapping the entire output.\
"""


def _build_prompt(title: str, template: str, context: str, glossary: str = "") -> str:
    tpl_dir = Path(__file__).parent.parent / "templates"
    tpl_path = tpl_dir / f"{template}.md"
    template_body = tpl_path.read_text() if tpl_path.exists() else "## Overview\n\n## Details\n"
    context_section = f"Project context:\n{context}\n\n" if context.strip() else ""
    glossary_section = (
        f"Existing glossary (reuse these terms):\n{glossary}\n\n" if glossary.strip() else ""
    )
    return DRAFT_PROMPT.format(
        title=title,
        template_body=template_body.replace("{", "{{").replace("}", "}}"),
        context_section=context_section.replace("{", "{{").replace("}", "}}"),
        glossary_section=glossary_section.replace("{", "{{").replace("}", "}}"),
    )


_GLOSSARY_BLOCK_RE = re.compile(r"<!--\s*GLOSSARY-PROPOSALS\s*(.*?)-->", re.DOTALL)


def extract_glossary_proposals(body: str) -> tuple[str, list[str]]:
    """Strip a trailing GLOSSARY-PROPOSALS comment block from AI-drafted body. Returns (clean_body, terms)."""
    m = _GLOSSARY_BLOCK_RE.search(body)
    if not m:
        return body, []
    terms = [
        line.strip().lstrip("- ").strip()
        for line in m.group(1).splitlines()
        if line.strip().startswith("-")
    ]
    clean_body = (body[: m.start()] + body[m.end() :]).rstrip() + "\n"
    return clean_body, [t for t in terms if t]


def _via_claude_code(prompt: str) -> str:
    """Call `claude -p <prompt>` as a subprocess (uses the active Claude Code session)."""
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
    return result.stdout.strip()


def _via_anthropic(prompt: str, model: str) -> str:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _via_openai(prompt: str, model: str, base_url: str) -> str:
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "sk-placeholder")
    client = openai.OpenAI(api_key=api_key, base_url=base_url or None)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def draft_spec_content(
    title: str,
    template: str,
    context: str = "",
    provider: str = "claude-code",
    model: str = "",
    base_url: str = "",
    glossary: str = "",
) -> str:
    """
    Draft spec content via the configured AI provider.

    provider: "claude-code" | "anthropic" | "openai"
    model: provider-specific model name (optional, uses sensible defaults)
    base_url: for openai provider — allows Ollama, Groq, etc.
    glossary: existing approved glossary terms (from constitution.md) to keep terminology consistent
    """
    prompt = _build_prompt(title, template, context, glossary)

    if provider == "claude-code":
        try:
            return _via_claude_code(prompt)
        except FileNotFoundError:
            raise RuntimeError(
                "Claude Code CLI (`claude`) not found. "
                "Set ai_provider to 'anthropic' or 'openai' in .spec/config.yaml."
            )

    if provider == "anthropic":
        return _via_anthropic(prompt, model or "claude-opus-4-5")

    if provider == "openai":
        if not base_url and not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OpenAI provider requires OPENAI_API_KEY or ai_base_url in config.yaml."
            )
        return _via_openai(prompt, model or "gpt-4o", base_url)

    raise RuntimeError(f"Unknown ai_provider: '{provider}'. Use claude-code, anthropic, or openai.")
