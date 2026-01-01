# Typosquatting patterns

Playbook for generating typosquat candidates. The LLM produces the candidate list by applying every applicable technique below to the target label, then writes the merged result into `./<domain>-typosquat-memory.json` (new entries with `{"candidate": "<fqdn>", "technique": "<name>"}` and no `last_checked`); the helper script `scripts/typosquat_scan.go` then resolves every pending and stale row. Each section names a technique, says what it models, and shows what its output looks like for the example label `google` (TLD `com`). The technique names match the `technique` field on each candidate in the JSON memory file.

When generating, apply every technique to the target's label, plus the `tld_swap` set against a curated TLD list (`com, net, org, co, io, app, dev, cc, tv, me, info, biz, us, uk, eu, xyz, online, site, store, shop, club, page, ai`). Skip candidates already present in the memory file. The helper caps the batch at `-max-candidates`, so for very common-letter labels prefer a balanced subset across techniques rather than exhausting one type first.

## campaign_known and campaign_pattern (seed expansion) — do this first

**This is the highest-yield technique in the playbook whenever you have even one confirmed-active squat.** Blind generation produces thousands of plausible labels of which a fraction of a percent resolve; expanding around a *known* squat hits repeatedly, because real operators register in families rather than one-offs.

Record the seeds the user gives you (or that a previous run confirmed) as `campaign_known`, verbatim, even when your generators would never have produced them. Then expand around them as `campaign_pattern`:

1. **Decompose each seed into its deviation from the brand.** For a label like `exampay`, seeds `exapmay`, `exampaay`, `exsampay`, `exompay`, `exampat` decompose into a reusable vocabulary: an `mp`↔`pm` transposition stem (`exapm…`), an `a`-count mutation (`…paay`, `…pa`), an `a`→`o` vowel shift (`exom…`), an inserted `s` (`exsam…`), and a `y`→`t` substitution.
2. **Cross-product the vocabulary.** Apply each seed's mutation to the other seeds' stems — `exapmay` plus the doubled-vowel ending yields `exapmaay`, edit-distance 3 from the brand and reachable by no standard technique. In a confirmed run this cross-product step produced the single best find of the scan: an edit-distance-3 name serving a live storefront on the *same IP* as its seed.
3. **Lift every seed onto the TLDs the campaign already uses.** Operators reuse registrars and price tiers. If a seed appears on `.top` or `.info`, try every other seed on `.top` and `.info`. Cheap-TLD sets worth adding beyond the curated list: `top, icu, vip, cfd, sbs, live, fun, space, website, online, shop, pro, one`.
4. **Add brand-semantic TLDs** for the target's vertical — the words a customer would associate with the brand. Payments/fintech: `cash, finance, money, exchange, credit`. Retail: `shop, store, deals, gift`. SaaS/infra: `app, cloud, dev, network, link`. Health: `care, clinic, health`. Pick from the target's own vertical; do not paste all of them.
5. **Add vertical-specific combosquat keywords** on top of the generic list — the nouns and verbs that appear in the brand's own funnel, since a kit needs them to look plausible. Derive them from the target's site rather than a fixed list: an account verb (`login, signin, verify, kyc`), a money verb (`pay, refund, claim, redeem`), and a product noun (whatever the brand actually sells).

Prefer edit-distance-3+ candidates that a seed justifies over exhausting edit-distance-1 candidates the generators already covered. Standard techniques saturate quickly; seed expansion does not.

## omission

Drop one character from the label. This is what happens when a finger slips or a key gets missed. Output: `oogle`, `ggle`, `goole`, `googe`, `googl`. Labels of two characters or fewer are skipped, since the result is too short to be meaningfully confusable.

## multi_omission

Drop two adjacent characters. Only runs for labels of eight characters or more, where the result is still distinctively close to the brand. Output for `cloudflare`: `oudflare`, `cudflare`, `cldflare`, `cloflare`, `cludflare`-style results — every adjacent pair removed in turn. Captures realistic two-finger fumbles on long brand names that the single-character omission misses.

## repetition

Double one character. Captures stuck keys and held-too-long fingers. Output: `ggoogle`, `gooogle`, `googgle`, `googlee`. A noticeable share of real squatters use this for short, recognizable brand names.

## transposition

Swap two adjacent characters, the classic hand-coordination slip. Output: `ogogle`, `gogole`, `goolge`, `googel`. Pairs of identical characters are skipped because the swap would be a no-op.

## replacement (keyboard)

