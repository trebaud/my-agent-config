---
name: releaser
description: >
  Cut a new release of a bun package: bump the version in package.json,
  run typecheck and tests, push the git tag, and create a GitHub release with a
  curated changelog. Does not publish to the registry — that step is left to the
  user. Use when the user says "release", "cut a release", "tag v1.x", or
  "new version".
allowed-tools: Bash
---

# Release a package

Cut a new release of the current npm package: bump version, run gates, tag, and create a GitHub release. Publishing to the registry is **not** part of this skill — the user runs `bun publish` (or equivalent) themselves at the end.

## Arguments

`$ARGUMENTS` may be:
- A full version tag: `v1.2.0` — used as-is, skips version analysis
- A bump keyword: `patch`, `minor`, or `major` — overrides the inferred bump
- Empty — infer the bump level from the changes (see step 1)

## Preflight

Check the workspace is clean and on the right branch:

```bash
git status --porcelain
git rev-parse --abbrev-ref HEAD
```

Refuse to proceed if the working tree is dirty or the branch is not `main` (ask the user to confirm an override). Confirm a package manifest is present:

```bash
test -f package.json
```

If `package.json` is missing, this is not an npm package — stop and surface the mismatch.

## Steps

### 1. Determine the version bump

Get the latest tag, the current package version, and the commits since it:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo "NO_TAG"
node -p "require('./package.json').version"
git log <LATEST_TAG>..HEAD --oneline --no-merges
git diff <LATEST_TAG>..HEAD
```

If there is no previous tag, treat the entire git history as the diff and propose `v0.1.0` (or whatever is in `package.json`) as the initial release.

If `$ARGUMENTS` is a full version tag (starts with `v`), skip this analysis and use it directly.

Otherwise, analyze the commits and diff to classify the bump:

**MAJOR** — any of:
- A commit message contains `BREAKING CHANGE:` or a type with `!` (e.g. `feat!:`, `fix!:`)
- A public API, CLI flag, config key, or exported type was removed or changed incompatibly
- An exported function signature changed in a breaking way

**MINOR** — none of the above, and any of:
- A commit type is `feat:` or similar (new feature added)
- A new CLI command, flag, exported function, or config option was introduced
- New functionality added without breaking existing behavior

**PATCH** — only backwards-compatible fixes, chores, or documentation:
- Commit types: `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`, `test:`, `style:`
- No new features, no breaking changes

If `$ARGUMENTS` is a bump keyword (`patch`, `minor`, `major`), use that instead of the inferred level.

Compute the next version by incrementing the appropriate component of the latest tag (or `package.json` version if no tag exists):
- `major` → bump first number, reset minor and patch to 0
- `minor` → bump second number, reset patch to 0
- `patch` → bump third number

Always prefix the git tag with `v` (e.g. `v1.2.3`). The version inside `package.json` must be the bare semver string (`1.2.3`), without the `v` prefix.

Present the inferred bump level, the reasoning, and the resolved version to the user, then ask for confirmation before proceeding.

### 2. Update package.json and run gates

Update the `version` field in `package.json` to the bare semver (no `v` prefix). Prefer `bun pm version` if available, otherwise edit `package.json` directly:

```bash
bun pm version <SEMVER> --no-git-tag-version 2>/dev/null \
  || (jq ".version = \"<SEMVER>\"" package.json > package.json.tmp && mv package.json.tmp package.json)
```

Verify the change, then run the project's gates so failures surface before any tag is created:

```bash
bun install
bun run typecheck
bun test
```

If any gate fails, stop and report — do not tag.

### 3. Commit the version bump and tag

```bash
git add package.json
git commit -m "release: <VERSION>"
git tag <VERSION>
git push origin HEAD
git push origin <VERSION>
```

Fail loudly if any push is rejected.

### 4. Generate changelog

Get the previous tag (the one before the latest):

```bash
git tag --sort=-version:refname | sed -n '2p'
```

Then collect commits between the previous tag and the new tag:

```bash
git log <PREV_TAG>..<VERSION> --oneline --no-merges
```

If this is the first release, use the full history: `git log --oneline --no-merges`.

Filter and rewrite the commits into concise, user-facing release notes:

- **Include only** changes that affect end users: new features, bug fixes, UX improvements, performance gains visible to users.
- **Exclude** anything that is purely internal: CI/CD, devops, documentation, refactoring, dependency bumps, test changes, chores.
- Prefix each entry with a short type label: `feature:`, `bug:`, `perf:`, `ux:`.
- Keep each entry to one short sentence. Do not copy the raw commit message verbatim — rephrase it to describe what the user experiences.

Format the notes as:

```
## What's Changed

- feature: <what the user can now do>
- bug: <what was broken and is now fixed>
...

**Full changelog**: https://github.com/<OWNER>/<REPO>/compare/<PREV_TAG>...<VERSION>
```

Derive `<OWNER>/<REPO>` from `package.json`'s `repository.url` (or `git remote get-url origin`). If no previous tag exists, omit the compare link.

If no commits pass the user-facing filter, write "No user-facing changes in this release."

### 5. Build cross-platform binaries

Compile standalone executables for each supported platform/arch using `bun build --compile`. The entry point is the package's `bin` target (e.g. `./index.ts` — read it from `package.json` rather than hardcoding).

Create a clean output directory and build all targets:

```bash
rm -rf dist/release
mkdir -p dist/release

ENTRY=$(node -p "let b=require('./package.json').bin; typeof b==='string'?b:Object.values(b)[0]")
NAME=$(node -p "require('./package.json').name")

for TARGET in bun-linux-x64 bun-linux-arm64 bun-darwin-x64 bun-darwin-arm64 bun-windows-x64; do
  EXT=""
  [[ "$TARGET" == bun-windows-* ]] && EXT=".exe"
  OUT="dist/release/${NAME}-<VERSION>-${TARGET#bun-}${EXT}"
  bun build "$ENTRY" --compile --target="$TARGET" --outfile "$OUT" || exit 1
  (cd "$(dirname "$OUT")" && shasum -a 256 "$(basename "$OUT")" > "$(basename "$OUT").sha256")
done
```

If any target fails to build, stop and report — do not create the release.

Each binary gets a sibling `<binary>.sha256` file (one line, `<hash>  <filename>`) that users can verify with `shasum -a 256 -c <binary>.sha256`. Also produce an aggregate manifest for convenience:

```bash
(cd dist/release && shasum -a 256 $(ls | grep -v '\.sha256$\|^SHA256SUMS\.txt$') > SHA256SUMS.txt)
```

### 6. Create the GitHub release

Create the release and attach every artifact in `dist/release/` in a single `gh release create` call:

```bash
gh release create <VERSION> \
  --title "<VERSION>" \
  --notes "<NOTES>" \
  dist/release/*
```

Print the release URL when done.

### 7. Remind the user to publish

The skill does **not** publish to npm — registry auth/2FA is interactive and belongs to the user. Print a clear reminder:

```bash
echo ""
echo "Release <VERSION> is tagged and on GitHub."
echo "To publish to npm, run: bun publish"
echo ""
```
