---
name: repo-visualizer
description: >-
  Generates a polished, self-contained HTML page that explains an entire repository/codebase so a human can
  understand it at a glance — with hand-built interactive SVG graphs (a hover-to-isolate module/service
  dependency graph, a swimlane sequence diagram of a key end-to-end flow, a top-down decision/control-flow
  chart), a directory-tree map, flow diagrams of the main runtime paths, colour-coded module cards (entry /
  core / infra / config), a data-model/schema view, an external-integrations map, a conventions/patterns
  section, a domain glossary, and an "where to start" onboarding checklist. The output is one dependency-free
  .html file with embedded CSS/JS (no Mermaid/CDN), sticky scroll-spy nav, and a responsive layout. Use
  whenever the user wants to visualize, map, illustrate, document, or explain a whole codebase as a shareable
  web page rather than prose. Triggers: "visualize this repo", "map this codebase", "make an HTML page
  explaining how this project works", "create an architecture overview of the repo", "onboard me to this
  codebase visually", "turn this repository into a webpage/diagram", "show me how this system is structured".
---

# Repo Visualizer

Turn a whole repository into a single, beautiful, self-contained HTML page that makes the codebase easy to
understand. The result is a teaching artifact — it should answer "what is this, how is it structured, how
does it run, and where do I start?" faster than reading the source.

This is the codebase-scale sibling of `pr-visualizer`: same design system and component library, but the
subject is the *system as it stands* rather than a diff.

## Inputs (figure out which one applies)

- **The current working directory** — the default. "Visualize this repo / map this codebase."
- **A specific subdirectory or service** — e.g. "explain the `packages/api` service." Scope to that tree.
- **A remote repo** — a GitHub URL or `org/repo`. Clone it (or use `gh repo clone`) into a temp dir first,
  then proceed. Confirm before cloning anything large.

If the source or scope is ambiguous (whole monorepo vs one service), ask one short question before proceeding.

## Workflow

### 1. Gather the lay of the land
- **Top-level layout:** `git ls-files | head -300`, then `ls` key dirs. Find the real source roots (skip
  `node_modules`, `dist`, `vendor`, `.git`, build artifacts).
