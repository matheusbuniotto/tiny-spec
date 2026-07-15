## Destination

> What are we trying to reach? One or two sentences — the outcome, not the plan.
> Bad: "Improve onboarding." Good: "New users complete signup and reach their first successful action without contacting support."

## Decisions So Far

> One line per decision already made, each pointing at the spec that holds the detail. This section only gists and links — it never restates.

- [Decision] — see `<spec id>`

## Not Yet Specified

> The fog. Questions that need answering before this can be broken into buildable specs. Each becomes a child spec once it's clear enough to scope.

- [Open question]

## Child Specs

> Create children with `spec new "<title>" --parent <this-map-id>`. This section is informational only — `spec show <this-map-id>` renders the live roster from `parent` links, so don't hand-maintain a duplicate list here.

## Human Gate Checklist

> Before marking this map implemented, verify each item.

- [ ] **Nothing left in "Not Yet Specified"**: every open question graduated into a child spec or was explicitly ruled out of scope
- [ ] **Every child spec is `implemented` or `closed`**: `spec list --parent <this-map-id> --json`
- [ ] **Decisions So Far is current**: does it reflect what actually got built, not what was originally planned?
