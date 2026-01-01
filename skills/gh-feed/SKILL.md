---
name: gh-feed
description: Show a rich feed of the user's active open pull requests across all GitHub repos — links, review status, CI, comments, and latest activity. Use when the user runs /gh-feed or asks to see their open PRs or GitHub PR activity.
allowed-tools: Bash, Write
---

# gh-feed

Display a rich, formatted feed of all open pull requests authored by the user across all GitHub repos. Write the report to both a markdown file and a styled HTML file.

## When to Use

- When the user runs `/gh-feed`
- When the user asks to see their open PRs, PR feed, or GitHub activity

## Steps

### Step 1: Fetch all open PRs

Run both queries in parallel in a single message:

**1a. PRs authored by the user:**
```bash
gh search prs --author "@me" --state open --limit 100 --json number,title,repository,url,createdAt,updatedAt,isDraft
```

If that fails (auth or field error), fall back to the GitHub API:
```bash
gh api "search/issues?q=author:@me+type:pr+state:open&per_page=100"
```

**1b. PRs where the user is a requested reviewer:**
```bash
gh search prs --review-requested "@me" --state open --limit 100 --json number,title,repository,url,createdAt,updatedAt,isDraft
```

If that fails, fall back to:
```bash
gh api "search/issues?q=review-requested:@me+type:pr+state:open&per_page=100"
```

If both fail due to missing auth, tell the user to run `gh auth login`.

Filter results to only `state: open` and skip any with a non-null `merged_at`. Keep the two lists separate — do not merge them.

### Step 2: Fetch PR details in parallel

For every open PR (both authored and review-requested) — **all in a single parallel batch** (one message, multiple Bash tool calls):

```bash
gh pr view <number> --repo <owner/repo> --json number,title,url,state,isDraft,createdAt,updatedAt,headRefName,baseRefName,reviewDecision,reviews,comments,additions,deletions,mergeable,statusCheckRollup
```

Never fetch PRs sequentially. Always batch all calls in parallel.

### Step 3: Build the report content

The report has two independent sections: **My PRs** (authored by the user) and **Review Queue** (PRs where the user was requested as reviewer). Sort each section by `updatedAt` descending and group cards by repo within each section.

#### Summary table (shown once, at the top only, covers My PRs only)

| # | Title | Repo | Branch | Review | CI | Updated |
|---|-------|------|--------|--------|----|---------|
| #N | [title](url) [DRAFT] | owner/repo | head → base | emoji | emoji | relative time |

**Review emoji for table:**
| Decision | Emoji |
|----------|-------|
| APPROVED | ✅ |
| CHANGES_REQUESTED | ❌ |
| REVIEW_REQUIRED | 👀 |
| No reviewers | ⏳ |

**CI emoji for table:**
| State | Emoji |
|-------|-------|
| All passing | ✅ |
| Any failing | ❌ |
| In progress | ⏳ |
| No checks | — |

#### PR detail cards (My PRs)

```
## <owner/repo>

### [#<number> <title>](<url>)  [DRAFT]?
Branch: `<head>` → `<base>` | +<additions> / -<deletions> | Updated <relative time>
Reviews: <reviewer emoji + name list>
CI: <status>
💬 <count> comments · Latest: <author> — "<excerpt truncated to 120 chars>"

---
```

#### Review Queue cards

Same card format as above, but omit the "Reviews" line (since the user IS the reviewer here) and instead show the PR author:

```
## <owner/repo>

### [#<number> <title>](<url>)  [DRAFT]?
Branch: `<head>` → `<base>` | +<additions> / -<deletions> | Updated <relative time>
Author: <author login>
CI: <status>
💬 <count> comments · Latest: <author> — "<excerpt truncated to 120 chars>"

---
```

**Relative time:** compute from today's date (available in context) vs `updatedAt`.
Examples: "just now", "2 hours ago", "3 days ago", "2 weeks ago".

**Comment excerpt:** latest comment body, truncated to 120 characters.

### Step 4: Write output files

Generate a timestamp for the filenames:
```bash
date +%Y%m%d-%H%M%S
```

Use that timestamp in every output filename: `gh-feed-<timestamp>.md` and `gh-feed-<timestamp>.html`.

Write three artifacts. Use the Write tool for all three.

**4a. Markdown file** — `/tmp/gh-feed-<timestamp>.md`

Structure:
```markdown
# PR Feed — <today's date>

## My PRs

<summary table>

---

<grouped PR cards by repo>

---

## Review Queue

<grouped review-queue cards by repo, or "Nothing to review 🎉" if empty>
```

**4b. HTML file** — `/tmp/gh-feed-<timestamp>.html`

Write a single self-contained HTML file with:
- Inline CSS only (no external dependencies)
- Dark background (`#0d1117`), GitHub-like aesthetic
- Clean sans-serif font (system-ui stack)
- A sticky header with title and date
- Two top-level `<section>` elements: **My PRs** and **Review Queue**, each with an `<h2>` heading
- The summary table (My PRs only) rendered as an HTML `<table>` with hover rows and colored badges, inside the My PRs section
- PR cards as styled `<article>` elements grouped under `<section>` headings per repo
- Review Queue cards use the same card style; if the queue is empty, show a centered "Nothing to review 🎉" message
- Status badges for review/CI using colored pill spans:
  - ✅ green (`#238636` bg, `#aff5b4` text)
  - ❌ red (`#da3633` bg, `#ffc1be` text)
  - 👀 yellow (`#9e6a03` bg, `#e3b341` text)
  - ⏳ gray (`#30363d` bg, `#8b949e` text)
  - DRAFT: blue-gray badge (`#1f6feb` outline)
- Branch shown as inline `<code>` elements
- Comment excerpt in a `<blockquote>` styled with a left border
- Additions in green, deletions in red
- Smooth hover transitions on cards and table rows
- Responsive layout (max-width 960px, centered)

After writing the HTML file, run:
```bash
open /tmp/gh-feed-<timestamp>.html
```

**4c. Console output** — render the full feed to the terminal as well (same markdown format as the `.md` file), so the user can read it without opening files.

### Step 5: Report file paths

After writing, tell the user:
- The markdown file path: `/tmp/gh-feed-<timestamp>.md`
- The HTML file path: `/tmp/gh-feed-<timestamp>.html`
- A one-line summary covering both sections (e.g. "7 open PRs — 1 approved and ready to merge · 3 PRs waiting for your review")

## Constraints

- Only show `state: open` PRs — skip merged or closed.
- If a PR has no comments, omit the comments line in the detail card (both MD and HTML).
- If CI has no checks, show `—` in the table and `— none` in the card.
- Keep cards scannable — one per PR, separated by horizontal rules.
- The HTML file must be fully self-contained (no external CSS/JS/fonts).
