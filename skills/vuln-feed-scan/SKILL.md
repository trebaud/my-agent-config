---
name: vuln-feed-scan
description: Scan a whitelist of security feeds for recent high-signal vulnerabilities that pose immediate threat to the stack you configure (resolved from your prompt, a local stack file, or the manifests in the working directory), then cross-check each surviving finding against repositories in the current working directory and report concrete lockfile/package hits. Use when the user asks to check security news, scan vuln feeds, look for recent CVEs/zero-days, or run an OSINT sweep for security incidents. Keywords include "check vulns", "security feed scan", "any new CVEs", "zero-day check", "scan for threats".
---

# Vuln Feed Scan

Scan the whitelist sources below and surface only vulnerabilities that directly threaten the resolved stack. Keep it terse.

## Stack filter (scoring context)

Every filter and score below is relative to a **stack filter**. Resolve it once, before fetching anything, in this order — first hit wins:

1. **The user's prompt for this run.** An explicit stack ("scan for our Go/Postgres services") overrides everything else and applies to this run only.
2. **A stack file** — `./vuln-feed-stack.md` in the working directory, else `~/.claude/vuln-feed-stack.md`. Free-form prose or a list: languages, runtimes, datastores, package registries, cloud providers, and any domain-specific library families that matter. Keep it out of version control if the stack is not public.
3. **Derived from the working directory.** Enumerate repos as in step 5a and read their manifests — `package.json` and lockfiles, `go.mod`, `Cargo.toml`, `pyproject.toml`/`requirements.txt`, `Gemfile`, `pom.xml`, `Dockerfile`, IaC files. The languages, frameworks, datastores, and cloud SDKs actually present *are* the stack.

Whichever source resolved it, restate the stack in the step-1 plan so the user can correct it before the run burns fetches. If none of the three yields anything, say so and stop — an unfiltered feed scan is noise.

Also flag infra that sits in front of or alongside the resolved stack: TLS libs, HTTP parsers, container runtimes, CI/CD (GitHub Actions), the dominant frameworks / ORMs / auth libs of its languages, and the hosting providers its manifests point at.

## Whitelist

Check these first. Do not read sources not on this list unless the user expands the list for this run. Sources are tiered; the tier affects scoring in step 3.

**Primary / authoritative:** original advisories and canonical vuln data; signal stands on its own.

- https://github.com/advisories?query=type%3Areviewed+ecosystem%3Anpm (npm advisories)
- https://socket.dev/blog
- https://www.aikido.dev/category/vulnerabilities-threats
- https://snyk.io/blog/
- https://www.stepsecurity.io/blog
- https://www.wiz.io/blog

**Secondary / journalism:** original reporting, often derivative of a vendor advisory but can break stories.

- https://www.bleepingcomputer.com/
- https://thehackernews.com/

**Community-curated:** link aggregation; front-page position is a strong community validation signal.

- https://news.ycombinator.com/ — filter to security/CVE/exploit stories and record the item's approximate page position (top 10 / rest of page 1 / later). High placement = real signal even without other corroboration.

If the user provides additional URLs in their prompt, add them to this run only; do not persist.

## Workflow

Run these in order.

### 1. Plan the run

Emit a one-line plan stating: scan start timestamp (UTC, format `YYYY-MM-DD HH:MM:SS UTC`), cutoff window (default: last 24h), the resolved stack filter and where it came from, and whitelist size. Let the user interrupt if they want to change scope (e.g. widen to 3d after a quiet weekend).

### 2. Fetch whitelist in parallel

Use `WebFetch` on every whitelist URL in a single message with parallel tool calls. Do not fetch serially. Ask each fetch to extract: item title, publish date, affected product/version, CVE id if present, one-line summary.

For aggregator pages (HN, Bleeping, Krebs), the prompt should request only items matching security/vuln/CVE/exploit/breach keywords, to avoid pulling general tech news.

### 3. Build candidate list

**3a. Age gate.** Drop anything older than the cutoff window × 1.5 (default window 3 days → hard drop at 5 days). Exception: items labeled actively exploited, CISA KEV, or supply-chain may extend to 10 days. Anything older than 10 days is always dropped. Deduplicate across sources (same CVE or same incident).

**3b. Stack pre-filter (hard drop, not scoring).** An item must satisfy at least one of the following before it is scored. If none match, drop it — do not carry it into scoring on "interesting" grounds:

