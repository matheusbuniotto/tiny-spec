# tiny-spec

**Spec-driven development for humans and AI agents.**

Stop scattering feature intent across Slack threads, Notion docs, and half-remembered conversations. `tiny-spec` gives every feature, bug fix, and architecture decision a structured lifecycle — from draft to implemented — with a CLI that both you and your AI coding agent can drive.

```
uvx tiny-spec
```

---

## Why specs?

AI coding agents are fast. Dangerously fast. They'll implement what you *said*, not what you *meant* — and they'll do it confidently, completely, and wrong.

Specs fix this. A spec is a short markdown file that captures:

- **What** you're building and why
- **Acceptance criteria** (the gate an AI must pass before the feature is "done")
- **Context** your agent needs — stack, conventions, what's off-limits

When your agent has a spec, it stops guessing. When you have a spec, you stop re-explaining.

---

## How it works

tiny-spec stores specs as markdown files in `.spec/specs/`. Each spec has a lifecycle:

```
draft → approved → in-progress → at-gate → implemented
```

- **draft** — written, not yet reviewed
- **approved** — you've signed off, agent can start
- **in-progress** — agent is working
- **at-gate** — agent says it's done; waiting for human verification
- **implemented** — done and verified

The gate step is intentional. Agents must stop and ask a human to verify before a spec closes.

Every spec includes a **Human Gate Checklist** — a concrete list of verification steps the human must complete before passing the gate. No vague "review the code" — each item is a specific command to run, a scenario to test, or a diff to read.

---

## Quickstart

```bash
# Install
git clone https://github.com/matheusbuniotto/tiny-spec && cd tiny-spec && uv tool install .

# Set up a new project (interactive wizard)
spec init my-project --type python-api

# Or add tiny-spec to an existing project
cd my-project
spec init

# Create a spec (AI-drafted)
spec new "User authentication with JWT" --template feature --ai

# See what's in flight
spec dashboard

# Advance through the lifecycle
spec advance 0001          # draft → approved
spec advance 0001          # approved → in-progress
spec advance 0001 --note "Needs PM sign-off on rate limiting"   # → at-gate
spec advance 0001 --note "All criteria verified, tests green"   # → implemented
```

---

## Commands

| Command | What it does |
|---|---|
| `spec init [folder]` | Initialize `.spec/` in current dir, or scaffold a new project |
| `spec new "title"` | Create a spec (interactive or `--ai` for AI draft) |
| `spec list` | List all specs, filterable by `--status` |
| `spec show 0001` | Show a spec in full |
| `spec advance 0001` | Move to next state (auto-detects transition) |
| `spec revert 0001` | Send back to draft |
| `spec edit 0001` | Open spec in `$EDITOR` |
| `spec next` | Show the most important thing to do right now |
| `spec gate-check 0001` | Show the Human Gate Checklist for a spec |
| `spec sync` | Commit all `.spec/` changes to git |
| `spec list --stale` | Show specs stuck for 3+ days |
| `spec dashboard` | Pipeline dashboard with aging alerts |
| `spec config` | Show project config (stack, conventions, etc.) |

All commands support `--json` for machine-readable output and `--yes` to skip interactive prompts.

---

## Human Gate Checklist

Every spec template includes a `## Human Gate Checklist` section. When the AI implements a spec and it reaches `at-gate`, tiny-spec shows the checklist automatically:

```
╭─ ⏸ Human Gate Checklist ─────────────────────────────────╮
│ Before you pass this gate, verify each item:              │
│                                                           │
│ - [ ] Run the tests: `pytest -v` — all pass?              │
│ - [ ] Try the happy path: POST /api/users with valid JSON │
│ - [ ] Check the edge case: duplicate email returns 409    │
│ - [ ] Read the diff: `git diff main` — no debug code?     │
│ - [ ] Acceptance criteria met: re-read each criterion      │
╰───────────────────────────────────────────────────────────╯
```

When you create specs with `--ai`, the AI fills in **real commands and scenarios** specific to your feature — not generic placeholders.

