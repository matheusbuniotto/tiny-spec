# tiny-spec — State File

## Last updated: 2026-07-15 (session 9)

## Recent changes

### Session 9: `stats`/`dashboard`/`git-context` overlap audit

Fourth (last) bet from the session-8 improvement map: audit these three for redundancy before adding more surface.

**Findings**:
- `spec git-context` is NOT dead weight — it's the documented "check recent commits" step baked into 4+ scaffolded agent prompts (`architect`, `data-engineer`, `explorer`, etc. in `scaffold/agents.py`) and `scaffold/claude_md.py`. `spec sync` already refreshes `.spec/git-context.md` as a side effect, but the standalone command's own value — viewing recent commits without committing anything — is real and used. Left alone. (Corrects a guess from the original audit note — verify before cutting.)
- `spec dashboard` and `spec stats` *did* have real overlap: dashboard's "Summary" sidebar panel (a bare bar-chart of per-status counts) was a strictly worse duplicate of what `spec stats`'s "Pipeline" table already shows (same bars, plus percentages, health verdict, and cycle time that dashboard never had). Cut the sidebar from `dashboard.py` — `_summary()` removed, kanban board now takes the full width, replaced with a one-line pointer to `spec stats` for aggregates. Dashboard's own alert banner (at-gate/stale counts) stays — it's a glance-cue tied to the board you're already looking at, not a pure duplicate.

**Files changed (session 9):**
- `src/spec_cli/commands/dashboard.py` — removed `_summary()`, `_layout()` now full-width kanban + "N specs total — spec stats for health metrics" footer

### Session 8: Spec dependencies (`blocked_by`) + Maps (`parent`) + Living glossary

**Problem**: tiny-spec calls itself "spec-driven + implementation breakdown" but had no way to express that spec B can't start until spec A is done — specs were an unordered set. This is the highest-leverage gap identified while mapping the tool against Matt Pocock's `wayfinder`/`domain-modeling` skills (github.com/mattpocock/skills): his tooling separates decisions with explicit blocking edges; tiny-spec had none.

**`blocked_by` field** — new spec frontmatter, `list[str]` of spec IDs:
- Set at creation: `spec new "Title" --blocked-by 0001,0002`
- Enforced at the one point that matters — starting work: `spec claim` and `spec advance` (→ `in-progress`) both reject the transition with `{"error": "blocked", "blocked_by": [...]}` while any listed spec isn't `implemented`/`closed`. No override flag — clear the block by finishing the blocker or hand-editing `blocked_by` via `spec edit`.
- `spec next` and `spec list --claimable` skip blocked specs when picking/queuing work; `spec next` reports `blocked_by` in its JSON and points at the blocker when the top spec is blocked.
- `spec list --blocked` — new filter, shows what's stuck.
- `spec show` renders a "Blocked by" line; `spec dashboard` shows a ⛔ badge on blocked cards.

**Also fixed**: `src/spec_cli/SKILL.md` had drifted from `skill.md` (missing `claim`, `setup-checks`, and the agent pickup workflow sections) despite session 7 notes claiming they were synced. Resynced by copying `skill.md` over it — keep doing that after any `skill.md` edit until this is scripted.

**`map` template + `parent` field** — wayfinder-lite, second bet from the same gap analysis: tiny-spec had no way to represent "this idea is too big/foggy for one spec." Rather than a new subsystem (tracker, decision-map issue type, etc.), it's just one more template plus one more link field, reusing the existing lifecycle/storage/dashboard machinery entirely:
- `spec new "<title>" --template map` — a spec whose body has Destination / Decisions So Far / Not Yet Specified / Child Specs sections (`templates/map.md`)
- `spec new "<title>" --parent <map_id>` — links a normal spec to a map. `parent` is informational only — it does not gate anything (unlike `blocked_by`), matching Pocock's "the map is an index, not a store."
- `spec show <map_id>` renders a live child roster computed from `parent` links (new `children_of()` helper), so the roster can't drift from reality the way a hand-maintained checklist would.
- `spec list --parent <map_id>` — lists a map's children directly.
- The map spec goes through the same draft→...→implemented lifecycle as everything else; "implemented" for a map means the fog is gone and every child resolved.