- Directly affects a stack item: a language runtime, compiler, framework, datastore (server or official drivers), package registry, cloud service, or library family named in the resolved stack — including any popular package in its ecosystems (≥100k weekly downloads, or a known transitive dep of a framework/ORM in the stack).
- Affects adjacent infra the stack runs on: TLS libs (OpenSSL, BoringSSL, rustls), HTTP parsers used by its runtimes, container runtimes (Docker/containerd), GitHub Actions, or the hosting provider its manifests point at.
- Supply-chain incident affecting a developer tool the stack plausibly pulls: package-registry or GitHub/CI provider breach, maintainer account takeover of a popular package, malicious version published to a registry, leaked CI/provider tokens.

Anything whose blast radius lands entirely outside the resolved stack is **out of scope** — drop it even if it looks spicy. Typical drops: ecosystems the stack doesn't use, desktop/office software, ICS/OT, and niche packages (<100k weekly downloads and no popular parent).

**3c. Score survivors.**

**Severity / impact:**

| Signal | Weight |
|---|---|
| Published ≤ 24h ago | +4 |
| Published ≤ 48h ago | +2 |
| Published 2–3d ago | −2 |
| Published 4–7d ago | −4 (only via the KEV/exploited/supply-chain age exception) |
| Published 8–10d ago | −6 (KEV/exploited/supply-chain only; must be genuinely active) |
| Labeled zero-day / actively exploited / in CISA KEV | +5 |
| Directly affects a stack item | +4 |
| Affects adjacent infra the stack runs on | +2 |
| Pre-auth RCE | +3 |
| Credential theft / secret exposure affecting the stack | +3 |
| Requires unusual local access or social engineering only | −3 |
| No CVE, no vendor advisory, no PoC | −2 |

**Supply-chain signals** (apply on top of the severity table; one compromised dep poisons every repo that pulls it, so weight these heavily):

| Signal | Weight |
|---|---|
| Popular package in a stack ecosystem compromised: malicious version published, or maintainer account takeover | +6 |
| A package registry the stack uses, GitHub Actions, or a major CI/CD provider breached | +5 |
| Hosting/deploy provider the stack sits on breached with dev tokens leaked | +5 |
| Typosquat / dependency-confusion campaign targeting a registry the stack uses, with confirmed downloads | +3 |
| Build-tool or lockfile-manipulation vulnerability (npm, pnpm, yarn, bun) | +3 |

**Source signal** (apply by source tier, not raw count; multiple mentions of the same underlying article do not stack):

| Signal | Weight |
|---|---|
| Reported by ≥1 primary source | +3 |
| Reported by ≥2 primary sources | +4 (instead of +3) |
| Reported by a secondary (journalism) source | +2 |
| Same incident in both primary and secondary | +1 (on top of the above) |
| Appears on HN front page (top ~10) | +2 |
| Appears on HN page 1 below top 10, or later pages | +1 |

Keep items with score ≥ 7 before step 4. Cap at top 8 candidates. If nothing scores ≥ 7, say so and stop. Do not pad. Supply-chain items that clear the bar must be ranked above same-score non-supply-chain items in the final report.

### 4. Corroborate with a generic search

For each surviving candidate, run one `WebSearch` using the CVE id or incident name plus a confirmation term (`"exploited" OR "PoC" OR "patch"`). Do these searches in parallel.

Adjust score based on what the search returns. Do not drop items for lack of corroboration; a freshly-disclosed vuln may legitimately have only one source at first.

| Search result | Weight |
|---|---|
| Vendor advisory, KEV entry, or CVE record found independently | +3 |
| Second outlet or public PoC repo found | +2 |
| Nothing found | −2 |

Re-apply the score ≥ 7 cutoff after this adjustment. A single primary-source item (e.g. a fresh KEV entry) still clears the bar on its own; a single secondary-source story with no corroboration usually will not.

### 5. Cross-check against local repos

For every finding that survived step 4, check whether the affected package/component appears in any repository sitting in the current working directory. This is the step that turns a feed scan into an actionable patch list.

**5a. Enumerate repos and attack surfaces.** Run `ls -la` (or `find . -maxdepth 2 -name package.json -o -name go.mod -o -name pyproject.toml -o -name Cargo.toml` with build dirs pruned) to identify candidate repo directories. Treat each immediate subdirectory as a separate repo. Skip `node_modules`, build output dirs, and anything obviously not a project root. Record the list — it goes in the report header.

For **every** repo in the list, enumerate the attack surfaces below before per-finding lookup. Do not skip a surface because the previous repo didn't have it; check each repo independently. Missing files are fine, but the *check* must run per repo per surface.