You can view the checklist anytime with `spec gate-check <id>`.

---

## Git integration

tiny-spec auto-commits `.spec/` changes to git on every lifecycle transition. Each commit follows a consistent format:

```
spec(0001): draft → approved — User authentication with JWT
spec(0001): approved → in-progress — User authentication with JWT
spec(0001): in-progress → at-gate — User authentication with JWT
```

This means your spec lifecycle is always in git history — reviewable, revertable, blameable.

```yaml
# .spec/config.yaml
git_auto_commit: true   # default — set to false to disable
```

For manual control:

```bash
spec sync                                    # commit pending .spec/ changes
spec sync --message "updated acceptance criteria"  # custom message
```

---

## AI-native design

tiny-spec ships with a `SKILL.md` — a Claude Code skill that lets your agent drive the full spec lifecycle without any setup.

Copy it to your project's `.claude/skills/spec/` directory so Claude Code picks it up as the `/spec` slash command:

```bash
mkdir -p .claude/skills/spec
cp SKILL.md .claude/skills/spec/SKILL.md
```

Then your agent can:

```bash
# In Claude Code, your agent can:
spec new "Stripe webhook handler" --template feature --ai --yes --json
spec list --status at-gate --json
spec advance 0001 --note "Webhook signature verified, retries tested" --yes --json
```

The `--json` flag makes every command scriptable. The `--yes` flag makes it non-interactive. Agents never block on prompts.

### Project context for better AI drafts

`spec init` creates a `.spec/config.yaml` where you describe your stack:

```yaml
project_name: "my-api"
languages: ["python"]
frameworks: ["fastapi"]
testing: "pytest, >80% coverage"
conventions: ["no globals", "async everywhere"]
out_of_bounds: ["don't touch the billing module"]
```

When you run `spec new --ai`, this context is injected into the AI prompt. Your agent gets specs that already know your conventions.

---

## Templates

Four built-in templates, all markdown:

- **feature** — user story, acceptance criteria, implementation notes
- **bug** — repro steps, root cause, fix plan
- **adr** — architecture decision record (status, context, decision, consequences)
- **api** — endpoint design, request/response shapes, auth, errors

---

## Greenfield projects

`spec init` with a folder name scaffolds a full project structure:

```bash
spec init my-app --type python-api
```

Creates:
```
my-app/
  .spec/           # specs, config, constitution, log
  .claude/
    agents/        # pre-wired AI agent definitions
  CLAUDE.md        # project context for Claude Code
```

Project types: `blank`, `python-api`, `typescript-web`, `cli-tool`

---

## The constitution

`.spec/constitution.md` is a free-form markdown file where you define your project's non-negotiables — principles, standards, and things that are permanently off-limits. Agents read it. So do new engineers.

---

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone and install
git clone https://github.com/matheusbuniotto/tiny-spec && cd tiny-spec
uv tool install .
```

### Agentic install (for AI agents and CI)

If you're provisioning an environment from a script or letting an AI agent set up tiny-spec, use this self-contained sequence. It installs `uv` if missing, then installs from the repo — no prompts, no manual steps:

```bash
# 1. Install uv (idempotent — safe to run even if uv is already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Reload PATH so the next command finds uv without a shell restart
export PATH="$HOME/.local/bin:$PATH"

# 3. Clone and install tiny-spec
git clone https://github.com/matheusbuniotto/tiny-spec && uv tool install ./tiny-spec

# 4. Verify
spec --version
```

**For Claude Code agents** — paste this into your `CLAUDE.md` or agent preamble so the agent can self-install before its first `spec` call:

```
If `spec` is not found, run:
  curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH" && git clone https://github.com/matheusbuniotto/tiny-spec && uv tool install ./tiny-spec
```

For AI drafting, set your API key:

```bash
export ANTHROPIC_API_KEY=sk-...   # Claude (default)
export OPENAI_API_KEY=sk-...      # OpenAI
```

---

## License

MIT
