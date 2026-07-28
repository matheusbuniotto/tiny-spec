#!/usr/bin/env bash
#
# spec-loop.sh — spec-driven agent loop
#
# A reference implementation for running specs with AI agents.
# Each iteration: pick → advance → implement → verify → advance to done.
#
# Usage:
#   bash scripts/spec-loop.sh --pick next --agent kimi          # auto-detect
#   bash scripts/spec-loop.sh --pick 0003 --agent codex         # single spec
#   bash scripts/spec-loop.sh --pick next --test manual         # manual impl
#   bash scripts/spec-loop.sh --pick next --verifier human      # human verify (default)
#   bash scripts/spec-loop.sh --pick next --verifier codex      # agent verify
#   bash scripts/spec-loop.sh --pick next --worktree            # isolated worktree
#   bash scripts/spec-loop.sh --pick next --max 5               # max 5 specs
#   bash scripts/spec-loop.sh --pick next --dry-run             # show plan only
#
# Requirements:
#   - spec CLI (tiny-spec: uvx tiny-spec or pip install tiny-spec)
#   - git
#   - One of: kimi, pi, codex, claude (for --test agent)
#   - python3 (for JSON extraction of gate checklist)
#
# ─── Project configuration — EDIT THESE ─────────────────────────────────────
#
# The system prompt passed to the implementation agent. Replace with your
# project's description, stack, conventions, and out-of-bounds constraints.
# The {{SPEC_BODY}} placeholder is replaced at runtime with the full spec.
AGENT_SYSTEM_PROMPT="You are an autonomous implementation agent.

## Assignment
Implement spec #{{SPEC_ID}}: \"{{SPEC_TITLE}}\"

## Spec
{{SPEC_BODY}}

## Instructions
1. Read the spec — every AC must be met.
2. Read .spec/constitution.md for principles/constraints.
3. Read .spec/config.yaml for project context.
4. Implement ACs in order (AC1 = thinnest end-to-end slice first).
5. Make MINIMAL changes — stay in scope. Don't touch unrelated code.
6. Self-verify against the Human Gate Checklist at the end of the spec.
7. Run: spec verify {{SPEC_ID}}
8. If checks pass, summarize what you did and which ACs are met.
9. If checks fail, fix and re-verify. Don't report \"done\" if anything is red.
10. Do NOT git commit/push — the loop script handles that.

## Notes
- Keep it simple. No speculative abstractions.
- Match existing code conventions.
- Stay within project out-of-bounds constraints (config.yaml)."

set -euo pipefail

# ─── Colors ───────────────────────────────────────────────────────────────────
if [[ -t 2 ]]; then
    B="\033[1m"; D="\033[2m"; R="\033[31m"; G="\033[32m"
    Y="\033[33m"; B0="\033[34m"; C="\033[36m"; M="\033[35m"; X="\033[0m"
else
    B=""; D=""; R=""; G=""; Y=""; B0=""; C=""; M=""; X=""
fi

# ─── Defaults ─────────────────────────────────────────────────────────────────
PICK="next"
TEST="agent"
MAX_ITERS=0
DRY_RUN=false
VERBOSE=false
AGENT_NAME="loop-agent"
AGENT=""
VERIFIER="human"
VERIFY_AGENT=""
WORKTREE=false
WORKTREE_DIR=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_DIR/.spec/logs"
mkdir -p "$LOG_DIR"

# Deferred human-verification summaries
HUMAN_SUMMARIES=()