- **Package manifests and lockfiles** — every manifest and **every lockfile** the repo carries (`package.json` + `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock` / `npm-shrinkwrap.json` / `bun.lockb`, `go.mod` + `go.sum`, `pyproject.toml` + `poetry.lock` / `uv.lock`, `Cargo.toml` + `Cargo.lock`, `Gemfile` + `Gemfile.lock`), plus any workspace manifests (e.g. `packages/*/package.json`, `apps/*/package.json`). Lockfiles carry the resolved versions and are the primary attack surface; never skip them.
- **GitHub Actions** — every file under `.github/workflows/` (`*.yml`, `*.yaml`) plus `.github/actions/*/action.yml` for composite actions. Treat this surface as mandatory for every repo, even if the finding looks unrelated — a finding can hit via a reusable action or a third-party `uses:` reference you wouldn't otherwise expect.
- **Other manifests** — `Dockerfile`, `docker-compose*.yml`, IaC (`*.tf`, `cdk.*`, `serverless.yml`, `cloudformation*.{yml,json}`), and runtime configs (`.nvmrc`, `.node-version`, `tsconfig.json`) when the finding plausibly touches them.

**5b. Per-finding lookup.** For each surviving candidate, run the cheapest applicable check across every repo in parallel. **Every finding must be cross-checked against every repo** — do not stop at the first hit, and do not assume one repo's result applies to the others. When in doubt, run the grep; the cost is negligible compared to missing a hit.

- **npm package compromise / CVE in a JS/TS library** — for **every** repo, grep all package manifests (`package.json` at root and in any workspace path) for the package name, then grep **every** lockfile present (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `npm-shrinkwrap.json`, `bun.lockb`) to capture the actually-resolved version. Both direct and transitive matter — a clean `package.json` with a poisoned lockfile entry is still a hit.
- **Registry / supply-chain worm with a known publish-window** — also check each lockfile's `mtime` against the malicious-publish window (`ls -la <repo>/pnpm-lock.yaml` etc., for every lockfile in every repo). A lockfile written inside or seconds after the window is a critical signal even when versions look clean.
- **GitHub Actions / CI vulnerability** — for **every** repo, grep all files under `.github/workflows/` (`*.yml` and `*.yaml`) and any `.github/actions/*/action.yml` composite actions for the affected action, `uses:` reference, trigger, or pattern. Always run this check even when the finding's primary vector looks unrelated — a vulnerable third-party action can land via a workflow that pulls it transitively.
- **Cloud service issue** — grep IaC files (`*.tf`, `cdk.*`, `serverless.yml`, `cloudformation*.{yml,json}`) and cloud SDK imports for the affected service.
- **Container / runtime CVE** — grep `Dockerfile`, `docker-compose*.yml`, base image tags.
- **Any other library family in the stack** — grep package names plus any direct imports.

For each finding, capture: the repo(s) that hit, the file(s) and line(s), the actually-resolved version where applicable, and whether it's direct or transitive. Note the lockfile `mtime` only when the finding has a time-bounded compromise window. Keep this evidence — it goes into the detail block.

**5c. Run read-only checks and capture verbatim output.** Use cheap, read-only tools: `grep -rn`, `ls -la`, `cat`, `find`. Run them via `Bash` and **keep the exact output** — trimmed to the relevant lines, but verbatim (file paths, line numbers, resolved versions). This output is embedded into the report in step 6b as a fenced `Local evidence` block, so the user can see for themselves what the scan found. Do not paraphrase. Do not run anything that mutates lockfiles, installs packages, hits the network, or modifies CI state — those are *remediation commands* the user runs themselves (step 6c). If a repo's lockfile is in an unfamiliar format, note it (`{repo}: lockfile format unrecognized`) and move on.

**5d. No-hit findings still ship.** A finding can clear the score bar without matching any local repo — it stays in the report, but its detail block's `In your repos` line says `No direct or transitive match found in <N> repos checked.` so the user sees the check was actually run.

**5e. Hard-drop findings the local check rules out.** If a finding's only path to relevance is "the repos might use X" and grep proves they don't (e.g. Jenkins plugin compromise + no Jenkins anywhere), move the finding from the main report to *Also worth a glance* with the reason `no usage in local repos`. Don't silently delete it.

### 6. Generate an IoC scan script (conditional)

For findings where the source materials publish concrete **Indicators of Compromise** — malicious package versions, file hashes (SHA256/SHA1/MD5), suspicious file paths or filenames, post-install hook signatures, exfil domains/URLs, IPs, npm publish accounts, distinctive strings in malicious code — write a single bash script that scans the working directory and local system for those exact indicators.