**Living glossary** — third bet: `constitution.md` was static, "define your principles" once and never touched again. Domain terms drift between specs because nothing keeps them consistent. Fix mirrors Pocock's `domain-modeling`: update the shared vocabulary as a side effect of the work, not a chore.
- `constitution.md` (both `init` and `greenfield` templates) now scaffolds a `## Glossary` section.
- `spec new --ai` reads the approved glossary (`constitution.approved_glossary()` — parses `## Glossary`, stops before any `Proposed` subsection) and passes it into the draft prompt so drafts reuse existing terms instead of renaming things.
- The AI can append a `<!-- GLOSSARY-PROPOSALS ... -->` sentinel block after the spec body to propose genuinely new shared terms. `ai.extract_glossary_proposals()` strips it from the saved spec body; `constitution.propose_glossary_terms()` appends the terms to a `## Glossary — Proposed (review before promoting)` section, deduped by exact-line match. Nothing is auto-promoted — a human moves lines from Proposed into the real Glossary by hand.
- `spec new --ai --json` reports `glossary_proposed: [...]` so an agent can tell the human when new terms need review.
- `spec review` and `spec export` already read the full constitution file, so this needed no changes there — glossary flows through automatically.

**Files changed (session 8):**
- `src/spec_cli/models.py` — `blocked_by`, `parent` fields, `to_dict`
- `src/spec_cli/storage.py` — persist/parse both fields, `open_blockers()`, `children_of()` helpers
- `src/spec_cli/constitution.py` — NEW: `approved_glossary()`, `propose_glossary_terms()`, `read_constitution()`
- `src/spec_cli/integrations/ai.py` — glossary section in draft prompt, `extract_glossary_proposals()`
- `src/spec_cli/commands/init.py`, `greenfield.py` — `## Glossary` section in scaffolded constitution.md
- `src/spec_cli/commands/lifecycle.py` — dependency gate before `in-progress`
- `src/spec_cli/commands/claim.py` — same gate
- `src/spec_cli/commands/next_action.py` — skip blocked specs, report `blocked_by`
- `src/spec_cli/commands/list_cmd.py` — `--blocked`, `--parent` filters; `--claimable` now excludes blocked
- `src/spec_cli/commands/new.py`, `main.py` — `--blocked-by`, `--parent` options; `map` in `AVAILABLE_TEMPLATES`; glossary read/propose wiring, `glossary_proposed` in output
- `src/spec_cli/commands/show.py` — "Blocked by" / "Part of map" lines, live child roster for maps
- `src/spec_cli/commands/dashboard.py` — ⛔ badge
- `src/spec_cli/templates/map.md` — NEW
- `tests/test_storage.py` — NEW: `open_blockers()`, `children_of()` unit tests
- `tests/test_glossary.py` — NEW: `extract_glossary_proposals()`, `approved_glossary()`, `propose_glossary_terms()`, end-to-end `cmd_new` glossary proposal test
- `README.md`, `skill.md`, `src/spec_cli/SKILL.md` — documented

### Session 7: SKILL.md + Agent Overhaul

