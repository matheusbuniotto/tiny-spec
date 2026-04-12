# tiny-spec — State File

## Last updated: 2026-04-10 (session 3)

## Recent changes

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