**Hard rules:**

- **Extract verbatim.** Every IoC in the script must be quotable from a fetched source (primary advisory, vendor blog, GitHub Security Advisory, CISA KEV entry, etc.). Cite the source URL in a comment above each block. Do **not** infer, extrapolate, generate plausible-looking hashes/domains, or pattern-complete from partial data. If a source lists 3 hashes, the script checks 3 — not 4.
- **Skip the step entirely if no finding has published IoCs.** Most CVEs ship with affected-version ranges only; those are already covered by step 5 and don't need a separate script. The trigger for this step is concrete forensic artefacts (hashes, domains, distinctive filenames, malicious code snippets), typically from supply-chain incidents, malware campaigns, or post-incident vendor write-ups.
- **Read-only.** The script must only `grep`, `find`, `shasum`/`sha256sum`, `ls`, `stat`, `cat`, `pgrep`, `lsof`, `netstat`/`ss`, or equivalent. It must never modify files, install anything, hit the network with credentials, or alter system state. macOS-compatible (BSD `find`/`stat`, `shasum -a 256`, not `sha256sum`) since the host is darwin.
- **Exclude self-referential matches.** Every string IoC (IPs, usernames, distinctive paths like `/tmp/.sshd`, attacker handles, package names with no version) will match the script's own body and any scan reports sitting in the working directory — producing 100% false-positive `[HIT]` lines that drown out real signal. Every `grep` that walks the working directory unscoped (i.e. not narrowed by `--include=package.json` / lockfile patterns) **must** exclude: the script itself, the markdown/HTML report files written this run, and any prior `*vuln-scan*` artefacts. Concrete flags to add: `--exclude='*ioc-scan.sh' --exclude='*vuln-scan.*' --exclude-dir=reports --exclude-dir=node_modules`. Apply the same exclusion in any companion `find` that walks the tree. Scoped greps (e.g. `--include=package.json --include=pnpm-lock.yaml`) are safe and do not need the flags. When in doubt, add the exclusions — a false-positive HIT is worse than a missed self-reference.
- **Group by finding.** Use a clearly delimited section per finding with a header comment naming the CVE/incident and the source URL. Each section prints `[HIT]` or `[clean]` lines so output is greppable.
- **Final summary.** End with a count of `[HIT]` lines so the user instantly knows whether anything matched.

**Script path:** `./YYYY-MM-DD_HH-MM-SS_ioc-scan.sh` (same timestamp as the report files in step 7). Make it executable (`chmod +x`). Do not run it — just write it and tell the user the path.

If you skip this step because no finding had concrete IoCs, say so in one line in the report (`No IoC script generated — no source published concrete indicators this run.`) so the user knows the check was considered.

### 7. Report

Output the findings to the user. The report is the only thing they read — format it for scanning, most-urgent first, with whitespace between findings. The exact templates (ranked table columns, detail-block structure, remediation-commands block, "Also worth a glance" section, empty-report sentinel) live in **`references/report-format.md`** under "On-screen report". Read that file before rendering the report.

If step 6 produced a script, reference its path in the report so the user can find it.

### 8. Save report files

After outputting the report, write a markdown file and a self-contained HTML file in parallel with `Write`. Use `date -u +%Y-%m-%d_%H-%M-%S` to obtain the timestamp at write time.

- Markdown path: `./YYYY-MM-DD_HH-MM-SS_vuln-scan.md`
- HTML path: `./YYYY-MM-DD_HH-MM-SS_vuln-scan.html`

Content and styling specs for both files are in **`references/report-format.md`** under "Saved markdown file" and "Saved HTML file" — header format, metadata line, severity badge colors, layout, etc.

After writing the HTML file, open it:

```bash
open ./YYYY-MM-DD_HH-MM-SS_vuln-scan.html
```

Confirm with a single line: `Reports saved to ./<filename>.md and <filename>.html`.

## Rules

- Always run step 4. A single primary source (KEV, GH Advisory, NVD, vendor advisory) is sufficient signal on its own. A single secondary source, or an HN story with an unfamiliar underlying link, must be corroborated by step 4 before it qualifies.
- Never invent CVE ids or dates. If a date isn't in the fetched content, mark it `date?` and down-rank.
- Do not include general security best-practice advice. Report findings only, not hygiene.
- Do not summarize items the user almost certainly already knows (e.g. year-old log4j). Respect the cutoff window.
- If a fetch fails, note it in a single line at the end (`Fetch failed: <url>`) and continue with the rest. One broken source should not block the whole run.