- **Project metadata:** read `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `pom.xml` etc.
  for name, language, frameworks, scripts, and key dependencies. Read the `README` and any `docs/`, `CLAUDE.md`,
  or ADRs for stated purpose and conventions.
- **Size & shape:** `git ls-files | wc -l`, language breakdown (e.g. `git ls-files | sed 's/.*\.//' | sort |
  uniq -c | sort -rn | head`), and the few biggest/most-central files.
- **Entry points:** `main`/`index`/`server`/`cli`/`cmd` files, `bin` entries in package metadata, framework
  bootstrap files, worker/cron entry points, Dockerfile `CMD`.

### 2. Understand it (this is the real work)
Read enough source to be accurate — **do not infer architecture from the directory names alone.** Open the
entry points and trace the 1–3 most important runtime paths. Extract (never invent):
- **One-line purpose** and the scope (what the system does; what's in / out of this page).
- **The architecture** — the real modules/services/layers and how they depend on each other (who calls whom,
  who reads/writes what). This becomes the dependency graph — the centerpiece.
- **The main flow(s)** — the primary runtime path(s): e.g. request → router → controller → service → db; or
  event → queue → worker → side effect; or CLI invocation → command → output. These become flow + sequence diagrams.
- **The data model** — the core entities/tables/types and their relationships.
- **Entry points & boundaries** — where execution starts, and where the system talks to the outside world
  (DBs, queues, third-party APIs, caches, file system).
- **The linchpin** — the one module a newcomer must understand first. Flag it amber.
- **Conventions & patterns** — layering rules, naming, error handling, how features are added, test strategy.
- **Domain vocabulary** — terms that are obvious to insiders but opaque to newcomers.

### 3. Pick the sections
Use only the sections that fit the codebase — a small library might be hero + layout + modules + start; a
large service uses most of them. Catalog (all optional, reorder freely):
1. **Hero** — repo name, one-line lede, at-a-glance chips (language, framework, ~LOC, # services/modules).
2. **At a glance / tech stack** — cards for stack, scale, entry points, how to run.
3. **Directory map** — a tree of the top-level layout with a one-line role for each significant dir.
4. **Architecture / dependency graph** *(SVG, interactive)* — node-link map of the real modules/services with
   typed edges (solid=calls, dotted=writes, dashed=reads) and animated "packets" on hot paths. **Hover a node
   to isolate its dependencies** (the template JS handles it). This is the headline diagram — invest here.
5. **Main flow diagram(s)** — horizontal node→arrow→node steps for the primary runtime path(s) (CSS, no SVG).
6. **Sequence diagram** *(SVG, swimlanes)* — lifelines per participant for one key end-to-end flow (e.g. an
   API request, a job run), time flowing downward, returns dashed, invariants as inline bands.
7. **Decision / control-flow chart** *(SVG, top-down)* — process boxes + diamond decisions for an important
   piece of branching logic (auth gate, routing, state machine).
8. **Data / schema** — annotated core models / tables / key types and their relationships.
9. **Key modules** — colour-coded cards: green = entry point, cyan = core/domain, violet = infra/adapter,
   amber = linchpin. Path in monospace, one line on its responsibility.
10. **External integrations** — cards or a small graph for DBs, queues, third-party APIs, caches.
11. **Conventions & patterns** — how the code is organized and how to extend it.
12. **Glossary** — domain terms a newcomer needs.
13. **Where to start** — an onboarding checklist: the files to read first, in order, and how to run/test.
14. **Footer** — provenance (repo name, commit SHA, generated date, scope).

**Reach for the dependency graph (#4) on any non-trivial repo** — a hovered module graph teaches structure
far faster than prose. Add a sequence diagram (#6) when there's a clear end-to-end flow. Keep every node/edge
factual: it must map to a real module/import/call in the source.

### 4. Build from the template
- Copy `assets/template.html` (next to this skill) to the output path. It already contains the full CSS
  design system, sticky scroll-spy nav, the hover-to-isolate graph JS, and the toggle JS.
- The template's `<!-- COMPONENTS ... -->` comment block is a copy-paste library for every section type —
  directory tree, **dependency graph**, **sequence diagram**, **decision flowchart**, flow node, module card,
  integration card, schema, glossary item, checklist, callout, toggle. Fill the `<main>` with the sections
  you chose, wiring each section's `id` to a nav link.
- **SVG graphs:** copy the snippet, then edit node labels and coordinates to match the real codebase. Wrap
  each in `.gwrap`. For the dependency graph, give the `<svg>` `class="depgraph"` and tag nodes
  `<g class="gnode" data-id="X">` / edges `<g class="gedge" data-from="X" data-to="Y">` — the template JS
  wires hover-to-isolate automatically. Add `<path class="pkt" pathLength="100">` over an edge for an animated
  packet. All graphs are hand-built inline SVG — **never** pull in Mermaid or any CDN.
- Keep it **100% self-contained** — no CDNs, no external fonts/scripts/images. It must open offline.

### 5. Output & open
- Default output path: the repo root (or a `./local/` dir) as `<repo-name>-overview.html`. For a remote clone,
  write it next to where you'd want it kept, not inside the temp clone. Confirm the path with the user if unsure.
- `open <file>` (macOS) / `xdg-open` (Linux) to launch it, then tell the user the path.

## Quality bar

- **Factual** — every node, module card, integration, and claim must trace to real source. If you're unsure
  what a module does, read it; don't guess. No invented dependencies, metrics, or fake LOC numbers.
- **The graph is the hook** — a hovered dependency graph that maps the real modules is the highest-value
  element on the page. Invest in getting its nodes, edges, and layout right.
- **Flag the linchpin** — one module, marked amber, with a short "start here / why it matters". Newcomers
  should know where to look first.
- **Scale to the repo** — don't pad a tiny library with empty sections; don't cram a 500-file monorepo into
  one graph. For large repos, visualize at the module/service level and link out, not the file level.
- **Built for onboarding** — the implicit reader is a developer seeing this codebase for the first time. The
  "where to start" section and the linchpin flag are what make it useful, not exhaustive.
- **Responsive & legible** — flows stack on mobile (the template handles this), text stays readable, dark
  theme by default (offer a light variant only if asked).
- **Accessible-ish** — real headings, sufficient contrast, the nav works by anchor.

## Anti-patterns
- ❌ Generating from the README / directory names without reading the source.
- ❌ External dependencies (Mermaid CDN, Google Fonts, Tailwind CDN, D3) — breaks offline, defeats
  "self-contained". Graphs are hand-built inline SVG from the template snippets, not a rendered library.
- ❌ A dependency graph whose nodes/edges don't map to real modules/imports (a pretty but fictional graph is
  worse than none).
- ❌ A file-by-file dump for a large repo — visualize at the right altitude (modules/services), not every file.
- ❌ A wall of cards with no graph, tree, or flow — the structure is what teaches.
- ❌ Inventing conventions, integrations, or "where to start" steps that aren't grounded in the code.
