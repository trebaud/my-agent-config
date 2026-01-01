# Report Format

How findings produced by the vuln-feed-scan workflow are formatted — both the on-screen report (workflow step 6) and the saved markdown/HTML files (workflow step 7).

The report is the only thing the user reads. Format it for scanning, with plenty of whitespace between findings.

## On-screen report

### Ranked table

Most urgent first. One row per finding:

```
| # | Severity | CVE / Name | Affects | In your repos | Published | Action |
```

- `#` is a 1-based index matching the detail blocks below, so the user can jump between them.
- Severity: Critical / High only. Anything lower does not belong in the report.
- Affects: the specific stack item it hits (e.g. "npm: express@<4.20.0", "AWS IAM", "MongoDB driver").
- In your repos: the shortest possible hit summary (e.g. "app@1.2.3, api@2.0.1" or "no match"). If multiple repos hit, list them comma-separated; if too many to fit, write "N repos — see detail".
- Action: concrete next step in ≤12 words pinned to a specific file path when possible (e.g. "Pin protobufjs ≥7.5.5 in backend/package.json", "Rotate AWS keys issued before YYYY-MM-DD").

### Detail blocks

After the table, one block per finding in the same order. Separate blocks with a horizontal rule (`---`) so each finding is visually distinct. Use this structure, keeping each bullet on its own line:

```
### {index}. {CVE / Name} — {Severity}

- **Affects:** {specific stack item(s)}
- **In your repos:** {concrete hits from step 5, with file paths and resolved versions; or `No direct or transitive match found in <N> repos checked.`}
- **Published:** {date, or `date?`}
- **Source:** [{primary source name}]({url}) · [{secondary, if any}]({url})

**What it is.** One sentence describing the vulnerability in plain terms.

**Why it matters here.** One sentence tying it to the resolved stack — which service, which dep, which blast radius. Reference the specific repo(s) that hit from the `In your repos` line.

**Attacker capability.** One sentence on what exploitation gets them (RCE, data exfil, token theft, etc.).

**Action.** The same concrete next step from the table, expanded to one sentence if useful.

**Local evidence.**
```{language}
$ {exact read-only command that was run}
{verbatim trimmed output}
```
```

Rules for the detail blocks:

- Never merge the four labeled paragraphs into one run-on line. Each gets its own line with a blank line before and after.
- No padding sentences, no "it is important to note that", no best-practice lectures. If a section would be empty or obvious, drop it.
- Every CVE/incident name in both the table and the detail heading is a markdown hyperlink to its primary source.
- The `In your repos` line is mandatory. If step 5 found nothing, say so explicitly with the repo count — never omit the line.
- The `Local evidence` fenced block is mandatory whenever step 5 returned any output for this finding (hit or no-hit). Use a `$ ` prompt prefix for each command and follow it with the verbatim trimmed output. Cap at ~20 lines per finding; if more, show the most diagnostic 20 and end with `# {N} more lines elided`. For no-hit findings, show the command that returned empty (so the reader knows the check actually ran).

### Suggested next commands

A single fenced `bash` block listing *remediation* commands — things the skill deliberately did **not** run because they mutate state, install packages, hit the network, or affect production (e.g. `pnpm install`, `pnpm.overrides` edits, `gh auth refresh`, AWS key rotation). The read-only investigation commands already ran in step 5 and their output lives in each finding's `Local evidence` block — do not duplicate them here. One command per line, with a `# {finding index}: {short intent}` comment above each. When step 5 found a hit, target the exact repo path (e.g. `(cd backend && pnpm install)`), not a generic placeholder.

### Also worth a glance

A final section titled `## Also worth a glance` listing items that did not clear the score ≥ 7 bar but could still be interesting: tangential to the resolved stack, partially corroborated, or a slow-burn supply-chain story that may matter later. Also include items moved here by step 5e (relevant on paper, but no local usage). One line per item, up to 8 items total:

```
- [{CVE / Name}]({url}) — {≤15 words on what it is and why it's borderline} _(score {n}, {reason it was down-ranked})_
```

Pull candidates from items dropped in step 3c / 4 for score reasons only, plus items moved here by step 5e. Do not include items hard-dropped by the 3b stack pre-filter (ecosystems outside the resolved stack, desktop software, ICS, etc.); those are noise. If nothing qualifies, omit the section entirely; do not emit an empty header.

### Empty report

If nothing survives step 4 and nothing qualifies for "Also worth a glance", say exactly: `No high-signal threats in window. Next scan recommended in 12h.` with no table or detail blocks. If the main report is empty but "Also worth a glance" has items, keep that section and prepend a single line: `No items cleared the high-signal bar, but these may be worth a glance:`.

## Saved markdown file

Path: `./YYYY-MM-DD_HH-MM-SS_vuln-scan.md`

- Content: the report as shown to the user (ranked table, In-your-repos column, detail blocks **including the `Local evidence` fenced block for every finding where step 5 captured output**, suggested remediation commands, also-worth-a-glance section).
- Every CVE / incident name in the table must be a markdown hyperlink to its primary source. Do not omit links.
- Header line: `# Vuln Scan — YYYY-MM-DD HH:MM:SS UTC` (same timestamp, spaces/colons for readability).
- Metadata line directly under the header, before the table: `**Window:** Xd | **Stack:** {resolved stack filter, slash-separated} | **Repos checked:** {comma-separated list from step 5a}`.
- Example header: `# Vuln Scan — 2026-04-20 14:07:33 UTC`.

## Saved HTML file

Path: `./YYYY-MM-DD_HH-MM-SS_vuln-scan.html`

Write a single self-contained HTML file with:

- Inline CSS only (no external dependencies)
- Dark background (`#0d1117`), GitHub-like aesthetic
- Clean sans-serif font (system-ui stack)
- A sticky header with scan title, timestamp, window, stack, and repos-checked metadata
- The ranked summary table rendered as an HTML `<table>` with hover rows and severity badges, including the `In your repos` column
- Severity badge colors:
  - Critical: red (`#da3633` bg, `#ffc1be` text)
  - High: orange (`#9e4a01` bg, `#ffa657` text)
- Detail blocks as styled `<article>` elements, each separated visually, containing:
  - `<h3>` heading with CVE/name linking to primary source
  - Labeled rows for `Affects`, `In your repos`, `Published`, `Sources`
  - Labeled paragraphs (**What it is**, **Why it matters here**, **Attacker capability**, **Action**) each in its own `<p>`
  - A **`Local evidence`** `<pre><code>` block rendering the verbatim command + output captured in step 5; styled like a terminal (slightly inset, mono font, `$` prompt prefix highlighted)
  - Source links as `<a>` tags
- Suggested remediation commands in a styled `<pre><code>` block with a dark inset background (these are the workflow-step-6 remediation commands, not the already-run investigation ones)
- "Also worth a glance" as a final `<section>` with a muted header and list items, if any findings qualify; omit entirely if none
- Smooth hover transitions on table rows and article cards
- Responsive layout (max-width 960px, centered)
- The HTML file must be fully self-contained (no external CSS/JS/fonts)
