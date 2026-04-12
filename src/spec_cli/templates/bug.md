## Summary

> One sentence: what breaks, where, and for whom.
> Example: "Authenticated users get a 500 error when uploading files larger than 5 MB via the `/upload` endpoint."

## Severity

> **Impact**: [Critical / High / Medium / Low]
> **Frequency**: [Always / Often / Rare / Cannot reproduce reliably]
> **Affected versions**: [e.g. v1.2.3+, or `main` since commit `abc123`]
> **Who is affected**: [All users / Specific role / Specific environment]

## Reproduction Steps

> Must be a deterministic recipe. If it's flaky, say so explicitly and describe the trigger condition.

**Environment**: [OS, browser/client version, Python/Node version, staging/prod]

1. [Step one — be specific about inputs, state, and timing]
2. [Step two]
3. Observe: [exact error message, wrong output, or missing behavior]

**Minimal repro** (if possible):
```
[command, curl, or code snippet that reproduces the issue in isolation]
```

## Expected Behavior

> What should happen at step 3 instead?

## Actual Behavior

> What actually happens? Include error messages verbatim, stack traces, or screenshots if relevant.

## Root Cause

> Leave as `> Under investigation` until identified.
> Once known: explain the exact code path / condition that causes the bug. Link to the relevant file/line.

## Fix Plan

> How will we fix it? Be specific enough that an engineer (or agent) can implement without guessing.
> Call out: is this a targeted fix or does it require a broader refactor?

### Risk

> What could break if we fix this? What existing tests cover the affected area?

## Verification

- [ ] Original repro steps no longer produce the bug
- [ ] Regression test added that would have caught this
- [ ] Fix is isolated — no unrelated behavior changed

## Human Gate Checklist

> When the AI says "fixed", the human verifies each item before passing the gate.

- [ ] **Reproduce the original bug first**: follow repro steps above on the unfixed version — does it still fail? (establishes baseline)
- [ ] **Apply fix and retest**: same steps on the fixed version — bug is gone?
- [ ] **Run the test suite**: `<test command>` — all pass, including the new regression test?
- [ ] **Check one related flow**: [describe a nearby scenario that should still work — prevents silent regressions]
- [ ] **Read the diff**: `git diff main` — fix is minimal, no unrelated changes, no debug statements?
