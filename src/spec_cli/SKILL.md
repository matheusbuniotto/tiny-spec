---
name: spec
description: >
  Drive the full tiny-spec lifecycle from Claude Code. Use when the user says
  "spec this", "add to specs", "what's in flight", "review that spec",
  "what's blocking", "assign this", "search specs", "run checks",
  "what's the pipeline health", or anything about spec status, lifecycle,
  search, stats, or assignment.
---

You have access to the `spec` CLI. Always use `--json` and `--yes` for agent use.
Never invent commands — only use what's listed here.

---

## Human setup vs agent work

Humans usually run project setup: `spec init`, `spec doctor`, `spec setup-checks`.
Agents should not run `spec init` unless the human explicitly asks.

## Bootstrap (start of every session)

```bash
spec doctor --json                  # readiness: checks, constitution, project context
spec boot --json                    # small agent packet: rules, next action, claimable queue
spec boot --agent implementer --json # role-specific queue when acting as an implementer
```

After claiming work, load focused context only:

```bash
spec context <id> --json
```

---

## Full command reference

### Lifecycle

```bash
# Create
spec new "Title" --template feature --ai --yes --json
spec new "Title" --template bug --yes --json
spec new "Title" --template adr --yes --json
spec new "Title" --template api --yes --json
spec new "Title" --template data-pipeline --yes --json
spec new "Title" --template experiment --yes --json

# Read
spec list --json
spec list --status draft --json
spec list --status in-progress --json
spec list --status at-gate --json
spec list --full --json                              # includes spec bodies
spec list --assignee "alice" --json                 # filter by owner
spec list --agent implementer --json                # filter by suggested agent role
spec list --stale --json                            # stuck 3+ days
spec show <id> --json
spec context <id> --json                            # focused task packet
spec gate <id> --json                               # human review packet

# Role-intent lifecycle
spec approve <id> --yes --json                      # human: draft → approved
spec route <id> implementer --json                  # set suggested agent role
spec claim <id> --yes --json                        # agent: approved → assigned → in-progress
spec deliver <id> --note "AC1: evidence; AC2: evidence; Checks: ..." --yes --json  # agent → at-gate
spec pass <id> --note "what was verified" --yes --json    # human only: at-gate → implemented
spec reject <id> --note "what failed" --category missed-ac --correction "reusable lesson" --yes --json

# Advanced escape hatch
spec advance <id> --yes --json
spec advance <id> --note "what to verify" --yes --json
spec advance <id> --skip-checks --note "reason" --yes --json

# Revert / close
spec revert <id> --note "why" --yes --json
spec close <id> --reason descoped --note "why" --yes --json
spec close <id> --reason wont-fix --note "why" --yes --json
spec close <id> --reason superseded --note "replaced by <id>" --yes --json
spec close <id> --reason duplicate --note "same as <id>" --yes --json

# Assign / claim
spec assign <id> "alice" --json                     # owner/person/runtime
spec assign <id> "" --json                          # unassign
spec claim <id> --as "my-agent" --yes --json        # specify runtime name (default: $SPEC_AGENT or "agent")
```

### Discovery & search

```bash
spec search "payment retry" --json
spec search "schema migration" --status in-progress --json
spec stats --json                                   # pipeline health object
spec doctor --json                                  # harness readiness check
spec boot --json                                    # agent startup packet
spec next --json                                    # top priority action (includes assignee + claimable_queue)
spec next --agent implementer --json                # top priority for a role
spec list --claimable --json                        # only unclaimed approved specs — ready to pick up
spec log --last 20 --json
spec log --spec <id> --json                         # history for one spec
spec log --query "gate" --json
```

### Quality & gates

```bash
spec setup-checks --yes --json  # scan project, auto-configure pre-gate checks
spec gate <id> --json           # full human review packet
spec gate-check <id> --json     # checklist only
spec run-checks --json          # run all checks, exit 1 on failure
spec run-checks <id> --json     # same, scoped to a spec for context
spec correction <id> --category missed-ac --note "lesson" --json
spec corrections --suggest --json
```

### Context & git

```bash
spec config --json
spec export --json              # full payload: config + constitution + all specs
spec export --active --json     # active specs only
spec git-context --json         # last 10 commits + branch + remotes
spec sync --json                # commit pending .spec/ changes
```

