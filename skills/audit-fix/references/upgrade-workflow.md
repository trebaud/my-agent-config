# Upgrade Workflow Reference

Execution steps for subagents. Each strategy section is self-contained — read only the one assigned to you.

**Commit rule (applies to every strategy):** commit after every successful change — one bump, update, replacement, or ignoreGhsas entry per commit. Stage only the specific files you edited (`git add package.json pnpm-lock.yaml`, never `-A`). See `SKILL.md` → "Commit Discipline" for message formats.

## Strategy A: Recursive Update

```bash
pnpm update <vulnerable-package> --recursive
pnpm why <vulnerable-package>                    # confirm version >= fix version
pnpm audit --audit-level critical --prod         # confirm CVE resolved
git add pnpm-lock.yaml                           # only the lockfile changed
git commit -m "fix(audit): recursive update <vulnerable-package> to <version> (<CVE ids>)"
```

`--recursive` is required — without it pnpm only updates direct deps, not transitive ones.

## Strategy B: Minor/Patch Parent Bump

```bash
pnpm view <parent> version                       # confirm latest is minor/patch bump
```

Edit package.json to update the parent version, then:

```bash
pnpm install
pnpm why <vulnerable-package>                    # confirm transitive dep updated
pnpm typecheck
git add package.json pnpm-lock.yaml
git commit -m "fix(audit): bump <parent> to <version> (<CVE ids>)"
```

## Strategy C: Major Parent Bump

### 1. Research (mandatory)

```bash
pnpm view <parent> repository.url
```

Web search: `"<parent> breaking changes v<new-major>"` and `"<parent> migration guide"`.

Check: CHANGELOG.md, GitHub releases, migration guides, issues tagged "breaking-change".

### 2. Implement

Find all usages with Grep (`from '<parent>'` and `require('<parent>')`), then:

```bash
# Edit package.json with new major version
pnpm install
# Fix breaking changes per research (edit call sites)
pnpm typecheck
pnpm test <relevant-test-files>
```

Commit as **two** separate commits — the version bump and the call-site migration are different concerns:

```bash
git add package.json pnpm-lock.yaml
git commit -m "fix(audit): bump <parent> to <new-major> (<CVE ids>)"

git add <call-site files>
git commit -m "refactor: migrate <parent> usages to v<new-major> API"
```

If the migration is too complex, try the latest minor/patch of the current major first. If that doesn't fix it, document the finding and recommend the major bump as a separate task.

## Strategy D: Replace Dependency

1. Find all usages with Grep (`from '<parent>'` and `require('<parent>')`)
2. Check if an alternative is already in package.json
3. Map each used function to its equivalent in the replacement
4. Update imports and function calls — `pnpm install && pnpm typecheck && pnpm test <relevant-tests>`
5. Commit the migration (replacement is in place but old dep still listed):

   ```bash
   git add package.json pnpm-lock.yaml <call-site files>
   git commit -m "refactor: replace <old-pkg> usages with <new-pkg>"
   ```

6. Remove deprecated package from package.json — `pnpm install`
7. Commit the removal as its own change:

   ```bash
   git add package.json pnpm-lock.yaml
   git commit -m "fix(audit): remove deprecated <old-pkg> (<CVE ids>)"
   ```

## Strategy E: Accept Risk (Exploitability Analysis)

**All 4 conditions must be met** for a vulnerability to be exploitable:

1. **Attacker-controlled input** — can an external attacker control data flowing into the vulnerable code path?
2. **Dangerous sink reached** — does the codebase actually invoke the vulnerable function? Common false positives: types-only deps (`@types/*`), unused functions, client-only usage
3. **Defenses bypassed** — no input validation, sandboxing, or network restrictions in the way?
4. **Realistic impact** — would exploitation cause meaningful damage?

Report each as:

```markdown
**<CVE-ID>: <vulnerability name>**
- Package: <package>@<version> via <root-parent>
- ① Attacker input: YES/NO — <explanation>
- ② Dangerous sink: YES/NO — <explanation>
- ③ Defenses bypassed: YES/NO — <explanation>
- ④ Realistic impact: YES/NO — <explanation>
- **Verdict: EXPLOITABLE / NOT EXPLOITABLE**
```

### After verdict: silence the audit via `pnpm-workspace.yaml`

If the verdict is **NOT EXPLOITABLE** and there is genuinely no upgrade path (A–D all fail), suppress the advisory in `pnpm-workspace.yaml` so future `pnpm audit` runs stay clean:

```yaml
# at the top level of pnpm-workspace.yaml
auditConfig:
  ignoreGhsas:
    # <root-parent>@<version> pins <vulnerable-pkg>@<vuln-version> exactly.
    # <one-line summary of why it is not exploitable in our call graph>.
    # Revisit if <upstream releases new version | call graph changes | etc.>.
    - GHSA-xxxx-xxxx-xxxx # <vulnerable-pkg> <short advisory description>
    - GHSA-yyyy-yyyy-yyyy # <vulnerable-pkg> <short advisory description>
```

Rules for `ignoreGhsas` entries:

- Put a comment block above each group explaining the package, why no upgrade path exists, why it's not exploitable, and what would force a revisit. The comment IS the audit trail; do not create a separate `SECURITY.md` / acceptance doc.
- Put one advisory per line with an inline `# <pkg> <reason>` comment so `git blame` makes the source obvious.
- Group by root parent: all GHSAs from the same upstream go together, under one comment block.
- Verify with `pnpm audit --audit-level <level> --prod`. The suppressed GHSAs should disappear from the output.
- Commit one accept-risk decision per root parent group, so `git log -- pnpm-workspace.yaml` is a chronological record of accepted risks:

  ```bash
  git add pnpm-workspace.yaml
  git commit -m "chore(audit): ignore <GHSA-id[, GHSA-id]> — <one-line reason>"
  ```

Use `ignoreCves` (instead of `ignoreGhsas`) only if the advisory has a CVE ID but no GHSA; GHSA IDs are preferred since they are what `pnpm audit` prints in `More info` URLs.

### When Strategy E is NOT appropriate

If the verdict is **EXPLOITABLE** and A–D are impossible, do NOT silence the audit. Escalate to the user as a Strategy F (override) candidate — see the Hard Rule in `SKILL.md`. Overrides require explicit user approval before any `package.json` / `pnpm-workspace.yaml` change.

## Subagent Completion Checklist

Before reporting back:

1. `pnpm audit --audit-level <level> --prod` — confirm CVE no longer appears
2. `pnpm typecheck` — no type errors introduced
3. `pnpm test <relevant-tests>` — existing tests pass
4. `git log --oneline <branch-base>..HEAD` — verify each change you made has its own commit (no batched commits)
5. Report: what was done, which strategy succeeded, commit SHAs, any remaining issues