Replace a character with one of its US-QWERTY neighbors, i.e. hitting the wrong key. Output for `g`: `f`, `t`, `y`, `h`, `b`, `v` substituted in place. Tuned for ASCII and US keyboards. AZERTY and Dvorak users mistype differently, but US QWERTY remains the dominant target.

## insertion (keyboard)

Insert a keyboard-neighbor character next to an existing one, the stray-finger case. Two insertion points per neighbor: before and after the source character. Output for `g`: `fgoogle`, `gfoogle`, `tgoogle`, `gtoogle`, and so on.

## homoglyph

Replace a character with a visually similar single character (ASCII only). The attacker is targeting the reader's eye, not the typist's fingers; the URL should look right at a glance. Substitutions used: `o`/`0`, `l`/`1`/`i`, `e`/`3`, `a`/`4`, `s`/`5`, `b`/`8`, `g`/`9`, `z`/`2`, `t`/`7`. Output: `g00gle`, `googie`, `goog1e`, `g0ogle`. Unicode and IDN homographs (Cyrillic `а` for Latin `a`, and so on) are not covered. See "Out of scope" below.

## compound_homoglyph (cognitive blindspot)

Replace a single character with a *multi-character cluster* whose glyphs combine into the same visual shape at a glance — `m` → `rn`, `w` → `vv`. Output: `arnazon.com` for `amazon`, `vvalmart.com` for `walmart`, `tvvitter.com` for `twitter`, `grnail.com` for `gmail`.

This is distinct from single-character homoglyph. There, the substitution exploits *character-level* visual similarity (`o` looks like `0` on its own). Here, the substitution exploits a perceptual blindspot in *word-level* reading: the brain chunks adjacent glyphs into the shape they collectively resemble and glides past without inspecting each letter, a phenomenon related to saccadic reading and gestalt grouping. The effect is robust across the proportional sans-serif fonts used in browsers, email clients, and chat apps — `rn` and `m` are nearly indistinguishable in Helvetica, Arial, and the default system UI fonts on macOS, Windows, and Android.

High-value targets are short, well-known brand labels containing `m` or `w`, where the cluster substitution still reads as a familiar word at a glance: `amazon`, `walmart`, `gmail`, `twitter`, `microsoft`, `meta`.

## hyphenation

Insert a single hyphen between two characters of the label. Mirrors the "company-name.com" pattern common in landing pages and phishing kits. Output: `g-oogle`, `go-ogle`, `goo-gle`, `goog-le`, `googl-e`.

## vowel_swap

Replace a vowel with another vowel. Captures phonetic mistakes and non-native-speaker spelling guesses. Output for `o`: `gaogle`, `gegogle`, `gigogle`, `gugogle` and so on, also applied to the second `o` and to `e`. False-positive rate is high, but generation is cheap and the matches that actually resolve are usually intentional squatters.

## bitsquat

Flip a single bit in the ASCII value of one character. Keep it only if the result is still a valid DNS label character (alphanumeric or hyphen). The threat model is a cosmic ray or hardware fault that flips a bit in a DNS query in flight, in DNS cache, or in a CPU register. Dinaburg's 2011 DEF CON research showed measurable traffic to bitsquat domains of high-volume brands. Defensive value is lower than for typos because the squatter cannot predict which bit will flip, but a handful of canonical bitsquat domains for big brands are still worth registering. Output for `g` (0x67): flipping each bit gives `f`, `e`, `c`, `o`, `w`, `7`, so candidates include `foogle`, `eoogle`, `coogle`, `ooogle`, `woogle`, `7oogle`.

## tld_swap

Keep the label, swap the TLD for a common alternative. The model squatter is one who couldn't get the `.com` and registered `.co`, `.io`, `.app`, `.dev`, `.xyz`, etc. instead. Built-in TLD list: `com, net, org, co, io, app, dev, cc, tv, me, info, biz, us, uk, eu, xyz, online, site, store, shop, club, page, ai`. For well-known brand names this is often the highest-yield technique; many `<brand>.io` and `<brand>.ai` lookalikes already resolve.

## doppelganger

Glue a subdomain-style prefix to the label without the separating dot, producing a valid DNS label that reads at a glance like the real subdomain. Built-in prefix list: `www, mail, login, secure, my, app, account, auth, id`. Output: `wwwgoogle.com`, `mailgoogle.com`, `logingoogle.com`, `securegoogle.com`. The Godai Group "Doppelganger Domains" study estimated that prefixes of this shape on Fortune 500 brands intercepted on the order of 20 GB of misdirected email over six months — making this a high-yield generator even when the registrant is passive.

