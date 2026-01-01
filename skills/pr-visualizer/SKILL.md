---
name: pr-visualizer
description: >-
  Generates a polished, self-contained HTML page that explains a pull request's (or branch's, or working diff's)
  changes so a human can understand them at a glance — with hand-built interactive SVG graphs (a hover-to-isolate
  module/dependency graph, a swimlane sequence diagram, a top-down decision flowchart), flow diagrams,
  colour-coded file-change cards, a data-model/schema view, edge-case cards, a "decisions" timeline, a
  verification checklist, and an interactive before/after (or beta/standard, old/new) toggle. The output is one
  dependency-free .html file with embedded CSS/JS (no Mermaid/CDN), sticky scroll-spy nav, and a responsive
  layout. Use whenever the user wants to visualize, illustrate, or explain changes as a shareable web page
  rather than prose. Triggers: "visualize this PR", "make an HTML page explaining the changes", "create a
  visual summary of the diff/branch", "explain PR #123 visually", "turn this diff into a webpage", "show me
  these changes as a diagram/graph/flowchart/sequence diagram".
---

# PR Visualizer

Turn a set of code changes into a single, beautiful, self-contained HTML page that makes the changes easy
to understand. The result is a teaching artifact — it should answer "what changed, why, and how does it
flow?" faster than reading the diff.

## Inputs (figure out which one applies)

- **A PR** — number or URL (e.g. "visualize PR #9811"). Use `gh`.
- **A branch / two refs** — e.g. "visualize my branch vs master". Use `git diff`.
- **The working tree** — uncommitted changes. Use `git diff` / `git status`.
- **A plan or design doc** — sometimes there's no diff yet (like a planning session). Then visualize the
  *proposed* changes from the doc, and label the footer "planning artifact — no code written yet".

If the source is ambiguous, ask one short question before proceeding.

## Workflow

### 1. Gather the change set
- PR: `gh pr view <n> --json title,body,headRefName,baseRefName,files,additions,deletions` and
  `gh pr diff <n>`. For large diffs, `gh pr diff <n> --name-only` first, then read the diff in sections.
- Branch/working tree: `git diff <base>...<head>` (or `git diff` for unstaged), `git diff --stat`.
- **Read the actual diff and the key changed files** — do not visualize from the title alone. Open the 1–3
  files that carry the core behavioral change so the diagrams are accurate.

