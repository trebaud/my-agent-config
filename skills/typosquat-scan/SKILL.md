---
name: typosquat-scan
description: Find lookalike domains for a brand. Generates typosquat candidates (omissions, transpositions, homoglyphs, keyboard typos, bitsquats, TLD swaps, doppelgangers, combosquats, plus expansion around known-active squats), resolves them via DNS (A + MX), probes HTTP/HTTPS, then renders each resolving name in a real browser to classify what a human sees: live kit, registrar parking, lapsed host, unprovisioned PaaS, or a phishing interstitial. Results persist to a JSON memory file so later runs surface newly registered squats. Use when the user wants lookalike domains, phishing impersonators, defensive registrations, or a brand-protection scan. Trigger on "find typosquats for X", "domain squatters", "lookalike domains", "check phishing variants", "brand protection scan".
---

# typosquat-scan

`/typosquat-scan <domain> [known-active squats ...] [--report]`

Known-active squats are lookalikes already confirmed live, in any format. `--report` renders the markdown + HTML reports; without it, no report files are written.

Scripts do I/O, the LLM does judgment. State lives in `./<domain>-typosquat-memory.json` (dots become `_`) in the current working directory, and rows older than 7 days are auto-rechecked, so the file doubles as a monitoring feed. Its highest-signal event is an `unregistered` to `resolves` transition. Paths below are relative to `~/.claude/skills/typosquat-scan/`.

## Workflow

0. **Repair first if needed.** If the memory file has many `status: "error"` rows from a saturated run, `go run scripts/typosquat_scan.go -repair <domain>` restores them from their `prev_status` lineage. Scanning against corrupted state wastes the run.

1. **Read [`references/typosquatting_patterns.md`](./references/typosquatting_patterns.md) and the memory file.** Never re-escalate a row carrying `verdict: FALSE_POSITIVE`.

2. **Expand any seeds first.** Known-active squats are the highest-yield generator available, because real operators register in families. Record them verbatim as `campaign_known` and expand their shared vocabulary as `campaign_pattern`. See the seed-expansion section of the patterns doc.

3. **Generate the rest.** Every applicable technique, skipping names already in memory. Prefer breadth across techniques over exhausting one.

4. **Write the memory file.** Keep existing rows verbatim; add new ones as `{"candidate": "<fqdn>", "technique": "<name>"}` with no `status` or `last_checked`. An empty `last_checked` is what marks a row pending.

5. **Resolve and probe.** Keep `-workers` low and confirm the run ends with `errors=0`; if not, re-run at lower concurrency.

   ```bash
   go run scripts/typosquat_scan.go -max-candidates 0 amazon.com
   ```

6. **Verify in a browser. Do not skip this.** A status code cannot tell a phishing kit from a parking page, and a client-rendered kit looks empty to curl, so every content-state claim must come from this step. Flags: `--all`, `--limit N`, `--only <substr>`, `--concurrency N` (default 4), `--headed`.

   ```bash
   node scripts/browser_verify.js amazon.com
   ```