## combosquat

Glue a phishing-kit keyword to either side of the label, with or without a separating hyphen. Built-in keyword list: `login, secure, pay, support, help, account, verify, app`. Each keyword produces four candidates per target: `<label><kw>`, `<kw><label>`, `<label>-<kw>`, `<kw>-<label>`. Output for `google`: `googlelogin.com`, `logingoogle.com`, `google-login.com`, `login-google.com`, and the analogous forms for the other keywords. Search space is bounded by design (keyword list × 4 per target), so the technique stays cheap while covering the shapes that phishing kits actually use.

## Out of scope

These attack classes exist but are deliberately not generated by the script.

*IDN and Punycode homographs* are visually identical Unicode substitutions, like Cyrillic `а` for Latin `a` or Greek `ο` for Latin `o`. Detecting them well needs a full confusables table from Unicode TR39 plus per-TLD policy (some registries refuse mixed-script labels). A separate generator would belong in its own pass.

*Sound-alike or phonetic squats* (`gewgle.com`, `gugel.com`) need a phoneme model.

*Subdomain confusion* (`google.com.evil.tld`) is a phishing-page concern, not a domain-registration one, and is not visible at the DNS-resolution layer.

*Path-based typosquatting* (`googl.ecom`) produces broken DNS labels that will not resolve.

If you need any of these, extend this playbook with a new section describing the rule, and start emitting the candidates with a fresh technique name — the helper script will accept and persist whatever technique label you choose.

## Resolution status meanings

What the `status` field on each candidate actually tells you:

- `resolves`: the system resolver returned at least one A record. This does *not* mean a squatter is active. The IP might be a registrar parking page, a CDN catch-all, or an unrelated legitimate site that happens to share the name. Always triage further with HTTP fetch, TLS cert, WHOIS, reverse DNS.
- `unregistered`: DNS authoritatively says the domain does not exist (NXDOMAIN). The candidate is currently available, or more often for valuable brands, registered but not delegated.
- `error`: timeout, SERVFAIL, or network issue. Re-run later; transient errors are common when scanning hundreds of names against a local resolver.

A status transition from `unregistered` to `resolves` between scans is the highest-signal event the memory file captures: someone registered and delegated the domain in the interval. `prev_status` and `prev_checked` are populated automatically whenever a re-check flips the status, and the run output prints a "Status transitions this run" block summarizing them. To surface fresh registrations, just run the script again — rows older than 7 days are auto-rechecked.

## The `mx` field

When a candidate resolves, the script also captures its MX records. An MX-bearing lookalike can receive email regardless of whether anyone serves an HTTP page from it, so this field is a distinct, high-value signal:

- An MX on a candidate plus an active A record is consistent with someone running a passive mail-harvester, capturing whatever misaddressed email arrives.
- An MX with a registrar's catch-all hostname (e.g. `mx*.parkingcrew.net`) is usually benign parking; an MX on the squatter's own infrastructure is not.
- Doppelganger and combosquat candidates show up with MX more often than typo candidates, matching the threat model — these are the shapes attackers register specifically for mail interception.

## An HTTP 200 is not a live site

The single most important triage lesson: **status codes cannot distinguish a phishing kit from an empty registration.** Run `scripts/browser_verify.js` on every resolving row before you call anything live. Real cases observed in a single scan, all returning HTTP 200 to `curl`:

| What curl saw | What the browser saw | Real state |
|---|---|---|
| `200`, empty body | A full storefront clone — brand logo, hero tagline, thousands of products | Client-rendered SPA kit — **the worst case, and curl misses it entirely** |
| `200` on `http://` | "`<domain>` has been recently registered with namecheap.com" + auction listings | Registrar parking |
| `200` | `Your Subscription Expired.` | Lapsed hosting panel — something *was* deployed, now dormant |
| `200` / `404` | "Application not found… the train has not arrived at the station" | Unprovisioned PaaS hostname |
| `403` | "Suspected Phishing — this website has been reported for potential phishing" | **Cloudflare already confirmed phishing** — external corroboration |

Two structural points follow:

- **Browsers try HTTPS first.** A squat with no TLS listener on `:443` fails to load for real victims even though `curl http://` returns 200. In one run, a cluster of five Namecheap-parked TLD swaps all behaved this way. `https_ok: false` is a large threat downgrade, and it is the usual explanation when a reviewer says "that link didn't work in my browser."
- **Client-side rendering inverts the signal.** An empty `curl` body on a resolving name is a reason to open a browser, not a reason to dismiss the row.