# ─── Args ─────────────────────────────────────────────────────────────────────
usage() {
    cat <<'EOF'
spec-loop.sh — spec-driven agent loop

  bash spec-loop.sh [--pick <next|ID>] [--agent <kimi|pi|codex|claude>]
                    [--test <agent|manual>] [--verifier <agent|human>]
                    [--max N] [--verbose] [--dry-run] [--worktree]

  --pick <val>       next (default) or spec ID like 0003
  --agent <val>      kimi | pi | codex | claude (default: auto-detect)
  --test <val>       agent (default) | manual
  --verifier <val>   kimi | pi | codex | claude | human (default: human)
                     agent verifier gets fresh-context (ACs + diff + checklist)
                     human verifier defers summary at end of loop
  --max <N>          max iterations (0 = unlimited, default)
  --verbose          show detailed phase-by-phase logs
  --worktree         isolated git worktree per spec (merge to master on done)
  --dry-run          show plan, change nothing
  -h, --help         this help
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pick)        PICK="$2"; shift 2 ;;
        --test)        TEST="$2"; shift 2 ;;
        --agent)       AGENT="$2"; shift 2 ;;
        --verifier)    VERIFIER="$2"; shift 2 ;;
        --max)         MAX_ITERS="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=true; shift ;;
        --worktree)    WORKTREE=true; shift ;;
        --verbose)     VERBOSE=true; shift ;;
        --agent-name)  AGENT_NAME="$2"; shift 2 ;;
        -h|--help)     usage ;;
        *) echo "${R}unknown: $1${X}" >&2; usage ;;
    esac
done

# ─── Output helpers ──────────────────────────────────────────────────────────
v()  { $VERBOSE && echo -e "$*" >&2 || true; }
out() { echo -e "$*" >&2; }
status()    { out "  ${D}$1${X}"; }
good()      { out "  ${G}✓${X} $1"; }
bad()       { out "  ${R}✗${X} $1"; }
hesitate()  { out "  ${Y}⚠${X} $1"; }
hdr()       { v "\n${B}${B0}── $1 ──${X}"; }

require() {
    command -v "$1" &>/dev/null || { bad "missing: $1"; exit 1; }
}
require spec

# ─── Spinner ──────────────────────────────────────────────────────────────────
SP_PID=""

_start_spin() {
    [[ -t 2 ]] || return
    $VERBOSE && return
    local msg="$1"
    SP_START=$SECONDS
    (
        local sc=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
        local i=0
        while true; do
            local e=$((SECONDS - SP_START))
            local t="${e}s"
            [[ $e -ge 60 ]] && t="$((e/60))m$(printf '%02d' $((e%60)))"
            printf "\r${D}${sc[$((i%10))]}${X} ${B}%s${X} ${D}(%s)${X}   " "$msg" "$t" >&2
            i=$((i+1)); sleep 0.15
        done
    ) &
    SP_PID=$!
}

_stop_spin() {
    [[ -n "$SP_PID" ]] && kill "$SP_PID" 2>/dev/null && wait "$SP_PID" 2>/dev/null || true
    SP_PID=""
    [[ -t 2 ]] && ! $VERBOSE && printf "\r\033[K" >&2
}

quick() {
    local label="$1"; shift
    if $DRY_RUN; then status "$label (dry-run)"; return 0; fi
    if $VERBOSE; then
        v "  ${D}$label${X}"
        "$@" 2>&1 | sed 's/^/    /' >&2
        return "${PIPESTATUS[0]}"
    fi
    _start_spin "$label"
    "$@" >/dev/null 2>&1
    local ec=$?
    _stop_spin
    return $ec
}

# ─── Agent detection ─────────────────────────────────────────────────────────
SUPPORTED_AGENTS=("kimi" "pi" "codex" "claude")

detect_agent() {
    if [[ -n "$AGENT" ]]; then
        [[ " ${SUPPORTED_AGENTS[*]} " =~ " ${AGENT} " ]] || { bad "unknown agent: $AGENT"; exit 1; }
        command -v "$AGENT" &>/dev/null || { bad "agent not found: $AGENT"; exit 1; }
        return
    fi
    for a in "${SUPPORTED_AGENTS[@]}"; do
        if command -v "$a" &>/dev/null; then AGENT="$a"; return; fi
    done
    bad "no agent found (need one of: ${SUPPORTED_AGENTS[*]})"
    exit 1
}

[[ "$TEST" == "agent" ]] && detect_agent

# ─── Verifier detection ──────────────────────────────────────────────────────
detect_verifier() {
    if [[ "$VERIFIER" == "human" ]]; then
        VERIFY_AGENT=""
        return
    fi
    [[ " ${SUPPORTED_AGENTS[*]} " =~ " ${VERIFIER} " ]] || { bad "unknown verifier: $VERIFIER"; exit 1; }
    command -v "$VERIFIER" &>/dev/null || { bad "verifier not found: $VERIFIER"; exit 1; }
    VERIFY_AGENT="$VERIFIER"
}
detect_verifier

