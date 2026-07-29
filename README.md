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

### Verification summary

`spec verify --summary <id>` shows a structured human verification summary for any spec:

```bash
spec verify 0001 --summary
```

Displays: spec info + acceptance criteria + gate checklist (split into agent-verifiable and human-only items) + git diff stat + commands to advance or revert. Supports `--json` for scripting.

Useful at the end of an agent loop — see `scripts/spec-loop.sh` for a reference implementation that collects these summaries across multiple specs and shows them at the end.

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
  AGENTS.md        # tool-agnostic agent instructions (Codex, Cursor, Copilot, ...)
```

Project types: `blank`, `python-api`, `typescript-web`, `cli-tool`

Both `spec init` and greenfield `spec init <folder>` write `AGENTS.md` (skipped if one already exists — never overwrites a hand-authored one). Pass `--hooks` to also install a Claude Code `SessionStart` hook that runs `spec next --json` at the start of every session.

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

# Or install straight from the repo (latest main, no PyPI wait)
uv tool install git+https://github.com/matheusbuniotto/tiny-spec
```

For AI drafting, set your API key:

```bash
export ANTHROPIC_API_KEY=sk-...   # Claude (default)
export OPENAI_API_KEY=sk-...      # OpenAI
```

---

## Automating specs with AI agents

`scripts/spec-loop.sh` is a reference implementation for running specs with AI agents in a loop. It handles the full lifecycle:

```bash
bash scripts/spec-loop.sh --pick next --agent codex              # run next spec, human verify (default)
bash scripts/spec-loop.sh --pick 0003 --agent codex --test manual # specific spec, manual impl
bash scripts/spec-loop.sh --pick next --max 3                     # 3 specs, then stop
bash scripts/spec-loop.sh --pick next --timeout 300               # cap each agent invocation at 5 minutes
bash scripts/spec-loop.sh --pick next --agent codex --verifier codex  # codex verifies with fresh context
bash scripts/spec-loop.sh --pick next --agent codex --worktree    # isolated git worktree per spec
bash scripts/spec-loop.sh --pick next --dry-run                   # preview without changing anything
```

### Features

- **Multi-agent**: supports `kimi`, `pi`, `codex`, `claude` with auto-detection
- **Verifier split**: `--verifier human` (default) defers a structured summary for you; `--verifier codex` etc invokes a **different agent** with fresh context (ACs + diff + gate checklist only, no implementation plan)
- **Worktree isolation**: `--worktree` creates an isolated git worktree per spec; merges to `master` only when the merge is clean, preserves the worktree for manual resolution on conflicts, and discards failed work
- **Optional agent timeout**: `--timeout <seconds>` caps each agent invocation; it defaults to `0` (unlimited)
- **Evidence collection**: extracts ACs from the spec file, gate checklist via `spec gate-check --json`, and git diff stat — shows you exactly what to validate
- **Compact output**: spinner with elapsed timer, heartbeat every 30s, one-line-per-phase results
- **Human verification summary**: at end of loop, prints a structured block per spec with ACs, gate checklist, diff stat, and commands to validate
- **Retry with backoff**: agent retries up to 2× on failure, reverts spec to draft on exhaustion

### Verifier architecture

The loop implements a **verification separation of concerns**:

1. **Human verifier** (`--verifier human`, default): the agent implements, code is committed with "awaiting human verify", loop continues to next spec. At end, you get a structured summary for each spec showing ACs, gate checklist, diff stat, and how to run. You validate and `spec advance <id>` or `spec revert <id>`.

2. **Agent verifier** (`--verifier codex` etc): a different agent (fresh context, no implementation bias) gets only the spec's acceptance criteria + git diff evidence + gate checklist. It runs actual commands to check ACs, reports PASS/FAIL/NEEDS HUMAN. This is intentionally not the same agent that implemented — it has zero context about what the implementer was thinking.

3. **Human escalation**: when either path returns "needs human" (visual inspection, product judgment), the spec is left at `at-gate` with a note so you can verify and advance manually.

The agent-verifier prompt contains *only* the ACs, the diff stat, and the gate checklist — the full spec body (with technical notes and implementation plan) is deliberately excluded to prevent confirmation bias.

### Customizing for your project

Edit the `AGENT_SYSTEM_PROMPT` variable at the top of `scripts/spec-loop.sh` with your project's context:

```bash
AGENT_SYSTEM_PROMPT="You are an autonomous implementation agent for My App...

## Project
Stack: Python + FastAPI
Conventions: async everywhere, no globals
Out of bounds: don't touch billing"
```

Configurable placeholders used internally: `{{SPEC_ID}}`, `{{SPEC_TITLE}}`, `{{SPEC_BODY}}`, `{{PROJECT_DIR}}`.

### Agent compatibility

| Agent | Flag | Status |
|---|---|---|
| Claude Code | `--agent claude` | ✅ Tested (needs `claude` CLI) |
| Codex CLI | `--agent codex` | ✅ Tested |
| Kimi | `--agent kimi` | ✅ Tested |
| Pi (Terminal) | `--agent pi` | ✅ Tested |

---

## License

MIT
