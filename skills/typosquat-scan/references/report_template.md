# Report templates

After the helper script writes results back to the memory file, the skill produces two report artifacts next to it:

- `<domain>-typosquat-report.md` — diffable, commits cleanly into a brand-protection repo
- `<domain>-typosquat-report.html` — single-file standalone artifact for non-engineering stakeholders

Both reports are derived entirely from the memory JSON. Read the memory file after the helper exits, then write each report using the template below. Substitute the `{{...}}` placeholders. Sort and group exactly as described — keep terminal output, markdown, and HTML aligned so reviewers can correlate them.

## Sorting and grouping rules

- **Resolving candidates** are grouped by `/24` of their A record. Clusters with more than one name get a header line; singletons render inline. Order clusters by size (largest first), then alphabetically by `/24` key. Within a cluster, sort candidates alphabetically.
- **Status transitions** include rows whose `prev_status` differs from the new `status`, plus first-time observations that resolved. Sort alphabetically by candidate. Show `prev_status` (or `new` if empty) → `status`.
- **By-technique table** counts every row in the memory file by `technique`, broken down by status. Sort by `resolving` desc, then `total` desc, then technique name.
- **`[MX]` marker** appears next to any resolving candidate whose `mx` field is non-empty.
- **HTTP signal** — each resolving row carries `https` and `http` probe objects (status code + final URL). Render the HTTP state inline so reviewers can see at a glance whether the squat serves content, redirects, or refuses connections.

## HTTP state classification