# ─── JSON helper (no jq) ─────────────────────────────────────────────────────
jval() {
    local json="$1" key="$2"
    echo "$json" | sed 's/[{}]/\n/g' \
        | grep -o "\"${key}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 \
        | sed "s/.*\"${key}\"[[:space:]]*:[[:space:]]*\"//;s/\"$//"
}

# ─── Pick ────────────────────────────────────────────────────────────────────
pick_spec() {
    hdr "PICK"

    if [[ "$PICK" != "next" ]]; then
        local json
        json=$(spec show "$PICK" --json 2>/dev/null) || { bad "spec $PICK not found"; exit 1; }
        SPEC_ID=$(jval "$json" id)
        SPEC_TITLE=$(jval "$json" title)
        SPEC_STATUS=$(jval "$json" status)
        SPEC_BLOCKED=$(echo "$json" | grep -o '"blocked_by"[[:space:]]*:[[:space:]]*\[[^]]*\]' | sed 's/.*\[//;s/\]//' | tr -d '" ')
        return
    fi

    local next_json
    next_json=$(spec next --json 2>/dev/null || echo "")
    if [[ -n "$next_json" ]]; then
        SPEC_ID=$(jval "$next_json" id)
        SPEC_TITLE=$(jval "$next_json" title)
        SPEC_STATUS=$(jval "$next_json" status)
        SPEC_BLOCKED=$(echo "$next_json" | grep -o '"blocked_by"[[:space:]]*:[[:space:]]*\[[^]]*\]' | sed 's/.*\[//;s/\]//' | tr -d '" ')
    fi

    # If blocked, scan for unblocked draft
    if [[ -z "$SPEC_ID" ]] || [[ "$SPEC_BLOCKED" =~ [0-9] ]]; then
        v "  next is blocked — scanning drafts..."
        local best_id="" best_title=""
        local all_ids
        all_ids=$(spec list 2>/dev/null \
            | grep -oE '│[[:space:]]*0[0-9]{3}[[:space:]]*│' \
            | sed 's/│//g' | tr -d ' ' | sort -u)

        for sid in $all_ids; do
            local j st bl
            j=$(spec show "$sid" --json 2>/dev/null || echo "")
            [[ -z "$j" ]] && continue
            st=$(jval "$j" status)
            bl=$(echo "$j" | grep -o '"blocked_by"[[:space:]]*:[[:space:]]*\[[^]]*\]' | sed 's/.*\[//;s/\]//' | tr -d '" ')
            [[ "$st" != "draft" ]] && continue

            local blocked=false
            if [[ -n "$bl" ]] && [[ "$bl" =~ [0-9] ]]; then
                for dep in $bl; do
                    local dep_st
                    dep_st=$(jval "$(spec show "$dep" --json 2>/dev/null || echo '{}')" status)
                    [[ "$dep_st" != "implemented" ]] && [[ "$dep_st" != "closed" ]] && { blocked=true; break; }
                done
            fi

            if ! $blocked; then
                if [[ -z "$best_id" ]] || [[ "$sid" < "$best_id" ]]; then
                    best_id="$sid"
                    best_title=$(jval "$j" title)
                fi
            fi
        done

        if [[ -n "$best_id" ]]; then
            SPEC_ID="$best_id"; SPEC_TITLE="$best_title"
            SPEC_STATUS="draft"; SPEC_BLOCKED=""
        else
            if [[ -n "$SPEC_ID" ]]; then
                hesitate "all drafts blocked — next is #${SPEC_ID} (blocked by: ${SPEC_BLOCKED:-?})"
            else
                bad "no specs available"; exit 0
            fi
        fi
    fi
}