### 2. Understand it (this is the real work)
Extract, from the diff itself (never invent):
- **One-line purpose** and the scope (what's in / out).
- **The single most important change** — the file/function where the behavior actually changes. This gets
  visually flagged as critical.
- **The main flow** — the runtime path the change affects (request → handler → side effect; or
  event → worker → db). This becomes the flow diagram.
- **A branch/variant worth toggling** — most changes have a "before vs after", "feature-flagged vs not",
  "happy path vs error" split. That becomes the interactive toggle (the highest-value UX element).
- **File groups** — new vs edited; group trivial edits together, give the critical one its own row.
- **Edge cases & decisions** — anything in the PR description, comments, or tests that explains a tradeoff.
- **How it's verified** — tests, type/lint/CI checks, manual steps.

### 3. Pick the sections
Use only the sections that fit the change — a tiny PR might be hero + flow + files + verify; a large one
uses everything. Catalog (all optional, reorder freely):
1. **Hero** — title, one-line lede, scope chips.
2. **Problem → Fix callout** — the why, as a paired before/after.
3. **Flow diagram(s)** — horizontal node→arrow→node steps for the main runtime path (CSS, no SVG).
4. **Architecture / dependency graph** *(SVG, interactive)* — node-link map of the touched modules/files
   with typed edges (solid=call, dotted=write, dashed=read) and animated "packets" on the live paths.
   **Hover a node to isolate its call paths** (the JS handles it). Best for PRs that wire several modules
   together. Tip: lay the outbound path L→R and the inbound/webhook path R→L, with shared models in the middle.
5. **Sequence diagram** *(SVG, swimlanes)* — lifelines per participant (Actor/Route/Controller/Client/External/DB),
   time flowing downward, returns dashed, notes/invariants as inline bands. Best for request/response or
   multi-step async handshakes (e.g. create→confirm).
6. **Decision flowchart** *(SVG, top-down)* — process boxes + diamond decisions with yes/no branches. Best for
   branching runtime logic (feature-flag gates, error vs happy path). Often a stronger alternative to the toggle
   when there are >2 outcomes.
7. **Interactive toggle** — switch between two variants of a flow (include it whenever the change has a natural
   binary split). Ends each branch with a clear "verdict" banner. Pairs well with, or substitutes for, #6.
8. **Data / schema** — annotated model or API shape when the PR adds/changes one.
9. **Files changed** — colour-coded cards: green = new, cyan = edited, amber = critical. Path in monospace.
10. **Edge cases** — small cards tagged `resolved` / `by design` / `handled` / `future`.
11. **Decisions timeline** — when the design evolved through choices, show them as a vertical timeline.
12. **Verification** — a checklist.
13. **Footer** — provenance (PR #, branch, or source doc).

**Reach for at least one SVG graph (#4–#6) on any non-trivial PR** — a hovered dependency graph or a sequence
diagram teaches structure far faster than prose or flat cards. Keep them factual: every node/edge must map to
a real module/call in the diff.

### 4. Build from the template
- Copy `assets/template.html` (next to this skill) to the output path. It already contains the full CSS
  design system, sticky scroll-spy nav, and the toggle/observer JS.
- The template's `<!-- COMPONENTS ... -->` comment block is a copy-paste library for every section type —
  flow node, **architecture/dependency graph**, **sequence diagram**, **decision flowchart**, file row,
  edge card, timeline item, callout, schema, checklist, toggle. Fill the `<main>` with the sections you
  chose, wiring each section's `id` to a nav link.
- **SVG graphs:** copy the snippet, then edit node labels and coordinates to match the real diff. Wrap each
  in `.gwrap`. For the dependency graph, give the `<svg>` `class="depgraph"` and tag nodes
  `<g class="gnode" data-id="X">` / edges `<g class="gedge" data-from="X" data-to="Y">` — the template JS
  wires hover-to-isolate automatically (no per-page JS needed). Add `<path class="pkt" pathLength="100">`
  over a call edge for an animated packet; stagger with `style="animation-delay:..."`. All graphs are
  hand-built inline SVG — **never** pull in Mermaid or any CDN.
- Keep it **100% self-contained** — no CDNs, no external fonts/scripts/images. It must open offline.

### 5. Output & open
- Default output path: alongside the source. For a PR/branch in a repo, write to the repo root or a
  `./local/` dir as `pr-<n>-visualization.html` (or `<branch>-visualization.html`). If the source was a doc
  in `~/.claude/plans/`, write the html beside it. Confirm the path with the user if unsure.
- `open <file>` (macOS) / `xdg-open` (Linux) to launch it, then tell the user the path.

## Quality bar

- **Factual** — every node, file card, and claim must trace to the actual diff. If you're unsure what a
  change does, read the file; don't guess. No invented metrics or fake numbers.
- **The toggle is the hook** — a change is far easier to grasp when you can flip between its two states and
  watch the path change. Reach for it.
- **Flag the linchpin** — one critical change, marked amber, with a short "why it matters". Reviewers should
  know where to look first.
- **Scale to the PR** — don't pad a 3-file fix with empty sections; don't cram a 40-file PR into one flow.
- **Responsive & legible** — flows stack on mobile (the template handles this), text stays readable, dark
  theme by default (offer a light variant only if asked).
- **Accessible-ish** — real headings, sufficient contrast, the toggle works by click and the nav by anchor.

## Anti-patterns
- ❌ Generating from the PR title/description without reading the diff.
- ❌ External dependencies (Mermaid CDN, Google Fonts, Tailwind CDN, D3) — breaks offline, defeats "self-contained".
  Graphs are hand-built inline SVG from the template snippets, not a rendered library.
- ❌ A wall of cards with no graph or flow — the structure is what teaches.
- ❌ A dependency graph whose nodes/edges don't map to real modules/calls in the diff (a pretty but fictional graph
  is worse than none).
- ❌ Inventing edge cases or test names that aren't in the PR.