Resolve each candidate to one of these HTTP states by examining its `https` and `http` probe objects (HTTPS dominates when both succeed, since that's the realistic phishing channel):

| State | Definition | Triage weight |
|---|---|---|
| `LIVE` | `https.status` in 200–299 (or HTTP if no HTTPS) AND `final_url` host matches the candidate. The squat serves content from its own name. | Highest — pull a screenshot before it ages. |
| `REDIRECT_OFFSITE` | 2xx response but `final_url` host differs from the candidate AND from the target brand. Squat is funneling traffic somewhere. | High — check destination; often a redirect-based attack or affiliate skim. |
| `REDIRECT_TO_TARGET` | 2xx response and `final_url` host is (or is a subdomain of) the target brand itself. Defensive registration or someone signaling intent. | Medium — verify ownership via WHOIS. |
| `BLOCKED` | 4xx (403, 451, etc.) on both schemes. Server up, content gated — common for active infrastructure not yet pointed at a landing page. | Medium — recheck on next run. |
| `SERVER_ERROR` | 5xx on both schemes. | Low — could be misconfigured squat or transient. |
| `NO_HTTP` | Both probes error with connection refused / timeout / TLS failure. DNS-only registration. | Low for HTTP; **High if `mx` is non-empty** (mail-interception setup). |
| `OTHER` | Mix not covered above (e.g. HTTP 200 but HTTPS handshake fail, exotic codes). | Inspect manually. |

## Browser content state (overrides HTTP state when present)

If a row has a `browser` object (written by `scripts/browser_verify.js`), **its `content` value is authoritative** and the curl-derived HTTP state is only supporting detail. The HTTP layer routinely reports `LIVE` for parking pages and misses client-rendered kits entirely, so a report built on HTTP state alone overstates some rows and understates others.

| `browser.content` | Meaning | Triage weight |
|---|---|---|
| `FLAGGED_PHISHING` | An interstitial (Cloudflare, Safe Browsing) says this is phishing. A third party has already confirmed it. | **Highest** — externally corroborated. Cite in abuse reports. |
| `LIVE_CLONE` | Renders its own substantive content. Includes SPA kits that look empty to curl. | **Highest** — screenshot now, before it rotates. |
| `OFFSITE_REDIRECT` | Lands on an unrelated third party. Often an affiliate-referral skim. | High — name the destination and the monetisation. |
| `EXPIRED_HOST` | "Subscription expired" / suspended panel. Something *was* deployed here. | Medium-high — dormant, not innocent. Pull passive DNS + urlscan history. |
| `UNPROVISIONED` | PaaS hostname with nothing deployed ("Application not found"). | Medium — provisioned intent, no content yet. Recheck. |
| `BLANK` | Loads, renders nothing. | Low-medium — often a CDN catch-all. |
| `BRAND_REDIRECT` | Lands on the protected brand. | Medium — likely defensive; confirm via WHOIS. |
| `PARKED` | Registrar/broker template (Namecheap, GoDaddy, HugeDomains, Sedo, Bodis). | Low — aggregate only, do not enumerate. |
| `ERROR` | Did not load on either scheme. | Low for web; **high if `mx` is set**. |

Always surface `browser.https_ok == false` next to the candidate as `[NO-HTTPS]`. Browsers try HTTPS first, so a name with no TLS listener does not work for real victims — and it is the answer when a reviewer reports that a flagged link "didn't work in my browser."

## Priority scoring (drives the "Recommended next steps" block)

Browser content state is the primary signal, freshness is the multiplier, cluster membership is the tiebreaker. Score every resolving row, highest first:

1. **Fresh registration** — row appears in this run's status transitions (`prev_status` was `unregistered` or empty, now `resolves`), or the candidate was added this run and resolves. Strongest squatter signal in the dataset. Rank fresh rows above equivalent older ones and tag each with its content state.
2. **`FLAGGED_PHISHING`** — a third party already confirmed phishing. Quote the interstitial text.
3. **`LIVE_CLONE`** — serving its own content. `[MX]` raises urgency further (full kit with mail). Note whether the origin is Cloudflare-shielded, since that decides who can take it down.
4. **`OFFSITE_REDIRECT`** — document the destination host and the apparent monetisation (affiliate ref parameter, competitor storefront).
5. **`EXPIRED_HOST` / `UNPROVISIONED`** — provisioned but dormant. These are the early-warning rows; call out that they need a recheck rather than an abuse report.
6. **`ERROR`/`NO_HTTP` + MX** — no web service but mail-capable. Mail-interception or BEC setup; web-only triage misses it entirely.
7. **`BRAND_REDIRECT`** — points at the brand. Usually defensive; confirm via WHOIS.
8. **Everything else** — parking, CDN catch-alls, broker listings. Aggregate count only.

Quote at most 5 candidates by name in the priority block **unless the user asks for the new findings up front**, in which case lead with every fresh row that has a non-parking content state and let the block run longer. Everything else rolls up into the cluster counts further down.

Anything carrying `verdict: FALSE_POSITIVE` is excluded from the priority block entirely and listed in the "Known false positives" section instead, so it is never re-escalated on a later run.

## Plain candidate list (always include)

Reviewers frequently want to copy names straight out of the report into a ticket, a blocklist, or an abuse form. Emit a fenced code block, one FQDN per line, no commentary, no markup, sorted by priority — immediately after the priority block:

````markdown
## Actionable names (plain list)

```
arnazon.info
arnazon.top
amazom.com
```
````

Include only rows whose content state is `FLAGGED_PHISHING`, `LIVE_CLONE`, `OFFSITE_REDIRECT`, `EXPIRED_HOST`, or `UNPROVISIONED`. Exclude parking, brand redirects, and known false positives. When a reviewer asks for "just a list", this block is the answer — bare names, nothing else.

## Quick-test link set

Every resolving candidate gets the same five links so a reviewer can triage in one click. Use the candidate FQDN verbatim — these are user-derived strings, so URL-encode in HTML (markdown autolinks tolerate dots and hyphens directly).

| Label | URL pattern | What it answers |
|---|---|---|
| `visit` | `https://{candidate}` | Is there a live site? Parking page or real content? |
| `crt.sh` | `https://crt.sh/?q={candidate}` | When was the first TLS cert issued? Any subdomains? |
| `VT` | `https://www.virustotal.com/gui/domain/{candidate}/detection` | Any AV vendor flagging it? Passive DNS history. |
| `urlscan` | `https://urlscan.io/domain/{candidate}` | Recent screenshots, redirects, requested resources. |
| `whois` | `https://who.is/whois/{candidate}` | Registrar, creation date, registrant (often privacy-masked). |

Render them in markdown as ` · `-separated bracketed links after the IP/technique line. Don't add links to unregistered or error rows.

## Markdown template

```markdown
# Typosquat scan: {{TARGET}}

_Generated {{LAST_RUN}} — run #{{RUN_COUNT}}_

## Summary

| Metric | Count |
|---|---:|
| Candidates tracked | {{STATS_TOTAL}} |
| Resolving (registered, DNS active) | {{STATS_RESOLVING}} |
| Unregistered (NXDOMAIN — available) | {{STATS_UNREGISTERED}} |
| Lookup errors (retry next run) | {{STATS_ERRORS}} |

<!-- Second table: browser content-state counts over resolving rows that carry a
`browser` object. Omit the table if none do, and say so explicitly:
_No rows browser-verified this run — content states below are curl-derived and
may misread parking pages as live._ -->

| Browser content state | Count |
|---|---:|
| `FLAGGED_PHISHING` | {{N_FLAGGED}} |
| `LIVE_CLONE` | {{N_LIVE_CLONE}} |
| … | … |

## Recommended next steps

<!-- One short paragraph headline ("N high-priority items this run."), then a
bulleted list of the top items by the priority rubric above. For each, lead
with the candidate FQDN, give the content-state tag, the one-line reason, then
the quick-test links. Cap at 5 candidates — unless the user asked for new
findings up front, in which case lead with every fresh non-parking row.

State the evidence, not a guess: quote the page title, the interstitial text,
or the redirect destination. Say whether the origin is Cloudflare-shielded,
because that decides who can take it down. Example shapes:

  - **Fresh registration · FLAGGED_PHISHING:** `<candidate>` → `<ip>` _(<technique>)_ [MX]
    Cloudflare serves "Suspected Phishing" — externally confirmed. Cite in the abuse report.
    [visit](https://<candidate>) · [crt.sh](https://crt.sh/?q=<candidate>) · [VT](https://www.virustotal.com/gui/domain/<candidate>/detection) · [urlscan](https://urlscan.io/domain/<candidate>) · [whois](https://who.is/whois/<candidate>)

  - **Fresh registration · LIVE_CLONE:** `<candidate>` → `<ip>` _(<technique>)_ [MX]
    Renders a full storefront, title `<title>`; origin `nginx/1.18.0` with no cf-ray —
    hosting provider is reachable, file there first.
    [visit](...) · [crt.sh](...) · [VT](...) · [urlscan](...) · [whois](...)

  - **OFFSITE_REDIRECT:** `<candidate>` → `<ip>` _(<technique>)_
    Redirects to `<final_host>` with an affiliate ref param — monetised brand hijack.
    [visit](...) · [crt.sh](...) · [VT](...) · [urlscan](...) · [whois](...)

  - **EXPIRED_HOST:** `<candidate>` → `<ip>` _(<technique>)_
    Serves only "Your Subscription Expired." — a kit was deployed here and lapsed.
    Pull passive DNS / urlscan history for what it served.
    [visit](...) · [crt.sh](...) · [VT](...) · [urlscan](...) · [whois](...)

  - **ERROR + MX:** `<candidate>` → `<ip>` _(<technique>)_ [MX]
    No web service on either scheme, MX present — mail-interception setup, not web.
    [visit](...) · [crt.sh](...) · [VT](...) · [urlscan](...) · [whois](...)

Append `[NO-HTTPS]` to any row with `browser.https_ok == false` and explain once
in the section that such names fail in a real browser, which is why a reviewer
may report the link as broken.

Close the section with a one-line summary of the rest:
  _N other resolving candidates are registrar parking or CDN catch-alls (see below)._

If no resolving candidates: write _No resolving candidates this run — nothing to action._
-->

## Actionable names (plain list)

<!-- Fenced code block, one FQDN per line, no markup or commentary, ordered by
the priority rubric. Include only FLAGGED_PHISHING / LIVE_CLONE /
OFFSITE_REDIRECT / EXPIRED_HOST / UNPROVISIONED rows; exclude parking, brand
redirects, and known false positives. This block exists so a reviewer can copy
names straight into a ticket, blocklist, or abuse form. -->

## Same-operator fingerprints

<!-- Omit if nothing correlates. Otherwise call out, with the evidence:
  - kit tells (a `<title>` that is a bare domain name, or a sibling squat's name)
  - shared origin IPs holding more than one confirmed kit
  - unusual third-party asset hosts loaded by the kit
  - registrar / privacy-service / nameserver tuple shared across registrations
  - which brand each kit currently impersonates, if it is not the target brand
These are the pivots that find names candidate generation cannot. -->

## Resolving candidates ({{STATS_RESOLVING}})

Grouped by `/24` so parking-provider clusters collapse into a single block. `[MX]` means the name can receive email. The `https=…` / `http=…` line carries the HTTP probe state (status code + final-URL host if redirected, or the connection error). Each row also carries quick-test links — click through to triage.

<!-- For each cluster:
  - if singleton:
    - `<candidate>` → `<ip>` _(<technique>)_  [MX]
      `https=200 (self)` · `http=301→<final_host>`
      [visit](https://<candidate>) · [crt.sh](https://crt.sh/?q=<candidate>) · [VT](https://www.virustotal.com/gui/domain/<candidate>/detection) · [urlscan](https://urlscan.io/domain/<candidate>) · [whois](https://who.is/whois/<candidate>)
  - if multi:
    - **Cluster <ip>/24** (<n> names on shared infrastructure):
      - `<candidate>` → `<ip>` _(<technique>)_  [MX]
        `https=…` · `http=…`
        [visit](...) · [crt.sh](...) · [VT](...) · [urlscan](...) · [whois](...)
      - ...
  If no resolving rows, write: _None._
  Format conventions for the http line:
    - successful response: `https=<code>` if final_url host matches candidate, `https=<code>→<final_host>` otherwise.
    - missing response: `https=<error>` (the short `error` field from the probe, e.g. `connection refused`, `timeout`).
    - omit the per-scheme entry entirely if the probe object is missing (older memory files).
    - append `· server=<server>` when the probe captured one, and `· cloudflare` when `cdn` is set —
      these decide who to file abuse with.
  When the row has a `browser` object, put its state and evidence on their own line
  directly under the http line, since it overrides the HTTP reading:
      **`<content>`** [NO-HTTPS] · title `<title>`
-->

## Known false positives

<!-- Omit if empty. One bullet per row carrying `verdict: FALSE_POSITIVE`:
  - `<candidate>` → `<ip>` — <verdict_note>
These are recorded so later runs don't re-escalate them. Typical members: an
unrelated legitimate business owning a near-miss name, or a domain broker's
for-sale listing. -->

## Status transitions this run ({{N_TRANSITIONS}})

<!-- Omit this whole section if there are no transitions. Otherwise one bullet per transition:
  - `<candidate>`: <prev_status or "new"> → **<status>**  [MX]
    `https=…` · `http=…` (only when status == resolves)
    [visit](https://<candidate>) · [crt.sh](https://crt.sh/?q=<candidate>) · [VT](https://www.virustotal.com/gui/domain/<candidate>/detection) · [urlscan](https://urlscan.io/domain/<candidate>) · [whois](https://who.is/whois/<candidate>)
  (Only attach the http line and links when the new status is `resolves`.)
-->

## By technique

| Technique | Total | Resolving | Unregistered | Errors |
|---|---:|---:|---:|---:|
<!-- one row per technique, sorted resolving desc / total desc / name asc -->

## Notes

- `resolves` ≠ active squatter. Most resolving lookalikes are registrar parking pages or CDN catch-alls. Triage out-of-band (WHOIS, TLS cert SAN, reverse DNS, CT-log history).
- **An HTTP 200 is not a live site.** Rows carrying a `browser` state were rendered in real Chromium; that state overrides the curl reading. Rows without one may misreport parking pages as live and miss client-rendered kits entirely.
- `[NO-HTTPS]` means no TLS listener on `:443`. Browsers try HTTPS first, so these names fail for real visitors even when `curl http://` returns 200 — that is the usual reason a flagged link "doesn't work in a browser".
- `[MX]` on a resolving candidate is a stronger phishing/mail-interception signal than HTTP-only.
- `cloudflare` on a row means the origin IP is shielded: file abuse with Cloudflare. A real `server` header with no `cf-ray` means the hosting provider is directly reachable — action those first.
- A squat impersonating a *different* brand is still a squat on this brand's typo traffic, and can be repointed in minutes. It is not a false positive.
- The system resolver was used. Behind split-horizon DNS, results may differ from an external view.
```

## HTML template

Use the file [`report_template.html`](./report_template.html) verbatim — it contains the full standalone document with embedded CSS, light/dark via `color-scheme`, and the same sections as the markdown report. Substitute the same `{{...}}` placeholders. The HTML-specific placeholders (`{{PRIORITY_BLOCK}}`, `{{RESOLVING_BLOCK}}`, `{{TRANSITIONS_BLOCK}}`, `{{TECHNIQUE_ROWS}}`) are HTML fragments to splice in; the comment inside each one shows the exact tag shape to emit per row/cluster, including the inline `<a>` quick-test link strip.

Always HTML-escape user-derived strings (candidate, IP, technique, status values) when emitting HTML, and URL-encode the candidate when building link `href`s — none of these are trusted, even though they came from your own DNS lookups.