# ─── Advance to in-progress ──────────────────────────────────────────────────
advance_to_in_progress() {
    hdr "ADVANCE"
    WORKTREE_DIR=""

    if [[ "$SPEC_STATUS" == "draft" ]]; then
        if $DRY_RUN; then status "advance (dry-run)"; return; fi
        spec advance "$SPEC_ID" --yes --json >/dev/null 2>&1 || { bad "draft → approved failed"; exit 1; }
        v "  draft → approved"
    fi

    if $DRY_RUN; then status "claim (dry-run)"; return; fi

    local claim_out
    if $WORKTREE; then
        claim_out=$(spec claim "$SPEC_ID" --as "$AGENT_NAME" --worktree --yes --json 2>&1) || {
            local cur_st
            cur_st=$(jval "$(spec show "$SPEC_ID" --json 2>/dev/null)" status)
            if [[ "$cur_st" == "in-progress" ]]; then
                hesitate "already in-progress (worktree may exist)"
                local wt
                wt=$(git worktree list 2>/dev/null | grep "spec-${SPEC_ID}" | awk '{print $1}')
                [[ -n "$wt" ]] && WORKTREE_DIR="$wt"
                return
            else
                bad "claim failed (status: $cur_st)"; exit 1
            fi
        }
    else
        claim_out=$(spec claim "$SPEC_ID" --as "$AGENT_NAME" --yes --json 2>&1) || {
            local cur_st
            cur_st=$(jval "$(spec show "$SPEC_ID" --json 2>/dev/null)" status)
            if [[ "$cur_st" == "in-progress" ]]; then
                hesitate "already in-progress"
            else
                bad "claim failed (status: $cur_st)"; exit 1
            fi
        }
    fi

    if $WORKTREE; then
        WORKTREE_DIR=$(git worktree list 2>/dev/null | grep "spec-${SPEC_ID}" | awk '{print $1}')
        if [[ -z "$WORKTREE_DIR" ]]; then
            WORKTREE_DIR="${PROJECT_DIR}-spec-${SPEC_ID}"
        fi
        v "  worktree: $WORKTREE_DIR"
    fi
    v "  claimed as $AGENT_NAME"
}

# ─── Agent invocation ────────────────────────────────────────────────────────
invoke_agent() {
    local prompt_file="$1" output_log="$2" label="$3"
    local work_dir="$PROJECT_DIR"
    [[ -n "$WORKTREE_DIR" ]] && work_dir="$WORKTREE_DIR"
    cd "$work_dir"

    local cmd_pid=""

    _run_agent() {
        case "$AGENT" in
            kimi)   kimi -p "$(cat "$prompt_file")" --auto --add-dir "$work_dir" ;;
            pi)     pi --print --no-session "$(cat "$prompt_file")" ;;
            codex)  codex exec --sandbox workspace-write - < "$prompt_file" ;;
            claude) claude -p --output-format text --permission-mode acceptEdits --add-dir "$work_dir" < "$prompt_file" ;;
            *)      bad "unknown agent: $AGENT"; return 1 ;;
        esac
    }

    _run_agent >"$output_log" 2>&1 &
    cmd_pid=$!

    if $VERBOSE; then
        v "  ${D}agent: $AGENT${X}"
        wait "$cmd_pid" 2>/dev/null
        return $?
    fi

    local sc=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local i=0 start=$SECONDS last_hb=0

    while kill -0 "$cmd_pid" 2>/dev/null; do
        local e=$((SECONDS - start))
        local t="${e}s"
        [[ $e -ge 60 ]] && t="$((e/60))m$(printf '%02d' $((e%60)))"
        printf "\r${D}${sc[$((i%10))]}${X} ${B}%s${X} ${D}(%s)${X}   " "$label" "$t" >&2
        i=$((i+1))

        if [[ $((e - last_hb)) -ge 30 ]]; then
            last_hb=$e
            printf "\n${D}  … %s (%s)${X}\n" "$label" "$t" >&2
        fi
        sleep 0.15
    done

    wait "$cmd_pid" 2>/dev/null
    local ec=$?
    printf "\r\033[K" >&2

    local e=$((SECONDS - start))
    local t="${e}s"
    [[ $e -ge 60 ]] && t="$((e/60))m$(printf '%02d' $((e%60)))"

    if [[ $ec -eq 0 ]]; then
        good "$label ($t)"
    else
        bad "$label ($t, exit $ec)"
    fi
    return $ec
}

