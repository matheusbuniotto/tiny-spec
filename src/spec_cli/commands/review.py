"""AI pre-flight review of a spec before human approval."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from rich import box

from ..config import load_config
from ..models import STATUS_STYLE
from ..storage import find_spec, find_root, spec_dir
from ..ui import console, error

_REVIEW_PROMPT = """\
You are a senior tech lead reviewing a spec before approving it.

## Project context
{context}

## Constitution
{constitution}

## Spec to review
Title: {title}
Template: {template}
Status: {status}

{body}

---

Review this spec against the following quality bar. Be direct and specific.
For each issue, cite the exact section and what's wrong.

## Quality checks

1. **Title** — Is it a clear, action-oriented verb phrase? (Bad: "Auth stuff", Good: "Add JWT authentication")
2. **Acceptance criteria** — Are ALL criteria independently testable and binary (pass/fail)?
   Flag any criterion that is vague, unmeasurable, or contains words like "should", "fast", "good", "nice".
3. **Out of scope** — Is at least one thing explicitly excluded?
4. **Constitution compliance** — Does anything in this spec violate the project constitution or out_of_bounds list?
5. **Human Gate Checklist** — Are all items specific? Flag any placeholder like "<command>" or generic phrases like "run the tests".
6. **Missing information** — What critical information is absent that an implementer would need?
7. **Risk** — What's the biggest implementation risk not addressed in the spec?

## Output format
Return a markdown review with these exact sections:

### ✅ Strengths
[What's good — be brief]

### ❌ Blockers
[Issues that MUST be fixed before approval. If none, write "None."]

### ⚠ Suggestions
[Non-blocking improvements]

### Verdict
**[APPROVE / NEEDS WORK / REJECT]** — one sentence explaining the decision.

Be ruthless about vague acceptance criteria. If you can't write a test for a criterion, flag it.
Return only the markdown — no preamble.\
"""


def _call_ai(prompt: str, provider: str, model: str, base_url: str) -> str:
    if provider == "claude-code":
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()

    if provider == "anthropic":
        import anthropic
        import os
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model=model or "claude-opus-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    if provider == "openai":
        import openai
        import os
        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "sk-placeholder"),
            base_url=base_url or None,
        )
        resp = client.chat.completions.create(
            model=model or "gpt-4o",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content

    raise RuntimeError(f"Unknown ai_provider: {provider}")


def cmd_review(spec_id: str, json_out: bool, root: Path) -> None:
    root = find_root(root)
    spec = find_spec(root, spec_id)
    if not spec:
        error(f"Spec not found: {spec_id}", json_out, {"error": "not_found", "id": spec_id})

    cfg = load_config(root)
    sd = spec_dir(root)
    constitution = (sd / "constitution.md").read_text() if (sd / "constitution.md").exists() else "(none)"

    prompt = _REVIEW_PROMPT.format(
        context=cfg.context_summary() or "(no project context configured)",
        constitution=constitution,
        title=spec.title,
        template=spec.template,
        status=spec.status.value,
        body=spec.body,
    )

    if not json_out:
        icon, color = STATUS_STYLE[spec.status]
        console.print()
        console.print(Panel(
            f"[bold]{spec.id}[/bold] — {spec.title}\n"
            f"[{color}]{icon} {spec.status.value}[/{color}]  [dim]template: {spec.template}[/dim]\n\n"
            f"[dim]Reviewing via[/dim] [cyan]{cfg.ai_provider}[/cyan][dim]...[/dim]",
            title="[bold cyan]◈ AI Spec Review[/bold cyan]",
            box=box.ROUNDED, border_style="cyan", padding=(0, 2),
        ))
        console.print()

    try:
        with console.status("[cyan]Analysing spec...[/cyan]", spinner="dots"):
            review_text = _call_ai(prompt, cfg.ai_provider, cfg.ai_model, cfg.ai_base_url)
    except FileNotFoundError:
        error(
            "Claude Code CLI not found. Set ai_provider to 'anthropic' or 'openai' in .spec/config.yaml.",
            json_out, {"error": "claude_not_found"},
        )
    except Exception as e:
        error(str(e), json_out, {"error": "ai_failed", "detail": str(e)})

    verdict = "UNKNOWN"
    for line in review_text.splitlines():
        if "**APPROVE" in line:
            verdict = "APPROVE"
        elif "**NEEDS WORK" in line:
            verdict = "NEEDS WORK"
        elif "**REJECT" in line:
            verdict = "REJECT"

    if json_out:
        typer.echo(json.dumps({
            "id": spec.id,
            "title": spec.title,
            "verdict": verdict,
            "review": review_text,
        }))
        return

    verdict_colors = {"APPROVE": "bright_green", "NEEDS WORK": "yellow", "REJECT": "red", "UNKNOWN": "dim"}
    verdict_icons = {"APPROVE": "✓", "NEEDS WORK": "⚠", "REJECT": "✕", "UNKNOWN": "?"}
    vc = verdict_colors[verdict]
    vi = verdict_icons[verdict]

    console.print(Rule(f"[{vc}]{vi} {verdict}[/{vc}]", style=vc))
    console.print()
    console.print(Markdown(review_text))
    console.print()
    console.print(Rule(style="dim"))

    if verdict == "APPROVE":
        console.print(f"\n  [bright_green]✓[/bright_green] Ready to approve: [cyan]spec advance {spec.id}[/cyan]\n")
    elif verdict in ("NEEDS WORK", "REJECT"):
        console.print(f"\n  [yellow]⚠[/yellow] Fix issues then re-review: [cyan]spec review {spec.id}[/cyan]"
                      f"  or edit: [cyan]spec edit {spec.id}[/cyan]\n")