## Same-operator pivots that outperform candidate generation

Once you have one confirmed kit, these find siblings faster than generating more labels:

- **`<title>` as a fingerprint.** Kits frequently set `<title>` to a bare domain name — and often to a **sibling squat's** name. In one run two separate confirmed kits each served a title naming a *different* squat in the same family: one deploy pushed across many labels. Search that exact title string in urlscan.io and Shodan to enumerate names no generator would produce.
- **Shared origin IP.** Check the whole `/24`, and check the exact IP for co-hosted siblings. Two confirmed squats on one IP means the rest of that IP is worth enumerating via passive DNS.
- **Asset hosts.** One confirmed kit loaded its product images from `tempfile.aiquickdraw.com`, an AI-image temp host. Unusual third-party asset domains are narrow, high-signal pivots.
- **Registrar + privacy-service + nameserver tuple.** Bulk registrations of brand variants sharing a registrant fingerprint indicate an organized operator. Record the tuple when you find it so later runs can match on it.

## Do not dismiss a squat because it impersonates someone else

Operators rotate which brand a label farm serves. In one run, a typo of the scanned brand was serving a clone of a **competitor** in the same vertical, while a sibling squat self-branded as yet another name in the family. The label still targets your brand's typo traffic regardless of what the page currently shows, and the page can be repointed at your brand in minutes. Report the infrastructure, and note the current impersonation target rather than treating a non-matching brand as a false positive.

Genuine false positives look different: an unrelated legitimate business that happens to own a near-miss name (one run surfaced a real fintech company with enterprise ADFS infrastructure whose name was one omission away from the target), or a domain broker's for-sale listing. Record these on the row as `verdict: FALSE_POSITIVE` with a `verdict_note`, so future runs don't re-escalate them.

## Triage and monitoring beyond DNS

DNS resolution is a cheap first filter, not a verdict. A `resolves` row tells you a name exists; it does not tell you who is behind it or what they intend. To close the loop on a candidate, layer on:

- *Certificate Transparency logs.* Every public TLS cert issued for a domain is published to CT. Watch CT feeds (crt.sh, Google's Argon, Cloudflare's Nimbus) for newly issued certs whose SAN matches your brand's lookalike set — a fresh Let's Encrypt cert on a candidate that resolved last week is a strong signal of an imminent phishing page.
- *WHOIS and registration analytics.* Bulk registrations of brand variants across many TLDs by the same registrant, registrar, or nameserver cluster point to an organized squatter rather than a coincidence. Damerau-Levenshtein distance against your brand list is a reasonable similarity metric when sifting WHOIS bulk feeds.
- *HTTP / TLS fingerprint.* Fetch the candidate over HTTPS and look at the served cert, the body, and any redirect chain. Parked-domain templates, registrar holding pages, and phishing kits each have recognizable fingerprints.
- *Inbound traffic to your own infra.* If you operate authoritative DNS or mail servers, log query patterns for misspellings. Squatters sometimes set up catch-all MX records to harvest misdirected email — Godai Group's "Doppelganger Domains" study estimated that dotless-subdomain squats alone intercepted on the order of 20 GB of email over six months from Fortune 500 lookalikes. Misrouted internal mail is a defensive priority on its own, separate from phishing of customers.

## Who to report to: Cloudflare fronting decides

The helper records `server` and `cdn` on each probe. Use them to route abuse reports, because it determines whether anyone can actually take the content down:

- **`cdn: "cloudflare"`** (a `cf-ray` header was present) — the origin IP is hidden. File with Cloudflare abuse; the hosting provider is unreachable from outside. In the Aug 2026 run every `172.64.80.1` name fell here.
- **No `cf-ray`, real origin `server`** (`nginx/1.30.3`, `nginx/1.18.0 (Ubuntu)`) — the IP is the actual host. File with the hosting provider *and* the registrar; these are the soft targets and should be actioned first.
- **Cloudflare nameservers but no `cf-ray`** — "grey cloud": Cloudflare DNS with the proxy disabled. Two channels apply, DNS abuse at Cloudflare and hosting abuse at the origin. Check `dig NS` separately, since the HTTP headers alone will not reveal this.
- **Parking-provider `server`** (`namecheap-nginx`, GoDaddy `forsale`, HugeDomains, Bodis, ParkingCrew) — not squatter infrastructure. Note in aggregate; do not spend abuse-report effort here.