# ─── Build prompt ────────────────────────────────────────────────────────────
build_prompt() {
    local spec_body
    spec_body=$(spec show "$SPEC_ID" --full 2>/dev/null | sed 's/^/  /')

    local work_dir="$PROJECT_DIR"
    [[ -n "$WORKTREE_DIR" ]] && work_dir="$WORKTREE_DIR"

    echo "$AGENT_SYSTEM_PROMPT" \
        | sed "s/{{SPEC_ID}}/$SPEC_ID/g" \
        | sed "s/{{SPEC_TITLE}}/$(echo "$SPEC_TITLE" | sed 's/[\/&]/\\&/g')/g" \
        | sed "s/{{SPEC_BODY}}/$(echo "$spec_body" | sed 's/[\/&]/\\&/g')/g" \
        | sed "s|{{PROJECT_DIR}}|$work_dir|g"
}

# ─── Run agent ────────────────────────────────────────────────────────────────
run_agent() {
    hdr "IMPLEMENT"
    local prompt
    prompt=$(build_prompt)
    local prompt_file="$LOG_DIR/${SPEC_ID}-prompt.txt"
    echo "$prompt" > "$prompt_file"

    if $DRY_RUN; then
        status "agent (dry-run)"
        $VERBOSE && head -20 "$prompt_file" | sed 's/^/    /' >&2
        return 0
    fi

    local agent_log="$LOG_DIR/${SPEC_ID}-agent.log"
    v "  prompt: $prompt_file"
    v "  log:    $agent_log"

    invoke_agent "$prompt_file" "$agent_log" "implement #${SPEC_ID}"
    local ec=$?
    [[ $ec -ne 0 ]] && v "  log: $agent_log"
    return $ec
}

