"""Generate CLAUDE.md from project config and constitution."""
from __future__ import annotations

from ..config import Config


def generate_claude_md(cfg: Config, project_name: str) -> str:
    name = cfg.project_name or project_name
    desc = cfg.description or ""
    langs = ", ".join(cfg.languages) if cfg.languages else "—"
    frameworks = ", ".join(cfg.frameworks) if cfg.frameworks else "—"
    libraries = ", ".join(cfg.libraries) if cfg.libraries else "—"
    testing = cfg.testing or "—"
    architecture = cfg.architecture or "—"
    conventions = "\n".join(f"- {c}" for c in cfg.conventions) if cfg.conventions else "- (none defined)"
    out_of_bounds = "\n".join(f"- {c}" for c in cfg.out_of_bounds) if cfg.out_of_bounds else "- (none defined)"

    return f"""# {name}

{desc}

---

## Project context

| | |
|---|---|
| **Languages** | {langs} |
| **Frameworks** | {frameworks} |
| **Libraries** | {libraries} |
| **Architecture** | {architecture} |
| **Testing** | {testing} |

## Conventions

{conventions}

## Out of bounds — never do this

{out_of_bounds}

---

## Session start — always run these first

```bash
spec config --json           # stack, conventions, katas, out_of_bounds
spec export --active --json  # all active specs + bodies + constitution + git history
spec next --json             # highest-priority action right now
```

---

## Spec-driven workflow

Specs live in `.spec/`. Always check the relevant spec before implementing.

```bash
# Discover
spec list --json
spec list --status <status> --json
spec list --full --json              # includes bodies
spec list --assignee "<name>" --json
spec list --stale --json
spec show <id> --json
spec search "<query>" --json
spec next --json
spec stats --json
spec log --last 20 --json
spec log --spec <id> --json

# Create & lifecycle
spec new "<title>" --template <feature|bug|adr|api|data-pipeline|experiment> --ai --yes --json
spec review <id> --json              # AI pre-flight: APPROVE / NEEDS WORK / REJECT
spec advance <id> --yes --json
spec advance <id> --note "..." --yes --json
spec advance <id> --skip-kata --note "reason" --yes --json
spec revert <id> --yes --json
spec close <id> --reason <descoped|wont-fix|superseded|duplicate> --note "..." --yes --json
spec assign <id> "<name>" --json

# Quality
spec run-kata --json
spec run-kata <id> --json
spec gate-check <id> --json

# Context & git
spec config --json
spec export --json
spec export --active --json
spec git-context --json
spec sync --json
```

### Lifecycle
```
draft → approved → in-progress → at-gate → implemented
  ↘                                               ↗
   closed (descoped | wont-fix | superseded | duplicate)
```

- `at-gate → implemented` requires explicit human verification — never pass automatically
- Katas (if configured) block `in-progress → at-gate` automatically
- `.spec/log.md` is an append-only record of all transitions

---

## Agent roster

Specialist agents are in `.claude/agents/`. Each has one job.

| Agent | Invoke when |
|---|---|
| `spec-manager` | Creating/triaging specs, pipeline health, lifecycle management |
| `architect` | Spec is approved and needs a technical plan before coding starts |
| `implementer` | Implementing an approved spec with a plan.md |
| `reviewer` | Verifying implemented code against AC before or at gate |
| `tester` | Writing tests mapped to acceptance criteria |
| `data-engineer` | Data pipeline or experiment specs, schema changes, DQ gates |
| `explorer` | Codebase health check, finding debt, mapping unfamiliar areas |
| `run-reviewer` | After a session — improving agents, CLAUDE.md, constitution |

### Standard workflow
```
spec-manager (creates + approves spec)
  → architect (writes plan.md)
    → implementer (writes code + tests)
      → tester (validates coverage)
        → reviewer (AC compliance check)
          → spec-manager (advances to at-gate)
            → [HUMAN verifies gate checklist]
              → spec-manager (passes gate)
```

---

## Key files

| File | Purpose |
|---|---|
| `.spec/constitution.md` | Governing principles — read before any decision |
| `.spec/config.yaml` | Stack, katas, conventions, out_of_bounds |
| `.spec/log.md` | Append-only event log |
| `.spec/git-context.md` | Recent git history for AI context |
| `.spec/specs/` | Active feature, bug, api, data-pipeline, experiment specs |
| `.spec/decisions/` | Architecture decision records (ADRs) |
"""