**SKILL.md** (the slash command for tech leads) — fully rewritten:
- Bootstrap pattern: 3 commands to run at session start
- Complete command reference for all 21 commands with correct flags
- Workflow sections for every common pattern (spec this / what's blocking / run checks / morning standup)
- Gate rule section — explicit non-negotiable on `at-gate → implemented`
- Removed all invented commands (`spec approve`, `spec gate`, `spec pass`)

**Agents** (8 total, all rewritten):
- `spec-manager`: full lifecycle with all new commands (search, assign, close, stats, review, export)
- `architect`: reads spec + git-context + config, produces structured plan.md with defined schema
- `implementer`: AC-by-AC loop, kata check before gate, specific note format required
- `reviewer`: structured output with AC compliance / tests / conventions / diff hygiene + PASS/FAIL/NEEDS MINOR FIXES verdict
- `tester`: test naming convention (`test_<spec_id>_<slug>`), TDD loop, coverage reporting
- `explorer`: findings as actionable table, each finding mapped to a suggested spec, no fixes
- `data-engineer` (NEW): data-pipeline + experiment spec workflows, DQ kata suggestions, schema ADR requirement, experiment launch checklist
- `run-reviewer`: structured session review with friction table, prioritized changes, requires human approval before editing

**CLAUDE.md** (generated on greenfield) — updated:
- Session start pattern added at top
- Full command reference with all 21 commands grouped by purpose
- Standard workflow diagram showing agent handoff sequence
- Updated agent roster table with `data-engineer`

**Files changed (session 7):**
- `src/spec_cli/SKILL.md` — fully rewritten
- `skill.md` — synced from SKILL.md
- `src/spec_cli/scaffold/agents.py` — all 8 agents rewritten
- `src/spec_cli/scaffold/claude_md.py` — updated

### Session 6: Tech Lead Toolkit — 9 New Commands + 2 Templates

**`spec search <query>`** — full-text search across title and body
- Highlights matches inline with Rich Text
- Shows excerpt with surrounding context, match-type badges (title / body)
- `--status` filter; results sorted title-match first
- Exits clean with "no results" panel when nothing found

**`spec stats`** — pipeline health dashboard
- Visual bar chart per status (proportional fill)
- Key metrics: total, active, stale count, blocked at gate, avg cycle days
- Health indicator: GREEN / YELLOW / RED with reason
- Attention panel lists stale + at-gate IDs with exact commands to unblock

**`spec export [--active]`** — single AI-ingestible context dump
- JSON payload: config, constitution, git-context, recent log tail, all specs with bodies
- Human view: grouped spec list by active/completed, project context table, payload size
- `spec export --json | pbcopy` → paste into any AI session for full context

**`spec assign <id> <assignee>`** — ownership tracking
- Persisted in spec frontmatter; shown in `spec show` and `spec list`
- `spec list --assignee <name>` filters to one person/agent
- Assignee column appears in list only when any spec has one (no wasted space)

**`spec review <id>`** — AI pre-flight before approval
- Runs against project context + constitution
- Checks: title quality, measurable AC, out-of-scope, constitution compliance, gate checklist specificity
- Returns APPROVE / NEEDS WORK / REJECT verdict with specific citations
- Powered by configured ai_provider (claude-code / anthropic / openai)

**`spec log [--last N] [--spec <id>] [--query <term>]`** — audit trail
- Parses `.spec/log.md` with color-coded entries by event type
- Inline query highlighting; most-recent-first ordering
- Filterable by spec ID or search term

**`data-pipeline` template** — source/sink schema, SLAs, data quality checks, backfill strategy, failure/recovery table, monitoring section

**`experiment` template** — hypothesis statement form, primary + guardrail metrics, MDE/power/sample size, decision criteria table, rollback plan, SRM check in gate checklist

**Kata UI refresh** — live spinner per kata, inline stderr preview on failure, summary panel with pass/fail count and exact fix command

**Files changed (session 6):**
- `src/spec_cli/commands/search.py` — NEW
- `src/spec_cli/commands/stats.py` — NEW
- `src/spec_cli/commands/export.py` — NEW
- `src/spec_cli/commands/assign.py` — NEW
- `src/spec_cli/commands/review.py` — NEW
- `src/spec_cli/commands/log_cmd.py` — NEW
- `src/spec_cli/templates/data-pipeline.md` — NEW
- `src/spec_cli/templates/experiment.md` — NEW
- `src/spec_cli/models.py` — `assignee` field
- `src/spec_cli/storage.py` — persist assignee
- `src/spec_cli/commands/show.py` — show assignee
- `src/spec_cli/commands/list_cmd.py` — assignee filter + column
- `src/spec_cli/commands/new.py` — new templates registered
- `src/spec_cli/commands/kata.py` — live spinner UI
- `src/spec_cli/main.py` — 7 new commands registered

### Session 5: Kata Harness, Close, Body Consistency, Agent Fixes

**`spec close` — graceful spec abandonment**
- New terminal state: `closed` (alongside `implemented`)
- Reasons: `descoped | wont-fix | superseded | duplicate`
- Requires `--reason`; prompts for `--note` interactively
- Auto-commits with git; excluded from `spec next`, `--stale`, dashboard stale alerts

**Kata harness — mandatory pre-gate verification**
- New `katas:` key in `.spec/config.yaml` — list of `{name, command, description}` objects
- `spec run-kata [id] [--json]` — runs all katas, exits 1 on any failure
- `spec advance` into `at-gate` automatically runs katas and blocks if any fail
- Override: `spec advance <id> --skip-kata --note "reason"` (requires explicit note)
- Katas appear in `context_summary()` so AI drafts know what checks exist

**`spec list --full` — body in JSON output**
- `Spec.to_dict(include_body=True)` — body now included by default in all JSON output
- `spec list --json` gives lightweight output (no body); `--full` includes bodies
- `spec show --json` no longer duplicates body manually

**`claude_md.py` — stays in sync with real CLI**
- Full command reference with `--json`/`--yes` flags as agents use them
- Added: `spec close`, `spec run-kata`, `spec git-context`, `spec list --full`, `spec next`
- Added: kata and closed lifecycle to workflow section

**`spec-manager` agent — rewritten with real commands**
- Removed invented commands (`spec approve`, `spec gate`, `spec pass`)
- Added kata workflow: run before gate, how to skip with reason
- Added `spec close` workflow with all 4 reasons
- Quality bar section made explicit with bad/good AC examples

**Files changed (session 5):**
- `src/spec_cli/models.py` — `closed` status, `CLOSE_REASONS`, `to_dict(include_body)`
- `src/spec_cli/config.py` — `Kata` dataclass, `katas` field, `context_summary` update
- `src/spec_cli/commands/close.py` — NEW
- `src/spec_cli/commands/kata.py` — NEW
- `src/spec_cli/commands/lifecycle.py` — kata enforcement in `_do_transition`, `--skip-kata`
- `src/spec_cli/commands/list_cmd.py` — `--full`, closed/stale exclusion fix
- `src/spec_cli/commands/dashboard.py` — closed exclusion in stale/badge
- `src/spec_cli/commands/show.py` — removed redundant body assignment
- `src/spec_cli/commands/next_action.py` — exclude closed
- `src/spec_cli/commands/init.py` — katas section in config template
- `src/spec_cli/commands/greenfield.py` — katas section in config template
- `src/spec_cli/scaffold/claude_md.py` — full command reference update
- `src/spec_cli/scaffold/agents.py` — spec-manager rewritten
- `src/spec_cli/main.py` — registered close, run-kata; added --skip-kata, --full

### Session 4: Template Overhaul

**All four templates rewritten** to be opinionated and production-quality:

- **`feature.md`**: User Story (named persona), measurable AC (binary pass/fail), explicit Out of Scope, Definition of Done separate from gate checklist
- **`bug.md`**: Severity/frequency/affected-versions table, deterministic repro steps with minimal repro snippet, pre/post-investigation structure for Root Cause, risk analysis in Fix Plan
- **`api.md`**: Base URL + versioning + breaking change policy header, Data Models section, full endpoint examples with typed JSON fields, pagination shape, error format contract, rate limiting headers
- **`adr.md`**: Decision Drivers (explicit criteria), Alternatives with per-driver rejection reasons, Risks & Mitigations table, Implementation Notes checklist, owner + review date required fields

**AI prompt in `ai.py` rewritten**: section-by-section filling instructions for each template type, enforces measurability in AC, requires specific curl/command examples in gate checklist, bans vague phrases like "should be fast"

**Files changed (session 4):**
- `src/spec_cli/templates/feature.md`
- `src/spec_cli/templates/bug.md`
- `src/spec_cli/templates/api.md`
- `src/spec_cli/templates/adr.md`
- `src/spec_cli/integrations/ai.py` — DRAFT_PROMPT rewritten

### Session 3: Git Context Awareness

**Git init on `spec init`**
- If the current folder is NOT a git repo, prompts user to `git init` (auto-yes in `--json` mode)
- If it IS a git repo, captures last 10 commits + branch + remotes into `.spec/git-context.md`

**Git init on `spec greenfield`**
- Always runs `git init` on the new folder immediately
- Writes `.spec/git-context.md` placeholder (no commits yet)

**New command: `spec git-context`**
- Displays last 10 commits in a table (SHA, date, author, message)
- Refreshes `.spec/git-context.md` with current git state
- `spec sync` also auto-refreshes the context file before committing

**Files changed (session 3):**
- `src/spec_cli/integrations/git.py` — added `git_init`, `git_recent_commits`, `git_context_markdown`
- `src/spec_cli/commands/init.py` — git init prompt + git-context.md generation
- `src/spec_cli/commands/greenfield.py` — always git init + git-context.md placeholder
- `src/spec_cli/commands/git_sync.py` — auto-refresh context on sync + new `cmd_git_context`
- `src/spec_cli/main.py` — registered `git-context` command

### Session 2: UX & Spec-Driven Development Improvements

**`spec show` — lifecycle progress bar + next action hint**
- Visual progress bar: `● draft  →  ● approved  →  ● in-progress  →  ○ at-gate  →  ○ implemented`
- Age indicator on each spec (e.g. "3 days ago")
- Next action hint tells you exactly what command to run

**`spec next` — most important action right now (NEW command)**
- Prioritizes: at-gate > in-progress > approved > draft
- Breaks ties by age (oldest first)
- Shows the exact command to run
- JSON-friendly for AI agents

**`spec edit` — open in $EDITOR (NEW command)**
- Opens the spec file in your configured editor
- Falls back to showing file path if $EDITOR not set

**Dashboard — aging alerts + stale detection**
- Each spec shows age badge (e.g. "3d")
- Stale specs (>3 days) highlighted in red
- Alert panel at top: "2 specs waiting at gate" / "1 stale spec"
- Per-column count in header

**`spec list --stale` — surface stuck specs**
- New `--stale` flag filters to specs >3 days without movement
- Age column added to table with red highlighting for stale items

**Spec drift guard**
- When advancing a spec that was hand-edited since last CLI transition, shows warning
- Prevents silent drift between what was approved and what's being gated

**Init templates — `git_auto_commit` discoverable**
- Both `init` and greenfield config templates now include `git_auto_commit: true`

**Files changed (session 2):**
- `src/spec_cli/commands/show.py` — progress bar + next action + age
- `src/spec_cli/commands/dashboard.py` — aging, alerts, stale detection
- `src/spec_cli/commands/list_cmd.py` — --stale flag, age column
- `src/spec_cli/commands/lifecycle.py` — drift guard warning
- `src/spec_cli/commands/edit.py` — NEW: edit command
- `src/spec_cli/commands/next_action.py` — NEW: next command
- `src/spec_cli/commands/init.py` — git_auto_commit in template
- `src/spec_cli/commands/greenfield.py` — git_auto_commit in template
- `src/spec_cli/main.py` — registered edit, next commands; --stale flag
- `src/spec_cli/SKILL.md` — documented new commands
- `skill.md` — documented new commands
- `README.md` — updated commands table

### Session 1: Human Gate Checklist + Git Integration

**Human Gate Checklist** — Clear verification for human reviewers
- All 4 templates (feature, bug, api, adr) include `## Human Gate Checklist`
- AI prompt enhanced to generate feature-specific checklist items
- Checklist auto-displayed at `at-gate` transition
- New command: `spec gate-check <id>`

**Git Integration** — Spec lifecycle stays in sync with git
- Auto-commit on every lifecycle transition
- Commit format: `spec(<id>): <old_status> → <new_status> — <title>`
- New config: `git_auto_commit: true` (default)
- New command: `spec sync`

## Architecture notes
- Git integration gracefully degrades if not in a git repo
- Gate checklist extracted from spec body via regex
- `state.transition()` returns `tuple[Spec, Optional[str]]` (spec, git_sha)
- Drift detection uses file mtime vs `updated_at` frontmatter comparison
- `spec next` prioritizes by status severity then age
- Dashboard STALE_DAYS threshold is 3 (hardcoded for now)

## Session 10: AI-first engineering mapping → tasks/ + backlog.md

Researched AI-first eng practices (AXI principles from axi.md via Wayback, no-mistakes repo,
AGENTS.md standard, worktree workflows). Found bug: `spec new --json` crashes on non-TTY stdin
(questionary prompts fire without --yes). Produced:
- `tasks/001`–`008` — PR-sized task files, product-first order: json-non-interactive fix,
  agent output ergonomics (help[]/counts/truncation), kata→checks rename (`spec verify`),
  `spec doctor`, `claim --worktree`, AGENTS.md scaffold, repo CI+ruff, CLI smoke + skill-drift tests.
- `backlog.md` — deferred: token saving (minimal schemas, TOON, body-less), action-classified
  gate items, doctor --fix, intent-verbatim wording, `init --ci`, mypy; rejected list (daemon/TUI/etc).
Files changed: tasks/*.md (new), backlog.md (new).