### Project setup

```bash
spec init                       # init .spec/ in current directory
spec init "my-project" --type python-api   # greenfield project
spec dashboard                  # kanban view (human-readable)
spec edit <id>                  # open spec in $EDITOR
```

---

## Status lifecycle

```
draft → approved → in-progress → at-gate → implemented
  ↘                                                 ↗
   closed (descoped | wont-fix | superseded | duplicate)
```

- `at-gate → implemented` always requires a human. Never pass this yourself without explicit confirmation.
- Checks (if configured) block `in-progress → at-gate` automatically.

---

## Workflow: "spec this idea"

```bash
spec config --json                                          # 1. get context
spec new "<title>" --template feature --ai --yes --json    # 2. AI draft
spec show <id> --json                                       # 3. read it back
spec validate <id> --json                                   # 4. deterministic quality check
# if validation passes, show user and ask
spec advance <id> --yes --json                             # 5. draft → approved (after user OK)
```

## Workflow: agent picks up and delivers work

```bash
spec next --json                                             # 1. find top action (check assignee + claimable_queue)
spec list --claimable --json                                 # (optional) browse all unclaimed approved specs
spec claim <id> --yes --json                                 # 2. atomic claim: assert approved, assign, start
# ... implement the work ...
spec run-checks --json                                         # 3. checks must pass before gating
spec advance <id> --note "<delivery summary>" --yes --json  # 4. DELIVERY SIGNAL: in-progress → at-gate
# The --note is the delivery receipt the human will read. Be specific:
# "Implemented X. Tests: 12 pass. Edge case Y handled in file.py:42."
# DO NOT advance past at-gate — that gate belongs to the human.
```

## Workflow: "what's in flight / what should I do next?"

```bash
spec next --json               # top action
spec stats --json              # pipeline health
spec list --status in-progress --json
spec list --status at-gate --json
```

## Workflow: "what's blocking?"

```bash
spec list --status at-gate --json      # specs waiting for human
# for each: show gate_notes + AC
spec gate-check <id> --json            # what specifically needs checking
```

## Workflow: "find specs about X"

```bash
spec search "<topic>" --json
spec search "<topic>" --status in-progress --json
```

## Workflow: "close / kill this spec"

```bash
spec close <id> --reason descoped --note "<why>" --yes --json
```

## Workflow: "assign this to someone"

```bash
spec assign <id> "<name or agent>" --json
spec list --assignee "<name>" --json   # what are they working on?
```

## Workflow: "set up pre-gate checks for this project"

```bash
spec setup-checks --yes --json         # scans for pytest/ruff/mypy/eslint/tsc/cargo/go etc.
# writes detected checks to .spec/config.yaml
# these auto-run before any spec can enter at-gate
```

## Workflow: "run the checks before gating"

```bash
spec run-checks <id> --json              # run checks, exit 1 on failure
# on failure: fix, then re-run
# to skip with justification:
spec advance <id> --skip-checks --note "<reason>" --yes --json
```

## Workflow: "give me full context for this project" (new AI session)

```bash
spec export --active --json   # paste this into AI context
```

## Workflow: start of day / tech lead morning check

```bash
spec stats --json
spec list --stale --json
spec list --status at-gate --json
spec next --json
```

---

## Gate rule (non-negotiable)

`spec advance <id> --note "..."` moving a spec from `in-progress` to `at-gate` is the **agent delivery signal**. The `--note` is the delivery receipt the human will read — be specific about what was done, what tests passed, and any edge cases handled.

`at-gate → implemented` requires a human.

Before calling `spec advance <id> --note "..." --yes --json` on an at-gate spec:
1. `spec gate-check <id> --json` — show the checklist
2. List each acceptance criterion
3. Ask the human: "Have you verified each item? What did you check?"
4. Only proceed after explicit confirmation with specifics.

Vague confirmation ("looks good") is not enough.
Acceptable: "Ran pytest — 47 passed. Hit POST /users with valid/invalid JWT — correct responses. Diff reviewed, no debug code."

---

## Exit codes
- `0` — success
- `1` — error (JSON response has `error` field with details)
