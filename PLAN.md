# tiny-spec: Agentic Harness + Grug Simplification

## Context

tiny-spec is a spec-driven development CLI (22 commands, 6 templates, full lifecycle management). The request is twofold:
1. **Grug/Pareto trim** — less complexity, higher ROI per command
2. **Agentic harness** — make this a reliable control harness for AI agent development

The core gap: agents can discover work (`spec next`) and deliver it (`spec advance`), but there's no atomic "claim" operation, the `next` output doesn't include `assignee` (so agents can't know if work is already taken), and the skill.md doesn't name `advance-to-at-gate` as the explicit agent delivery signal.

## What NOT to Build

These sound good but are complexity traps:
- `spec run-agent <id>` — subprocess lifecycle management, out of scope for a file-based CLI
- `spec context <id>` — thin wrapper over `show --json` + `export --active --json`; docs fix, not new command
- `spec handoff` — synonym for `spec advance` when in-progress; naming fix in skill.md
- New frontmatter fields (claimed_at, session_id) — `assignee` + log already capture this
- Additional templates — 6 is already enough for 80% of use cases

## Plan

### 1. New command: `spec claim <id>` (atomic pick-up)

**File to create:** `src/spec_cli/commands/claim.py`

Atomic operation: assert status is `approved` → assign → transition to `in-progress`.  
Value: two separate commands (`assign` + `advance`) don't validate the spec is claimable.

```python
# cmd_claim(spec_id, agent_name, yes, json_out, root)
# 1. find_root + find_spec
# 2. default agent_name = os.environ.get("SPEC_AGENT", "agent") if empty
# 3. If status == IN_PROGRESS and assignee == agent_name: succeed idempotently
# 4. If status == IN_PROGRESS and assignee != agent_name: error {"error": "already_claimed", "assignee": ...}
# 5. If status != APPROVED: error {"error": "not_claimable", "status": ..., "hint": "Only approved specs can be claimed"}
# 6. spec.assignee = agent_name
# 7. load config, call transition(spec, IN_PROGRESS, root, notes=f"Claimed by {agent_name}", auto_commit=cfg.git_auto_commit)
# 8. Return spec.to_dict()
```

CLI signature:
```bash
spec claim <id> [--as <agent_name>] [--yes] [--json]
```

**File to modify:** `src/spec_cli/main.py`
- Add import: `from .commands.claim import cmd_claim`
- Register `@app.command()` for `claim` (~8 lines)

---

### 2. Fix `spec next --json` output

**File:** `src/spec_cli/commands/next_action.py` — line 64–72

Add `"assignee": top.assignee` to the JSON dict so agents can tell if the top spec is already owned.

Also add `"claimable_queue"`: top 3 specs where `status == APPROVED and assignee == ""`, each with `{id, title, age_days}`. Agents don't need a second `list` call to find alternatives.

```python
# In cmd_next, after computing `active`:
claimable = [s for s in active if s.status == SpecStatus.APPROVED and not s.assignee]
claimable.sort(key=lambda s: -_age_days(s.updated_at))
queue = [{"id": s.id, "title": s.title, "age_days": _age_days(s.updated_at)} for s in claimable[:3]]

# In json_out block, add to dict:
"assignee": top.assignee,
"claimable_queue": queue,
```

---

### 3. Fix `spec gate-check --json` output

**File:** `src/spec_cli/commands/gate_check.py` — lines 39–46

Add `"gate_checklist_items": list[str]` — checklist split into an array so agents can iterate items.

```python
# After extracting checklist string:
def _parse_items(checklist: str) -> list[str]:
    items = []
    for line in checklist.splitlines():
        stripped = line.strip()
        if stripped:
            # Remove markdown checkbox prefixes: "- [ ] ", "- [x] ", "- "
            item = re.sub(r'^-\s*\[[ xX]\]\s*', '', stripped)
            item = re.sub(r'^-\s+', '', item)
            if item:
                items.append(item)
    return items

# In json_out block:
"gate_checklist_items": _parse_items(checklist),
```

---

### 4. Update `skill.md` (and `src/spec_cli/SKILL.md` if it exists)

**File:** `skill.md`

Four targeted additions:

**A. Add `spec claim` to Lifecycle section** (after `spec assign`):
```bash
spec claim <id> --yes --json                # atomic: assert approved → assign → in-progress
spec claim <id> --as "my-agent" --yes --json  # specify agent name (default: $SPEC_AGENT)
```

**B. New workflow section: "Workflow: agent picks up and delivers work"**
```bash
spec next --json                                   # 1. find what's available (check assignee + claimable_queue)
spec claim <id> --yes --json                      # 2. atomic claim (validates status, idempotent)
# ... do the work ...
spec run-checks --json                               # 3. checks must pass
spec advance <id> --note "<delivery summary>" --yes --json  # 4. DELIVERY SIGNAL (in-progress → at-gate)
# Note is the delivery receipt — be specific:
# "Implemented X. Tests: 12 pass. Edge case Y handled in file.py:42."
# DO NOT advance past at-gate — that gate belongs to the human.
```

**C. Name the handoff explicitly** in the Gate rule section:
> Moving a spec from `in-progress` to `at-gate` via `spec advance --note "..."` is the agent delivery signal. The `--note` is the delivery receipt the human will read. Be specific.

**D. Add `spec list --claimable` to Discovery section** (after adding the flag in step 5).

---

### 5. Add `--claimable` filter to `spec list`

**File:** `src/spec_cli/commands/list_cmd.py`

One new filter: `--claimable` returns specs where `status == APPROVED and assignee == ""`.

```python
# In cmd_list signature, add:
claimable: bool = False

# In filtering logic (after status filter):
if claimable:
    specs = [s for s in specs if s.status == SpecStatus.APPROVED and not s.assignee]
```

**File:** `src/spec_cli/main.py` — add `claimable: bool = typer.Option(False, "--claimable", help="Only show unclaimed approved specs")` to the `list_specs` command and pass it through to `cmd_list`.

---

## Critical Files

| File | Change |
|---|---|
| `src/spec_cli/commands/claim.py` | **CREATE** — new command |
| `src/spec_cli/main.py` | Register `claim` + `--claimable` on list |
| `src/spec_cli/commands/next_action.py` | Add `assignee` + `claimable_queue` to JSON |
| `src/spec_cli/commands/gate_check.py` | Add `gate_checklist_items` array to JSON |
| `src/spec_cli/commands/list_cmd.py` | Add `--claimable` filter |
| `skill.md` | Add `claim`, agent pickup workflow, handoff naming |

## Existing utilities to reuse

- `storage.find_root`, `storage.find_spec`, `storage.list_specs` — standard discovery pattern used by every command
- `state.transition(spec, new_status, root, notes, auto_commit)` — the lifecycle gate; `claim` calls this exactly like `advance` does
- `config.load_config(root)` — needed to read `git_auto_commit`
- `ui.error(msg, json_out, json_payload)` — standard error output pattern
- `SpecStatus.APPROVED`, `SpecStatus.IN_PROGRESS` — state machine constants

## Verification

```bash
# Install in dev mode
cd /Users/matheus/tiny-spec
uv pip install -e .

# Init a test project
mkdir /tmp/spec-test && cd /tmp/spec-test
spec init

# Create and approve a spec
spec new "Test feature" --template feature --yes --json
spec advance 0001 --yes --json   # draft → approved

# Test claim (happy path)
spec claim 0001 --yes --json     # should: assign + advance to in-progress

# Test claim (already claimed)
spec claim 0001 --yes --json     # should: idempotent success

# Test claim (wrong state)
spec advance 0001 --note "tests pass" --yes --json  # in-progress → at-gate
spec claim 0001 --yes --json     # should: error not_claimable

# Test next --json has assignee + claimable_queue
spec next --json | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'assignee' in d; assert 'claimable_queue' in d"

# Test gate-check --json has items array
spec gate-check 0001 --json | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'gate_checklist_items' in d"

# Test list --claimable
spec new "Feature 2" --yes --json
spec advance 0002 --yes --json   # to approved
spec list --claimable --json     # should show only 0002 (0001 is at-gate, already claimed)
```
