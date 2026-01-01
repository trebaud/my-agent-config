---
name: gha-audit
description: Audit GitHub Actions workflows for security issues — dangerous triggers, script injection, unpinned actions, over-permissioned tokens, secret leaks, unsafe self-hosted runners. Use when the user asks to audit/review/scan GitHub workflows, `.github/workflows`, CI security, pipeline security, or GitHub Actions hardening.
tools: Bash, Read, Grep, Glob, Agent
metadata:
  version: 1.0.0
---

# GitHub Actions Audit

Scan `.github/workflows/` for known security weaknesses. Triage each by exploitability before reporting, and include a remediation for every finding.

## Parameters

- **`<file-or-dir>`** — audit only this path (default: `.github/workflows/`)
- **`--severity <level>`** — report at this level and above: `low`, `medium`, `high`, `critical` (default: `medium`)
- **`--fix`** — propose edits for auto-fixable issues (SHA pinning, `persist-credentials: false`, `permissions:` scoping). Still requires review.

## Workflow

### Step 1: Discover workflows

```bash
find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) 2>/dev/null
```

Also check reusable/composite actions:
```bash
find . -path '*/.github/actions/*' -name 'action.y*ml' 2>/dev/null
```

If none found, stop and tell the user.

### Step 2: Run checks

Apply every check in [references/checks.md](references/checks.md) to every workflow file. Checks are grouped by category and each one specifies its detection pattern, severity, and remediation.

For large repos (>20 workflows), parallelize with one Agent per category using `subagent_type: general-purpose`. Each agent loads `references/checks.md`, runs its category's checks across all workflows, and returns findings in the structured format below.

### Step 3: Triage exploitability

Treat every pattern match as a candidate to confirm. Before reporting, assess:

- Trust boundary: does untrusted input reach this code path? (fork PRs, issues, comments, external webhooks)
- Privilege: does the job have access to secrets or write permissions when the risky code runs?
- Reachability: is the vulnerable step actually executed on the dangerous trigger?

Downgrade severity when the pattern is present but not reachable by an attacker. For example, `pull_request_target` with no checkout of PR head, or script injection in a workflow that only runs on `push` from protected branches.

### Step 4: Report

One table, sorted by severity:

```markdown
| File | Line | Severity | Check | Finding | Fix |
|------|------|----------|-------|---------|-----|
| release.yml | 14 | CRITICAL | pwn-request | pull_request_target checks out PR head and runs `npm test` | Switch to pull_request, or gate on approved-label |
| ci.yml | 8 | HIGH | script-injection | `${{ github.event.issue.title }}` interpolated into `run:` | Bind to env var and quote: `"$ISSUE_TITLE"` |
| ci.yml | 22 | MEDIUM | unpinned-action | `actions/setup-node@v4` uses tag | Pin to 40-char SHA + version comment |
```

Then a short summary: count per severity, top 3 issues by impact, and next steps.

### Step 5 (optional): Fix

With `--fix`, apply only these auto-fixes (each as a separate edit):

- Tag → SHA pinning (resolve via `gh api repos/<owner>/<repo>/commits/<tag> --jq .sha`)
- Add `permissions: {}` at workflow level if missing
- Add `persist-credentials: false` to `actions/checkout` when artifacts are uploaded
- Replace `${{ ... }}` interpolation in `run:` with env-var binding

Everything else (trigger changes, OIDC migration, runner isolation) needs a human to design the fix. Report those, don't attempt them.

## Checks summary

Full patterns and examples live in [references/checks.md](references/checks.md). The categories:

| Category | Severity ceiling | Key checks |
|----------|------------------|------------|
| Dangerous triggers | CRITICAL | `pull_request_target` + PR checkout; `workflow_run` artifact poisoning; `issue_comment` privileged execution |
| Script injection | HIGH | `${{ github.event.* }}` / `github.head_ref` in `run:`; unsafe writes to `$GITHUB_ENV`, `$GITHUB_PATH` |
| Supply chain | HIGH | Unpinned actions (tag/branch); third-party actions without SHA; missing cooldown on new versions |
| Permissions | HIGH | Missing top-level `permissions:`; `write-all`; `secrets: inherit` in reusable workflows; `toJson(secrets)` |
| Credentials & secrets | MEDIUM | `persist-credentials: true` + artifact upload; long-lived cloud keys instead of OIDC; broad artifact paths |
| Runners | HIGH | Self-hosted runner on public repo; non-ephemeral runners; runner groups not restricted |
| Repo/org config | MEDIUM | Actions allowed to create/approve PRs; default token not read-only; no CODEOWNERS on `.github/workflows` |

## Anti-patterns

- Don't flag every `${{ github.* }}` as injection. Only attacker-controlled fields (`event.issue.*`, `event.pull_request.*`, `head_ref`, `event.comment.*`, etc.) matter. See the allow/deny list in checks.md.
- Don't require SHA pinning for first-party actions (`actions/*`, `github/*`) at CRITICAL; it's noise. Pin them at HIGH or below depending on blast radius.
- Don't report without confirming reachability. A dangerous trigger with no privileged steps is not exploitable.
- Don't auto-fix trigger changes. Moving from `pull_request_target` to `pull_request` changes behavior and needs a human.

## Examples

```
/gha-audit                              # audit .github/workflows at medium+
/gha-audit --severity high              # only HIGH and CRITICAL
/gha-audit .github/workflows/release.yml
/gha-audit --fix                        # apply safe fixes, report the rest
```
