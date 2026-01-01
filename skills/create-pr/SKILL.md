---
name: create-pr
description: Create a pull request from the current branch using project conventions. Use when the user asks to create a PR, open a pull request, submit changes for review, push and create a PR, or says /create-pr. Keywords: pull request, PR, merge request, code review, gh pr create.
license: Apache-2.0
metadata:
  version: 1.0.0
allowed-tools: Bash Read Glob Grep
---

# Create Pull Request

Create a pull request from the current branch using project conventions.

## Instructions

### Step 1: Gather Context

Run in parallel:

```bash
git branch --show-current
git status -sb
git branch | grep -E 'main|master'
```

Store the detected default branch as `{base}`. If the current branch IS `{base}`, stop — user needs a feature branch.

Then get branch history:

```bash
git log {base}..HEAD --oneline
git diff {base}...HEAD --stat
```

### Step 2: Handle Uncommitted Changes

If there are staged or unstaged changes, ask the user whether to commit, stash, or abort. Never silently commit or discard.

### Step 3: Title

Use conventional commit format: `<type>(<scope>): <description>` (under 70 chars).

Derive **type** from branch prefix (`feat/` → `feat`, `fix/` or `hotfix/` or `security/` → `fix`, `deps/` → `chore(deps)`, etc). No prefix → derive from commits.

Derive **scope** from changed files (e.g., `api`, `auth`, `ui`). Derive **description** from commits and diff.

### Step 4: Body

Check for a repo template first:

```bash
cat .github/pull_request_template.md 2>/dev/null || \
cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || \
cat .github/PULL_REQUEST_TEMPLATE/pull_request_template.md 2>/dev/null || \
echo "NO_TEMPLATE"
```

If a template exists, fill it in exactly. Otherwise use:

```markdown
## Summary
<!-- 1-3 bullets: what changed and why -->

## Changes
<!-- Specific changes, grouped by area if needed -->
```

Read the full diff (`git diff {base}...HEAD`) to write an accurate body.

**Writing style**: Concise, information-dense, no filler. State what changed and why — skip what's obvious from the diff. Use precise technical language ("adds retry with exponential backoff to S3 uploads" not "improves reliability"). No "this PR does..." preamble. Every sentence must carry new information.

**IMPORTANT**: No mention of AI, agents, or automated generation anywhere in the PR body.

### Step 5: Push and Create

```bash
git push -u origin $(git branch --show-current)
gh pr create --base {base} -a "@me" --title "{title}" --body "$(cat <<'EOF'
{body}
EOF
)"
```

Output the PR URL when done.

### Error Handling

- **On `{base}` branch**: Stop, tell user to create a feature branch.
- **PR already exists**: `gh pr view` to show it, ask if they want to update.
- **Push rejected**: Suggest `git pull --rebase` and retry.
- **No `gh` or auth failure**: Suggest `gh auth login` or provide manual steps.
- **Merge conflicts with base**: Warn and suggest rebasing first.
