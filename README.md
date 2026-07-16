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
uv tool install tiny-spec

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
| `spec claim 0001 --worktree` | Claim a spec and create an isolated git worktree |
| `spec advance 0001` | Move to next state (auto-detects transition) |
| `spec revert 0001` | Send back to draft |
| `spec edit 0001` | Open spec in `$EDITOR` |
| `spec next` | Show the most important thing to do right now |
| `spec gate-check 0001` | Show the Human Gate Checklist for a spec |
| `spec sync` | Commit all `.spec/` changes to git |
| `spec list --stale` | Show specs stuck for 3+ days |
| `spec list --blocked` | Show specs waiting on an open blocker |
| `spec list --parent 0001` | Show a map's child specs |
| `spec new "title" --template map` | Create a map for an idea too big/foggy for one spec |
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

## Dependencies between specs

Specs can declare what they're blocked on:

```bash
spec new "Add refund flow" --blocked-by 0003,0007
```

While any spec in `blocked_by` isn't `implemented` or `closed`, tiny-spec won't let this one be claimed or started — `spec claim`/`spec advance` refuse the transition with the blocking IDs. `spec next` and `spec list --claimable` skip blocked specs automatically; `spec list --blocked` shows what's stuck and on what.

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

All markdown:

- **feature** — user story, acceptance criteria, implementation notes
- **bug** — repro steps, root cause, fix plan
- **adr** — architecture decision record (status, context, decision, consequences)
- **api** — endpoint design, request/response shapes, auth, errors
- **data-pipeline** — source/sink schema, SLAs, data quality checks
- **experiment** — hypothesis, metrics, decision criteria, rollback plan
- **map** — index for an idea too big or too foggy for one spec; see below

---

## Maps: for ideas too big for one spec

A regular spec is a decided, scoped unit of work. Some ideas aren't there yet — the destination is clear-ish but the shape of the work isn't. For those, `map` is a template, not a new subsystem:

```bash
spec new "Rebuild onboarding" --template map --yes --json   # 0001
spec new "Signup form redesign" --parent 0001 --yes --json  # 0002, linked
spec new "Email verification" --parent 0001 --yes --json    # 0003, linked
```

`spec show 0001` renders the live child roster (fetched from `parent` links, not hand-maintained) alongside the map's own body — destination, decisions made so far, and what's still fog. Children go through the normal spec lifecycle independently; the map goes through it too, and reaches `implemented` once nothing is left undecided and every child is `implemented`/`closed`. `spec list --parent 0001` lists a map's children directly.

`parent` is informational — it doesn't gate anything, unlike `blocked_by`. Use `blocked_by` when a child spec's *work* can't start until another spec is done; use `parent` to say a spec belongs to a larger initiative.

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

### Living glossary

The constitution's `## Glossary` section is shared vocabulary, kept current as a side effect of drafting specs rather than a doc nobody revisits:

- `spec new --ai` reads the approved glossary and reuses those terms instead of inventing new names for the same thing.
- If a draft introduces a genuinely new domain term, the AI proposes it under a `## Glossary — Proposed (review before promoting)` section — never directly into the approved list.
- You review and move entries from Proposed into `## Glossary` by hand (or reject them by deleting the line). Nothing is auto-promoted.

`spec review` and `spec export` already read the whole constitution file, so glossary terms flow into pre-flight review and cross-session AI context for free.

---

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Run without installing (try it instantly)
uvx tiny-spec

# Or install as a persistent tool
uv tool install tiny-spec
```

For AI drafting, set your API key:

```bash
export ANTHROPIC_API_KEY=sk-...   # Claude (default)
export OPENAI_API_KEY=sk-...      # OpenAI
```

---

## License

MIT
