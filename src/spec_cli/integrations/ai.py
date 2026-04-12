from __future__ import annotations

import os
import subprocess
from pathlib import Path

DRAFT_PROMPT = """\
You are a senior software architect writing a production-quality spec for: "{title}"

{context_section}Use this template structure exactly — preserve all section headings:
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

Return only the markdown content — no preamble, no explanation, no code fences wrapping the entire output.\
"""


def _build_prompt(title: str, template: str, context: str) -> str:
    tpl_dir = Path(__file__).parent.parent / "templates"
    tpl_path = tpl_dir / f"{template}.md"
    template_body = tpl_path.read_text() if tpl_path.exists() else "## Overview\n\n## Details\n"
    context_section = f"Project context:\n{context}\n\n" if context.strip() else ""
    return DRAFT_PROMPT.format(
        title=title,
        template_body=template_body.replace("{", "{{").replace("}", "}}"),
        context_section=context_section.replace("{", "{{").replace("}", "}}"),
    )


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


def draft_spec_content(title: str, template: str, context: str = "", provider: str = "claude-code", model: str = "", base_url: str = "") -> str:
    """
    Draft spec content via the configured AI provider.

    provider: "claude-code" | "anthropic" | "openai"
    model: provider-specific model name (optional, uses sensible defaults)
    base_url: for openai provider — allows Ollama, Groq, etc.
    """
    prompt = _build_prompt(title, template, context)

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
