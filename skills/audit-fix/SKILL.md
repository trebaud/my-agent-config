---
name: audit-fix
description: Audit prod dependencies and fix vulnerabilities by tracing to root parents, using recursive updates, parent bumps, or replacements
tools: Bash, Read, Grep, Glob, WebSearch, WebFetch, Agent
metadata:
  version: 1.2.0
---

# Audit Fix

Run `pnpm audit`, trace each vulnerability to its root parent, select a fix strategy, and apply fixes in parallel subagents.

## Commit Discipline (applies throughout)

Commit after **every** dependency bump, update, replacement, or risk-acceptance decision — one logical change per commit. Never batch multiple package changes into a single commit, even if they look related.

A commit is required after each of these:

- A successful `pnpm update <pkg> --recursive` (Strategy A)
- A `package.json` version edit + `pnpm install` (Strategy B/C)
- A dependency replacement (Strategy D) — separate commits for (a) adding the replacement and rewriting imports, (b) removing the deprecated package
- A `pnpm-workspace.yaml` `auditConfig.ignoreGhsas` addition (Strategy E)
- A `pnpm.overrides` addition after user approval (Strategy F)
- Any decision recorded as a config/comment change (e.g. revisit notes)

Why: each commit is a reversible step. If a later change breaks the build, `git bisect` or `git revert` lands on exactly the dependency that caused it. Squashing hides which bump introduced the regression.

Stage only the files touched by that single change (`git add <specific paths>`, never `git add -A`). Use the commit message form:

```
fix(audit): bump <pkg> to <version> (<CVE/GHSA ids>)
fix(audit): replace <old-pkg> with <new-pkg> (<CVE/GHSA ids>)
chore(audit): ignore <GHSA-id> — <one-line reason>
```

## Parameters

- **`<package-name>`** — only fix vulnerabilities for this package
- **`--level <severity>`** — fix all at this level and above (`low`, `moderate`, `high`, `critical`)
- **No args** — defaults to `--level critical`

## Workflow

### Step 0: Branch Check

Before making any changes, check the current branch:

```bash
git branch --show-current
```

If on `master` or `main`, create a new branch:

```bash
git checkout -b audit-fix-<short-descriptor>
```

Use a descriptor that reflects the scope (e.g. `audit-fix-critical`, `audit-fix-pbkdf2`).

### Step 1: Audit and Parse

```bash
pnpm audit --audit-level <level> --prod
```

For each vulnerability, extract: package, fix version, and full dependency path. If a specific package was passed, filter to that package only. Stop if no vulnerabilities found.

### Step 2: Group by Root Parent

The root parent is the first dep in the path (the direct dependency in package.json). Multiple CVEs from the same root parent are handled together.

### Step 3: Select Strategy Per Root Parent

For each root parent, check these in order — use the first that applies:

| Strategy | Condition | Check with |
|----------|-----------|------------|
| **A: Recursive update** | Parent's semver range allows the fix version | `pnpm view <parent>@<version> dependencies` |
| **B: Minor/patch bump** | Newer minor/patch of parent exists | `pnpm view <parent> version` |
| **C: Major bump** | Only a major bump fixes it | `pnpm view <parent> version` — **web search for breaking changes** |
| **D: Replace dep** | Parent is deprecated/abandoned | `pnpm view <parent>` deprecation notice, check for alternatives in package.json |
| **E: Accept risk** | No fix available, not exploitable | Exploitability analysis + add to `auditConfig.ignoreGhsas` (see [workflow reference](references/upgrade-workflow.md#strategy-e)) |
| **F: Override (last resort)** | A–E impossible AND vuln is exploitable | **Stop and ask the user before proceeding** (see Hard Rule below) |

#### Hard Rule: never add `pnpm.overrides` without explicit user approval

`pnpm.overrides` (in `package.json` or `pnpm-workspace.yaml`) is **last resort only**. Overrides bypass semver intent and pin us to versions the parent never declared support for, which masks upstream maintenance gaps.

Before adding **any** override entry you MUST:

1. Confirm strategies A–E are all genuinely impossible — document why each was rejected.
2. Stop and ask the user explicitly: name the override, the parent, the resolved version, and the reason A–E don't apply. Wait for confirmation.
3. If the user approves, scope the override as narrowly as possible (`parent>child` form, never bare package name) and add a comment explaining the rationale and revisit trigger.

If the vuln is **not** exploitable, prefer Strategy E (`auditConfig.ignoreGhsas`) over an override — the audit allow-list documents intent without changing what code runs.

### Step 4: Launch Subagents

One Agent per root parent, all in parallel. Each subagent commits **after every individual change** it makes (see Commit Discipline above) — not just one summary commit at the end.

```
Agent tool:
  subagent_type: "general-purpose"
  description: "Fix <root-parent> audit vulns"
  prompt: |
    Fix audit vulnerabilities for <root-parent>.
    Strategy: <A/B/C/D/E>
    Vulnerabilities: <CVE list with fix versions>
    Dependency chain: <full path>
    Read and follow: .claude/skills/audit-fix/references/upgrade-workflow.md

    Commit after EACH change, not at the end:
      - one commit per bump, update, replacement, or ignoreGhsas entry
      - stage only the files touched by that single change
      - never `git add -A` (parallel subagents share the working tree)
      - commit message: fix(audit): bump <pkg> to <version> (<CVE ids>)

    If Strategy E (accept risk) is chosen, the ignoreGhsas edit is itself a
    commit: chore(audit): ignore <GHSA-id> — <one-line reason>.

    Do NOT stage changes made by other parallel subagents.
```

Because subagents run in parallel on the same working tree, each subagent must stage only its own changed paths (explicit file list to `git add`). If two subagents would touch `pnpm-lock.yaml` simultaneously, serialize via a lockfile check or run those root parents sequentially.

### Step 5: Verify and Report

```bash
pnpm audit --audit-level <level> --prod
```

Report as:

```markdown
| Root Parent | CVEs | Strategy | Result |
|-------------|------|----------|--------|
| soap | 2 | A: Recursive update | FIXED |
| request | 2 | E: Accept risk | NOT EXPLOITABLE |
```

Include exploitability analysis for any remaining vulnerabilities.

## Anti-Patterns

- **Don't delete the lockfile** — use `pnpm update <pkg> --recursive` instead
- **Don't add `pnpm.overrides` without user approval** — see the Hard Rule above. Overrides bypass semver intent and are last-resort only
- **Don't do risky major bumps** for non-exploitable CVEs — prefer Strategy E (audit ignore) for non-exploitable findings
- **Don't write a separate doc/markdown for accepted risks** — keep the rationale as comments next to the GHSA list in `pnpm-workspace.yaml`'s `auditConfig.ignoreGhsas` so it lives with the config

## Example

```
/audit-fix                        # Fix all critical prod vulnerabilities
/audit-fix --level high           # Fix high and critical
/audit-fix pbkdf2                 # Fix only pbkdf2 vulnerabilities
```