# ─── Verification ─────────────────────────────────────────────────────────────
# Return codes: 0=PASS  1=FAIL  2=NEEDS_HUMAN  3=HUMAN_VERIFY (deferred)
run_verification() {
    hdr "VERIFY"
    if $DRY_RUN; then status "verify (dry-run)"; return 0; fi

    # Step 1: spec verify (automated checks)
    v "  spec verify..."
    set +e
    spec verify "$SPEC_ID" --json >/dev/null 2>&1
    local vexit=$?
    set -e
    if [[ $vexit -ne 0 ]]; then
        v "  spec verify: no checks configured (expected early on)"
    else
        v "  spec verify: passed"
    fi

    # Step 2: gather evidence
    local gate_check ac_text diff_ctx

    # Gate checklist: use --json + python3
    local gate_json
    gate_json=$(spec gate-check "$SPEC_ID" --json 2>/dev/null || echo "")
    if [[ -n "$gate_json" ]] && command -v python3 &>/dev/null; then
        gate_check=$(python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(d.get('gate_checklist', ''))
except: pass
" <<< "$gate_json" 2>/dev/null || spec gate-check "$SPEC_ID" 2>/dev/null || echo "")
    else
        gate_check=$(spec gate-check "$SPEC_ID" 2>/dev/null || echo "")
    fi

    # ACs from raw spec file
    local spec_file
    spec_file=$(find "$PROJECT_DIR/.spec/specs" -name "${SPEC_ID}-*.md" 2>/dev/null | head -1)
    if [[ -n "$spec_file" ]]; then
        ac_text=$(grep -E '^\s*-\s*\[ \]\s*\*\*AC' "$spec_file" 2>/dev/null || echo "")
    fi

    # Git diff stat
    diff_ctx=$(git diff --stat 2>/dev/null || echo "")
    if $WORKTREE && [[ -n "$WORKTREE_DIR" ]]; then
        diff_ctx=$(git -C "$WORKTREE_DIR" diff --stat 2>/dev/null || echo "")
    fi

    # ─── Branch: human vs agent verifier ────────────────────────────────────
    if [[ -z "$VERIFY_AGENT" ]]; then
        local summary
        summary=$(build_human_summary "$ac_text" "$gate_check" "$diff_ctx")
        HUMAN_SUMMARIES+=("$summary")
        out "  ${Y}▣${X} human verify — #${SPEC_ID} (deferred to end of loop)"
        return 3
    fi

    # AGENT verification (fresh context)
    local review_prompt
    review_prompt=$(cat <<REVIEW
You are a verification agent. You did NOT implement this spec — you are reviewing someone else's work with fresh eyes.

## Spec #${SPEC_ID}: "${SPEC_TITLE}"

## Acceptance Criteria
${ac_text}

## Human Gate Checklist
${gate_check}

## Diff Summary
${diff_ctx}

## Task
For EACH acceptance criterion AND each gate checklist item:
1. Actually do the verification (run command, check diff, walk path).
2. Report PASS or FAIL with evidence — cite the command you ran and what you saw.

## Scoring rules — READ CAREFULLY
- PASS only if the AC is demonstrably met. FAIL only if the AC is genuinely not met.
- Pre-existing conditions are NOT failures. If a file was untracked/dirty BEFORE this spec, that's not a FAIL.
- Trivial wording differences in READMEs/comments are NOT failures — only flag if the intent is wrong.
- Use \`git diff\` (not \`git status\`) to verify "unchanged" requirements — untracked != modified.
- If a check needs human interaction (visual inspection, product judgment), report NEEDS HUMAN — not FAIL.

End your output with exactly one line:
  VERDICT: PASS
  VERDICT: FAIL
  VERDICT: NEEDS HUMAN

Be honest but practical. Run actual commands. Don't be pedantic.
REVIEW
)

    local review_file="$LOG_DIR/${SPEC_ID}-review-prompt.txt"
    echo "$review_prompt" > "$review_file"
    local review_log="$LOG_DIR/${SPEC_ID}-review.log"
    v "  review log: $review_log"

    local saved_agent="$AGENT"
    AGENT="$VERIFY_AGENT"
    invoke_agent "$review_file" "$review_log" "verify #${SPEC_ID}"
    local rc=$?
    AGENT="$saved_agent"
    [[ $rc -ne 0 ]] && return 1

    local verdict
    verdict=$(grep -i "VERDICT:" "$review_log" | tail -1 \
        | sed 's/.*VERDICT:[[:space:]]*//I' | tr '[:lower:]' '[:upper:]')

    case "$verdict" in
        *PASS*)   return 0 ;;
        *FAIL*)   return 1 ;;
        *HUMAN*|*) return 2 ;;
    esac
}

# ─── Human verification summary ──────────────────────────────────────────────
build_human_summary() {
    local ac_text="$1" gate_check="$2" diff_ctx="$3"
    local spec_file
    spec_file=$(find "$PROJECT_DIR/.spec/specs" -name "${SPEC_ID}-*.md" 2>/dev/null | head -1)

    local ds="$diff_ctx"
    [[ -z "$ds" ]] && ds="  (no changes or not in a worktree)"

    cat <<SUMMARY
────────────────────────────────────────────────────────────────────────
  #${SPEC_ID} — ${SPEC_TITLE}
  spec:  ${spec_file:-.spec/specs/${SPEC_ID}-*.md}
  log:   ${LOG_DIR}/${SPEC_ID}-agent.log

  ▸ WHAT TO VALIDATE

${ac_text}

  ▸ GATE CHECKLIST (do each one)

${gate_check}

  ▸ CHANGES (git diff --stat)
${ds}

  ▸ VERDICT — when done, run:
    spec advance ${SPEC_ID} --yes         # mark implemented
    # or: spec revert ${SPEC_ID} --yes    # send back to draft
────────────────────────────────────────────────────────────────────────
SUMMARY
}

print_human_summaries() {
    local count=${#HUMAN_SUMMARIES[@]}
    [[ $count -eq 0 ]] && return

    out ""
    out "${B}${Y}╔══════════════════════════════════════════════════════╗${X}"
    out "${B}${Y}║  HUMAN VERIFICATION — ${count} spec(s) to validate        ║${X}"
    out "${B}${Y}╚══════════════════════════════════════════════════════╝${X}"
    for s in "${HUMAN_SUMMARIES[@]}"; do
        out "$s"
    done
}

# ─── Advance to done ──────────────────────────────────────────────────────────
advance_to_done() {
    hdr "ADVANCE → DONE"
    if $DRY_RUN; then status "advance (dry-run)"; return; fi

    if $WORKTREE && [[ -n "$WORKTREE_DIR" ]]; then
        v "  committing in worktree..."
        git -C "$WORKTREE_DIR" add -A 2>/dev/null || true
        git -C "$WORKTREE_DIR" commit -m "spec(${SPEC_ID}): implement" 2>/dev/null || true
    fi

    spec advance "$SPEC_ID" --yes --json >/dev/null 2>&1 \
        || spec advance "$SPEC_ID" --note "Agent verified" --yes --json >/dev/null 2>&1 \
        || { bad "could not advance to at-gate"; return 1; }
    v "  in-progress → at-gate"

    spec advance "$SPEC_ID" --note "Implemented and verified by $AGENT_NAME" --yes --json >/dev/null 2>&1 \
        || spec advance "$SPEC_ID" --note "No checks; manual verify" --skip-checks --yes --json >/dev/null 2>&1 \
        || { bad "could not advance to implemented"; return 1; }
    v "  at-gate → implemented"

    if $WORKTREE && [[ -n "$WORKTREE_DIR" ]]; then
        local branch
        branch=$(git -C "$WORKTREE_DIR" branch --show-current 2>/dev/null)
        v "  merging $branch → master..."
        git -C "$PROJECT_DIR" checkout master 2>/dev/null
        git -C "$PROJECT_DIR" merge "$branch" --no-edit -X theirs 2>/dev/null || {
            hesitate "merge conflict — keeping worktree at $WORKTREE_DIR for manual resolution"
            return 0
        }
        v "  merged"
        git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
        git branch -d "$branch" 2>/dev/null || true
        WORKTREE_DIR=""
        v "  worktree cleaned up"
    fi

    spec sync 2>/dev/null || true
    v "  synced"
}

# ─── Failure ──────────────────────────────────────────────────────────────────
handle_failure() {
    hdr "FAILURE"
    if $DRY_RUN; then status "revert (dry-run)"; return; fi

    if $WORKTREE && [[ -n "$WORKTREE_DIR" ]]; then
        local branch
        branch=$(git -C "$WORKTREE_DIR" branch --show-current 2>/dev/null)
        v "  discarding worktree..."
        git -C "$PROJECT_DIR" checkout master 2>/dev/null || true
        git -C "$WORKTREE_DIR" add -A 2>/dev/null || true
        git -C "$WORKTREE_DIR" commit -m "spec(${SPEC_ID}): revert (failed)" 2>/dev/null || true
        git -C "$PROJECT_DIR" merge "spec/${SPEC_ID}" --no-edit -X theirs 2>/dev/null || true
        git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
        git branch -D "spec/${SPEC_ID}" 2>/dev/null || true
        WORKTREE_DIR=""
        v "  worktree discarded"
    fi

    spec revert "$SPEC_ID" --note "Agent failed e2e (attempt $1)" --yes --json >/dev/null 2>&1 || true
    spec sync 2>/dev/null || true
    v "  reverted"
}

# ─── Main ─────────────────────────────────────────────────────────────────────
main() {
    if $DRY_RUN; then
        out "${D}── dry run ──${X}\n"
    fi
    out "${B}spec loop${X} ${D}— pick:$PICK agent:${AGENT:-auto} test:$TEST verifier:$VERIFIER max:${MAX_ITERS:-∞} worktree:$WORKTREE${X}"

    local iter=0 max_retries=2 start=$SECONDS

    while true; do
        iter=$((iter + 1))
        [[ $MAX_ITERS -gt 0 && $iter -gt $MAX_ITERS ]] && break
        if ! $VERBOSE; then out ""; fi

        # 1. Pick
        SPEC_ID="" SPEC_TITLE="" SPEC_STATUS="" SPEC_BLOCKED=""
        pick_spec
        [[ -z "$SPEC_ID" ]] && { hesitate "nothing to pick — done"; break; }

        if [[ "$SPEC_STATUS" == "implemented" ]]; then
            good "#${SPEC_ID} already done"
            [[ "$PICK" == "next" ]] && continue || break
        fi

        out "${B}#${SPEC_ID}${X} ${D}${SPEC_TITLE}${X}"

        # 2. Advance
        if $VERBOSE; then advance_to_in_progress; else
            if $DRY_RUN; then status "advance (dry-run)"; else
                advance_to_in_progress
            fi
        fi

        # 3. Implement
        if [[ "$TEST" == "manual" ]]; then
            hdr "MANUAL"
            spec show "$SPEC_ID" --full | sed 's/^/  /' >&2
            echo "" >&2
            read -rp "$(echo -e "${B}press ENTER when done…${X}")" </dev/tty
        else
            local retry=0
            while true; do
                retry=$((retry + 1))
                if run_agent; then break; else
                    if [[ $retry -ge $max_retries ]]; then
                        bad "agent failed ($max_retries)x — #${SPEC_ID}"
                        handle_failure "$retry"
                        exit 1
                    fi
                    hesitate "retry $retry/$max_retries"
                fi
            done
        fi

        # 4. Verify
        local vr=0
        run_verification || vr=$?

        case $vr in
            0)
                if $DRY_RUN; then
                    good "verify (dry-run) — would advance to done"
                else
                    advance_to_done
                    good "#${SPEC_ID} done"
                fi
                ;;
            1)
                bad "verification failed — #${SPEC_ID}"
                if [[ "$TEST" == "agent" ]]; then
                    handle_failure 1
                    v "  log: $LOG_DIR/${SPEC_ID}-review.log"
                    exit 1
                else
                    exit 1
                fi
                ;;
            2)
                hesitate "needs human review — #${SPEC_ID}"
                v "  log: $LOG_DIR/${SPEC_ID}-review.log"
                if [[ "$TEST" == "agent" ]] && ! $DRY_RUN; then
                    spec advance "$SPEC_ID" --note "needs human gate review" --yes --json >/dev/null 2>&1 || true
                    spec sync 2>/dev/null || true
                fi
                out "  ${D}review then: spec advance $SPEC_ID --yes${X}"
                exit 0
                ;;
            3)
                # HUMAN_VERIFY: spec stays in-progress, deferred to end-of-loop summary
                if ! $DRY_RUN; then
                    if $WORKTREE && [[ -n "$WORKTREE_DIR" ]]; then
                        git -C "$WORKTREE_DIR" add -A 2>/dev/null || true
                        git -C "$WORKTREE_DIR" commit -m "spec(${SPEC_ID}): implement (awaiting human verify)" 2>/dev/null || true
                        local branch
                        branch=$(git -C "$WORKTREE_DIR" branch --show-current 2>/dev/null)
                        git -C "$PROJECT_DIR" checkout master 2>/dev/null || true
                        git -C "$PROJECT_DIR" merge "$branch" --no-edit -X theirs 2>/dev/null || {
                            hesitate "merge conflict — keeping worktree at $WORKTREE_DIR"
                        }
                        git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
                        git branch -d "$branch" 2>/dev/null || true
                        WORKTREE_DIR=""
                    else
                        git -C "$PROJECT_DIR" add -A 2>/dev/null || true
                        git -C "$PROJECT_DIR" commit -m "spec(${SPEC_ID}): implement (awaiting human verify)" 2>/dev/null || true
                    fi
                    spec sync 2>/dev/null || true
                fi
                [[ "$PICK" != "next" ]] && {
                    out "  ${D}single spec — stopping for human verify${X}"
                    break
                }
                continue
                ;;
        esac

        # 5. Loop?
        [[ "$PICK" != "next" ]] && { good "single spec mode — done"; break; }
        [[ "$TEST" == "manual" ]] && {
            echo "" >&2
            read -rp "$(echo -e "${B}continue? [Y/n]${X} ")" cont </dev/tty
            [[ "$cont" =~ ^[Nn] ]] && break
        }
    done

    print_human_summaries

    local e=$((SECONDS - start))
    local t="${e}s"
    [[ $e -ge 60 ]] && t="$((e/60))m$(printf '%02d' $((e%60)))"
    out ""
    out "${B}done${X} ${D}— $iter iteration(s) in $t${X}"
}

main
