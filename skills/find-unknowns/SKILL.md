---
name: find-unknowns
description: >-
  Workflow for surfacing a task's unknowns before, during, and after
  implementation — blind spot pass, brainstorm/prototype, interview,
  references, implementation plan, deviation notes, quiz. Use when starting
  work in an unfamiliar domain or codebase, when a task feels underspecified,
  when the user says "find my unknowns", "blindspot pass", "what am I
  missing", "help me scope this", or when a long task came back wrong.
argument-hint: [task-or-problem-description]
user-invocable: true
---

# Find Your Unknowns

The prompt is a map; the codebase is the territory. The gap is the user's
unknowns, and every unknown forces the agent to guess. Route by the kind of
unknown:

- **Known unknowns** — user knows what's undecided → Interview
- **Unknown knowns** — "I'll recognize it when I see it" → Brainstorm/Prototype, References
- **Unknown unknowns** — user doesn't know what to ask → Blind Spot Pass

First get the user's starting point: where they are in their thinking, their
experience with the problem and codebase. Prefer a single HTML artifact for
anything visual or reviewable.

## Pre-implementation

**Blind Spot Pass** — Unfamiliar territory. Search the code/web and explain
the user's unknown unknowns: what questions to ask, what good looks like,
prior art, potholes. If they don't know what "good" looks like at all, teach
the domain first instead of generating variations to pick from.

**Brainstorm & Prototype** — "Know it when I see it" criteria. Produce several
genuinely different directions as cheap disposable mocks (one HTML file, fake
data, no wiring) so the user reacts before changes get expensive. At session
start: brainstorm approaches cheapest → most ambitious to set scope.

**Interview** — One question at a time, prioritizing questions whose answer
would change the architecture. Stop when answers stop changing the design.

**References** — When pointing beats describing. Find source code that does
what they want and reimplement its semantics, even across languages. Source
code beats screenshots and prose.

**Implementation Plan** — Lead with decisions most likely to change: data
models, type interfaces, anything user-facing. Bury mechanical refactoring at
the bottom.

## During implementation

**Implementation Notes** — Keep `implementation-notes.md`. When an edge case
forces deviation from the plan: pick the conservative option, log it under
"Deviations", keep going.

## Post-implementation

**Pitch / Explainer** — Package prototype + spec + notes into one shareable
doc for buy-in. Lead with the demo; show the anticipated failure points were
accounted for.

**Quiz** — Report the change with context and intuition, ending in a quiz the
user must pass before merging. Diffs hide behavior that depends on existing
code paths.
