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
    conventions = (
        "\n".join(f"- {c}" for c in cfg.conventions) if cfg.conventions else "- (none defined)"
    )
    out_of_bounds = (
        "\n".join(f"- {c}" for c in cfg.out_of_bounds) if cfg.out_of_bounds else "- (none defined)"
    )

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

## Out of bounds

{out_of_bounds}

---

## Spec workflow

Specs live in `.spec/`. Every feature, bug fix, or decision gets a spec before implementation.

```
draft → approved → in-progress → at-gate → implemented
```

- Humans: `init`, `doctor`, `approve`, `gate`, `pass/reject`
- Agents: `boot`, `claim`, `context`, `run-checks`, `deliver`
- `at-gate → implemented` requires explicit human verification — never pass automatically

### Agent session start

```bash
spec boot --json             # rules, next action, claimable queue
spec claim <id> --yes --json # claim approved work
spec context <id> --json     # focused task packet for the claimed spec
```

### Key commands

```bash
# Discover
spec next --json
spec list --json
spec list --status <status> --json
spec show <id> --json
spec context <id> --json

# Create & advance
spec new "<title>" --template <feature|bug|adr|api> --ai --yes --json
spec approve <id> --yes --json
spec claim <id> --as "claude-code" --yes --json
spec deliver <id> --note "AC1: ...; AC2: ...; Checks: ..." --yes --json
spec pass <id> --note "..." --yes --json        # human only
spec reject <id> --note "..." --category missed-ac --yes --json

# Quality
spec validate <id> --json
spec run-checks --json
spec gate-check <id> --json

# Inspect
spec config --json
spec log --last 20 --json
spec stats --json
```

---

## Agents

| Agent | Role |
|---|---|
| `spec-manager` | Creates/triages specs, runs the full pipeline, manages gate |
| `architect` | Turns an approved spec into a plan.md before coding starts |
| `implementer` | Implements the spec, runs checks, delivers to the gate |

Invoke via `"Build <feature> for me"` → spec-manager orchestrates the full cycle and stops at the human gate.

---

## Key files

| File | Purpose |
|---|---|
| `.spec/constitution.md` | Project principles — read before any decision |
| `.spec/config.yaml` | Stack, checks, conventions, out_of_bounds |
| `.spec/log.md` | Append-only event log |
| `.spec/specs/` | Active specs |
| `.spec/decisions/` | ADRs |
"""
