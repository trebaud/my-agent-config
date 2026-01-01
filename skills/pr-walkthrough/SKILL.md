---
name: pr-walkthrough
description: >-
  Generates a self-contained HTML page that walks a human reviewer through a
  pull request as a guided journey, ordered by trust: it starts at entry points
  and trust boundaries (route handlers, workers/jobs, CLI commands, webhooks,
  event consumers) and follows the call graph down into business logic. The
  page has a trust-flow map, numbered "stops" grouped by entry point,
  what-to-check questions tagged by trust concern, a skim batch for trivial
  changes, and browser-persisted progress tracking with per-stop flags and
  notes that export as a markdown review draft. Use when the
  user says "walk me through this PR", "help me review PR #123", "guide me
  through reviewing this branch/diff", or wants a structured, paced review
  companion rather than a prose summary.
argument-hint: [pr-number | branch | "working"]
user-invocable: true
---

# PR Walkthrough

Turn a diff into one self-contained HTML page of numbered, progress-tracked
review stops — **ordered by trust, not by filename**. Start where untrusted
input lands and follow the call graph down, so each function is understood
before the ones it calls. This is a review *companion* the reviewer ticks off;
explaining what changed is `pr-visualizer`.

## 1. Get the diff

- **PR**: `gh pr view <n> --json title,body,headRefName,baseRefName,files,additions,deletions` + `gh pr diff <n>` (`--name-only` first for large diffs, then read in sections).
- **Branch**: `git diff <base>...<head>` / `--stat`. **Working tree**: `git diff` + `git status`.

If the source is ambiguous, ask one short question, then proceed.

## 2. Map the review order (the real work)

Read the whole diff and open the key changed files — never build from the
title/description alone. Then:

1. **Find the roots** — entry points / trust boundaries in the changed set:
   HTTP route handlers, worker/cron jobs, queue/event consumers, CLI commands,
   webhooks, public API/SDK methods, auth/permission checks.
2. **Trace each down its call graph** (handler → service → domain/db). Note
   unchanged callees only where they matter for correctness.
3. **Order stops** per entry point, shallow → deep, with depth labels
   (`boundary`, `→ service`, `→→ domain`).
4. **Flag the key change** — the one stop where behavior actually shifts. It
   gets the `crit` card variant and a short "why it matters".
5. **Batch the trivial** — renames, formatting, generated files go to the skim
   section, not the walk.

Each stop, extracted from the diff (never invented — if unsure what a change
does, read the code):

- **Location** — `file:line` + depth, linked to the exact GitHub line (below).
- **The change** — the stop's **complete diff hunk(s), verbatim** (with `@@`
  headers when a stop spans several hunks). You may add a short pseudo-code
  summary (`.pseudo` block) above the diff to orient the reader, but it
  accompanies the diff — never replaces or truncates it. Long hunks scroll
  inside the diff box.
- **Why it matters** — the behavioral effect, not a restatement of the code.
- **What to check** — questions the reviewer must answer (not assertions), each
  tagged by trust concern: `input` (untrusted input validated?), `authz`
  (permission enforced at the boundary?), `edge` (error/empty/oversized path
  handled?), `logic` (invariant held? idempotent?).

Scale to the PR: a 3-file fix is 3 stops and no map; a 40-file PR groups stops
under several entry points.

### GitHub links

Build the base once, then append each stop's path + line:

```bash
gh pr view <n> --json url,number,headRefOid,headRepositoryOwner,headRepository \
  --jq '{owner:.headRepositoryOwner.login, repo:.headRepository.name, sha:.headRefOid, url}'
```

- **Per-line** (stop locations, entry-point titles):
  `https://github.com/<owner>/<repo>/blob/<headRefOid>/<path>#L<line>`.
  Use the head **sha**, not the branch name (survives force-pushes); line
  numbers are **new-side**; the head repo differs from base on fork PRs —
  that's why the query pulls `headRepositoryOwner`/`headRepository`.
- **PR-level** (hero chip, footer, skim "diff" links):
  `https://github.com/<owner>/<repo>/pull/<n>` (or `/pull/<n>/files`).
- **No PR** (branch/working tree): derive owner/repo from
  `git remote get-url origin`, use the current commit sha, drop PR-level links.

## 3. Build from the template

Copy `assets/template.html` (next to this skill) to the output path. It ships
the design system, trust-flow SVG map, stop cards, and progress JS (checkboxes
persist to `localStorage`, keyed by `<body data-pr="...">` — set it to the PR
number/branch). The `<!-- COMPONENTS LIBRARY -->` block at the bottom is a
copy-paste library — trust-flow map, entry-point heading, stop card (plain and
`crit`), skim batch, final checks — fill `<main>` with your sections.

- **Trust-flow map**: entry points inside the dashed boundary on the left;
  arrows flow right/down into logic and data. Every node/edge must map to a
  real module/call in the diff. Hover-to-isolate is auto-wired for any
  `<svg class="depgraph">`.
- **Map → stop navigation**: give every map node a
  `data-target="<element-id>"` pointing at the `id` of its review section —
  the `.epgroup` for entry-point nodes, the `.stop` card (`id="stop-N"`) for
  logic/data nodes. Clicking a node then scrolls to that section and flashes
  it (auto-wired). Every node must resolve to a real id; no dead targets.
  Nodes targeting a stop id also show a live ✓/⚑ badge mirroring the
  reviewer's progress — prefer stop ids as targets where sensible.
- **Flags, notes, review export** (auto — don't author, don't remove): flag ⚑
  and note ✎ controls are injected into every stop by the template JS; the
  final-checks component's `#flagged` list and `#copyreview` button must be
  included verbatim — they collect the reviewer's flags/notes and copy them
  as a markdown review draft.
- **Plain language**: write all page copy in plain, direct English that an
  international audience gets instantly. Say "key change", not "linchpin";
  "final checks", not "closeout". No rare idioms, wordplay, or clever labels —
  a reviewer should never have to decode the walkthrough's own vocabulary.
- **Complete diffs**: every stop card includes its `.diff` block with the full
  hunk(s) from step 2 — a stop without its actual diff is incomplete.
- Replace every `OWNER`/`REPO`/`HEADSHA`/`N` placeholder with the step-2 URLs —
  every `<a class="loc">`, entry-point title, PR chip, and footer. No dead URLs.
- Keep it **100% self-contained** — no CDNs, fonts, or external scripts/images;
  it must open offline.

## 4. Output & open

Write `pr-<n>-walkthrough.html` (or `<branch>-walkthrough.html`) to the repo
root or `./local/` — confirm if unsure. Then `open <file>` (macOS) /
`xdg-open` (Linux) and tell the user the path.

## Anti-patterns

- ❌ Ordering stops by filename — the call graph is the path; group stops under
  their entry point, boundary first.
- ❌ Building from the PR title/description without reading the diff.
- ❌ Stops that restate the code instead of posing a tagged review question.
- ❌ Summarizing or pseudo-coding a change *instead of* showing its diff —
  pseudo-code may sit above the hunk, never in place of it.
- ❌ Map nodes/edges that don't correspond to real calls in the diff, or nodes
  without a `data-target` that resolves to a stop/entry-point id.
- ❌ Invented edge cases, tests, or metrics not traceable to the diff or a file
  you opened.
- ❌ External dependencies (Mermaid/CDN/fonts) — breaks offline.
- ❌ Obscure or idiomatic terms in page copy — "linchpin", "crux",
  "closeout", "bikeshed". Use plain words: "key change", "final checks".