7. **Pivot on confirmed kits.** Check `<title>` (often a bare domain, sometimes a *sibling squat's* name), the origin IP's other tenants, and unusual third-party asset hosts. Search those strings in urlscan and Shodan. See "Same-operator pivots" in the patterns doc.

8. **Render reports, only with `--report`.** The renderer derives everything mechanical and fills both templates; do not hand-assemble them. `--annotations notes.json` adds prose it cannot infer, with keys `headline`, `priority` (a list of `{candidate, tag, reason}`, which replaces the mechanical ranking entirely), and `fingerprints`. Omit a key to keep the derived version.

   ```bash
   python3 scripts/render_report.py amazon.com --annotations notes.json
   ```

9. **Record verdicts.** `CONFIRMED`, `FALSE_POSITIVE`, `WATCH`, or `REPORTED`, plus a `verdict_note`, so later runs stop re-flagging the same legitimate business.

10. **Respond with a plain list of new candidates and nothing else.** A fenced code block, one FQDN per line, ordered by the report template's priority rubric (externally-confirmed phishing first, live kits next, dormant-but-provisioned last). No preamble, counts, reasons, tags, or links. Empty list means the entire response is `(none)`. Everything else, including evidence and cluster breakdowns, goes only into the report files.

    A name qualifies only if all of these hold:
    - `status: "resolves"`.
    - It is new this run: a transition from `unregistered` or empty, or a row added this run that resolves.
    - `browser.content` is `FLAGGED_PHISHING`, `LIVE_CLONE`, `OFFSITE_REDIRECT`, `EXPIRED_HOST`, or `UNPROVISIONED`. Parking, brand redirects, blanks, and `FALSE_POSITIVE` rows are excluded.
    - It is not a seed the user supplied. Check that set literally, name by name.

    Four exceptions to the bare list: with `--report`, append one line giving the two file paths; if the run is untrustworthy (`errors` > 0, browser step skipped, resolver saturated) say so in one sentence first; if the user explicitly asks for analysis this turn, answer that instead; if a later step contradicts an earlier claim, correct it in one sentence, then give the list.

Both scanners take a quiet flag printing only bare FQDNs on stdout, diagnostics on stderr. Intersect the two lists and subtract the user's seeds to get step 10's answer:

```bash
go run scripts/typosquat_scan.go -quiet -max-candidates 0 amazon.com   # newly resolving
node scripts/browser_verify.js amazon.com --quiet                      # actionable content
```

Requirements: Go (stdlib-only; `go build -o scripts/typosquat_scan scripts/typosquat_scan.go` once for repeated use) and `playwright` with a Chromium build. If `require('playwright')` fails, run `npm i playwright` anywhere and pass `NODE_PATH=<dir>/node_modules`. Without Go you can resolve candidates with `dig`, but persistence and stale-recheck logic are lost.

## Memory file fields

Written by the scripts, read by you for triage.

| Field | Meaning |
|---|---|
| `status` | `resolves` (an A record exists: parking, CDN, or a real site), `unregistered` (NXDOMAIN, in practice available to register), `error` (SERVFAIL or timeout; state unknown rather than changed, retried next run). |
| `ip`, `mx` | A and MX records. `mx` means the name can receive mail. |
| `https`, `http` | Per-scheme probe: `status` after up to 5 redirects (`0` plus an `error` string means no response), `final_url` (a different host means the squat redirects somewhere), `server` (identifies parking providers like `namecheap-nginx` against real origins), `cdn: "cloudflare"` when a `cf-ray` was present, meaning the origin is shielded and abuse goes to Cloudflare. |
| `browser` | Authoritative over the probe. `content` is `FLAGGED_PHISHING`, `LIVE_CLONE`, `OFFSITE_REDIRECT`, `EXPIRED_HOST`, `UNPROVISIONED`, `BLANK`, `BRAND_REDIRECT`, `PARKED`, or `ERROR`. `https_ok: false` means no TLS listener on `:443`, and browsers try HTTPS first, so the name fails for real visitors whatever `http://` returns. `title` is the post-hydration `<title>`. `text` is the first ~240 chars of rendered `innerText`. `screenshot` points into `./<domain>-typosquat-shots/`. |
| `prev_status`, `prev_checked` | Preserved on a status flip; this is what surfaces transitions. |
| `verdict`, `verdict_note` | Your triage result, so later runs don't repeat it. |

A row going NXDOMAIN drops its stale probe and browser data. Both scripts rewrite the file via temp-file rename, so partial writes aren't a risk.

## Caveats

- **Resolver saturation is the expensive failure.** Defaults are `-workers 8 -dns-timeout 8s`. The old 50 workers / 2s saturates the macOS system resolver and mass-returns SERVFAIL: a 397-row scan produced 179 `error` rows in one pass, while 8 workers / 8s resolved the identical set with zero errors. Raise `-workers` only against a dedicated recursive resolver. An `error` result is non-destructive and retried every run, but that is damage control, not a substitute for low concurrency. The HTTP probe saturates the same way against one anycast IP; if many rows on a single IP report `timeout`, re-probe serially (`curl -sk -L --max-redirs 5 -m 8` with a browser UA) before concluding there is no listener.
- `resolves` does not mean active squatter, and an HTTP 200 does not mean a live site. Parking templates, lapsed panels ("Your Subscription Expired."), and unprovisioned PaaS hostnames all return 200, while a client-rendered kit returns an empty body to curl. Only the browser step separates these.
- A squat impersonating a *different* brand is not a false positive. Operators rotate which brand a label farm serves, and the name still captures your typo traffic.
- The script uses the system resolver. Behind split-horizon DNS the results differ from an attacker's-eye view, so re-run somewhere that only sees public resolvers.
- Clustering by `/24` collapses parking providers: twenty candidates on one parking IP become one line.
- ASCII labels only. IDN and Punycode homographs are out of scope; see the patterns doc.
