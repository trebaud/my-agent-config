#!/usr/bin/env python3
"""render_report.py — build the markdown + HTML typosquat reports from a memory file.

Everything mechanical is derived here: summary tables, HTTP/browser state
classification, /24 clustering, status transitions, the by-technique table, the
plain actionable-names list, and the known-false-positive section. Prose that
needs judgment (why a specific candidate matters, what correlates across an
operator's infrastructure) comes from an optional annotations sidecar written by
the caller; without one, priority reasons are generated mechanically from the
rubric so the report is still complete and correct, just blunter.

Usage:
  python3 render_report.py <domain> [--annotations FILE] [--out-dir DIR]
                                    [--templates DIR] [--max-priority N]

Annotations JSON (all keys optional):
  {
    "priority": [
      {"candidate": "x.com", "tag": "Fresh registration · LIVE_CLONE",
       "reason": "Verbatim clone; title matches the real site byte for byte."}
    ],
    "fingerprints": ["Kit sets <title> to a sibling squat's domain name — ..."],
    "headline": "9 high-priority items this run."
  }

Reads  ./<domain>-typosquat-memory.json
Writes ./<domain>-typosquat-report.md and ./<domain>-typosquat-report.html
"""
import argparse
import collections
import html
import json
import os
import sys
from urllib.parse import urlparse, quote

# Browser content states, most to least urgent. Drives priority ranking, the
# plain list, and sort order everywhere.
BROWSER_ORDER = ['FLAGGED_PHISHING', 'LIVE_CLONE', 'OFFSITE_REDIRECT', 'EXPIRED_HOST',
                 'UNPROVISIONED', 'BLANK', 'BRAND_REDIRECT', 'PARKED', 'ERROR']
ACTIONABLE = {'FLAGGED_PHISHING', 'LIVE_CLONE', 'OFFSITE_REDIRECT', 'EXPIRED_HOST', 'UNPROVISIONED'}
HTTP_ORDER = ['LIVE', 'REDIRECT_OFFSITE', 'REDIRECT_TO_TARGET', 'BLOCKED',
              'SERVER_ERROR', 'NO_HTTP', 'OTHER']


def host_of(url):
    try:
        return (urlparse(url).hostname or '').lower()
    except Exception:
        return ''


def is_self(cand, h):
    return h in (cand, 'www.' + cand, '')


def http_state(c, target):
    """Curl-derived state. Superseded by browser state when one exists."""
    hs, ht = c.get('https') or {}, c.get('http') or {}
    pri = hs if hs.get('status') else ht
    if not pri.get('status'):
        return 'NO_HTTP'
    code, fh, cand = pri['status'], host_of(pri.get('final_url', '')), c['candidate']
    tgt = fh == target or fh.endswith('.' + target)
    if not is_self(cand, fh) and not tgt:
        return 'REDIRECT_OFFSITE'
    if tgt:
        return 'REDIRECT_TO_TARGET'
    if 200 <= code < 300:
        return 'LIVE'
    if 400 <= code < 500:
        return 'BLOCKED'
    if 500 <= code < 600:
        return 'SERVER_ERROR'
    return 'OTHER'


def state_of(c, target):
    """Authoritative state: browser verdict when present, else the HTTP reading."""
    b = c.get('browser') or {}
    if b.get('content'):
        return b['content'], True
    return http_state(c, target), False


def is_fresh(c):
    """New this run: NXDOMAIN→resolves, or a first-ever observation that resolves."""
    if c.get('status') != 'resolves':
        return False
    prev = c.get('prev_status')
    if prev in ('unregistered', ''):
        return True
    # A row whose first_seen equals its last_checked was observed for the first
    # time on this run.
    return bool(c.get('first_seen')) and c.get('first_seen') == c.get('last_checked')


def mx(c):
    return '[MX]' if c.get('mx') else ''


def no_https(c):
    b = c.get('browser') or {}
    return b.get('https_ok') is False


def cdn_of(c):
    for k in ('https', 'http'):
        o = c.get(k) or {}
        if o.get('cdn'):
            return o['cdn']
    return ''


def server_of(c):
    for k in ('https', 'http'):
        o = c.get(k) or {}
        if o.get('server'):
            return o['server']
    return ''


def probe_md(c):
    out = []
    for scheme in ('https', 'http'):
        o = c.get(scheme)
        if not o:
            continue
        if o.get('status'):
            fh = host_of(o.get('final_url', ''))
            suffix = ' (self)' if is_self(c['candidate'], fh) else f'→{fh}'
            out.append(f"`{scheme}={o['status']}{suffix}`")
        else:
            out.append(f"`{scheme}={o.get('error', 'no response')}`")
    if server_of(c):
        out.append(f'`server={server_of(c)}`')
    if cdn_of(c):
        out.append('`cloudflare`')
    return ' · '.join(out)


def probe_html(c):
    parts = []
    for scheme in ('https', 'http'):
        o = c.get(scheme)
        if not o:
            continue
        if o.get('status'):
            code = o['status']
            cls = 'ok' if 200 <= code < 300 else 'redir' if 300 <= code < 400 else 'err'
            fh = host_of(o.get('final_url', ''))
            suffix = (' (self)' if is_self(c['candidate'], fh)
                      else f' → <code>{html.escape(fh)}</code>')
            parts.append(f'{scheme}=<span class="{cls}">{code}</span>{suffix}')
        else:
            parts.append(f'{scheme}=<span class="err">{html.escape(o.get("error", "no response"))}</span>')
    if server_of(c):
        parts.append(f'server=<code>{html.escape(server_of(c))}</code>')
    if cdn_of(c):
        parts.append('<code>cloudflare</code>')
    return '<span class="sep">·</span>'.join(parts)


def evidence_md(c, with_state=True):
    """Browser evidence line: what a human actually saw.

    `with_state` is False where the caller already prints the state tag, so the
    same label is not repeated twice on adjacent lines.
    """
    b = c.get('browser') or {}
    if not b.get('content'):
        return ''
    bits = [f"**`{b['content']}`**"] if with_state else []
    if no_https(c):
        bits.append('`[NO-HTTPS]`')
    if b.get('title'):
        bits.append(f"title `{b['title'][:90]}`")
    fh = host_of(b.get('final_url', ''))
    if fh and not is_self(c['candidate'], fh):
        bits.append(f'→ `{fh}`')
    return ' · '.join(bits)


def evidence_html(c):
    b = c.get('browser') or {}
    if not b.get('content'):
        return ''
    bits = [f'<span class="state-tag state-{b["content"]}">{b["content"]}</span>']
    if no_https(c):
        bits.append('<span class="nohttps">NO-HTTPS</span>')
    if b.get('title'):
        bits.append(f'title <code>{html.escape(b["title"][:90])}</code>')
    fh = host_of(b.get('final_url', ''))
    if fh and not is_self(c['candidate'], fh):
        bits.append(f'→ <code>{html.escape(fh)}</code>')
    return '<div class="evidence">' + ' '.join(bits) + '</div>'


def links_md(c):
    q = c['candidate']
    return (f'[visit](https://{q}) · [crt.sh](https://crt.sh/?q={q}) · '
            f'[VT](https://www.virustotal.com/gui/domain/{q}/detection) · '
            f'[urlscan](https://urlscan.io/domain/{q}) · [whois](https://who.is/whois/{q})')


def links_html(c):
    q = quote(c['candidate'], safe='')
    pairs = [('visit', f'https://{q}'), ('crt.sh', f'https://crt.sh/?q={q}'),
             ('VT', f'https://www.virustotal.com/gui/domain/{q}/detection'),
             ('urlscan', f'https://urlscan.io/domain/{q}'),
             ('whois', f'https://who.is/whois/{q}')]
    return ('<span class="links">'
            + ''.join(f'<a href="{u}" target="_blank" rel="noopener noreferrer">{n}</a>'
                      for n, u in pairs) + '</span>')


def auto_reason(c, target, state, verified):
    """Mechanical reason line, used when no annotation supplies a better one."""
    b = c.get('browser') or {}
    bits = []
    if state == 'FLAGGED_PHISHING':
        bits.append('an interstitial reports this as phishing — externally confirmed')
    elif state == 'LIVE_CLONE':
        bits.append('renders its own content in a browser')
    elif state == 'OFFSITE_REDIRECT':
        bits.append(f'redirects to `{host_of(b.get("final_url", "")) or "another host"}`')
    elif state == 'EXPIRED_HOST':
        bits.append('serves a lapsed-hosting notice — a kit was deployed here')
    elif state == 'UNPROVISIONED':
        bits.append('hostname provisioned on a platform with nothing deployed')
    elif state == 'LIVE':
        bits.append('HTTP 2xx from its own host (not browser-verified — may be parking)')
    elif state == 'NO_HTTP':
        bits.append('resolves with no HTTP service on either scheme')
    else:
        bits.append(f'state {state}')
    if c.get('mx'):
        bits.append('mail-capable (MX present)')
    if no_https(c):
        bits.append('no TLS listener, so it fails in a real browser')
    if cdn_of(c) == 'cloudflare':
        bits.append('Cloudflare-shielded — file abuse with Cloudflare')
    elif server_of(c):
        bits.append(f'origin `{server_of(c)}` is directly reachable')
    if not verified:
        bits.append('**not browser-verified**')
    return '; '.join(bits) + '.'


def priority_rank(c, target):
    """Sort key for the priority block, most urgent first.

    A browser-verified actionable row always outranks an unverified one, no
    matter how alive the status code makes it look: unverified `LIVE` is the
    state most likely to be registrar parking, and letting it compete with
    confirmed kits is what floods the block with noise.
    """
    state, verified = state_of(c, target)
    order = BROWSER_ORDER if state in BROWSER_ORDER else HTTP_ORDER
    idx = order.index(state) if state in order else 99
    tier = 0 if (verified and state in ACTIONABLE) else (1 if verified else 2)
    return (tier, 0 if is_fresh(c) else 1, idx, 0 if c.get('mx') else 1, c['candidate'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('domain')
    ap.add_argument('--annotations', help='JSON sidecar with LLM-authored priority reasons and fingerprints')
    ap.add_argument('--out-dir', default='.')
    ap.add_argument('--templates',
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references'))
    ap.add_argument('--max-priority', type=int, default=10,
                    help='cap named priority items (0 = no cap). Default 10 keeps the block readable; '
                         'the rest roll up into the cluster breakdown.')
    a = ap.parse_args()

    safe = a.domain.replace('.', '_')
    mem_path = os.path.join(a.out_dir, f'{safe}-typosquat-memory.json')
    if not os.path.exists(mem_path):
        sys.exit(f'error: {mem_path} not found')
    mem = json.load(open(mem_path))
    target = (mem.get('target') or a.domain).lower()
    cands = mem['candidates']
    by = {c['candidate']: c for c in cands}
    ann = json.load(open(a.annotations)) if a.annotations else {}

    stats = mem.get('stats', {})
    fp_rows = [c for c in cands if c.get('verdict') == 'FALSE_POSITIVE']
    fp_names = {c['candidate'] for c in fp_rows}
    res = [c for c in cands if c.get('status') == 'resolves' and c['candidate'] not in fp_names]

    # ---- state tallies
    b_counts = collections.Counter()
    h_counts = collections.Counter()
    for c in res:
        st, verified = state_of(c, target)
        (b_counts if verified else h_counts)[st] += 1
    verified_n = sum(b_counts.values())

    # ---- priority set
    ann_priority = ann.get('priority') or []
    if ann_priority:
        prio = [(p.get('tag', ''), by[p['candidate']], p.get('reason', ''))
                for p in ann_priority if p.get('candidate') in by]
    else:
        pool = sorted(res, key=lambda c: priority_rank(c, target))
        pool = [c for c in pool
                if state_of(c, target)[0] in ACTIONABLE
                or (state_of(c, target)[0] in ('LIVE', 'NO_HTTP') and (not (c.get('browser') or {}).get('content')))
                or (state_of(c, target)[0] == 'NO_HTTP' and c.get('mx'))]
        if a.max_priority:
            pool = pool[:a.max_priority]
        prio = []
        for c in pool:
            st, verified = state_of(c, target)
            tag = ('Fresh registration · ' if is_fresh(c) else '') + st
            prio.append((tag, c, auto_reason(c, target, st, verified)))
    prio_names = {c['candidate'] for _, c, _ in prio}

    # ---- plain actionable list
    plain = [c['candidate'] for c in sorted(res, key=lambda c: priority_rank(c, target))
             if state_of(c, target)[0] in ACTIONABLE]

    # ---- clusters by /24
    clusters = collections.defaultdict(list)
    for c in res:
        ip = c.get('ip', '')
        key = '.'.join(ip.split('.')[:3]) + '.0/24' if ip.count('.') == 3 else (ip or 'no-ip')
        clusters[key].append(c)
    for v in clusters.values():
        v.sort(key=lambda c: c['candidate'])
    ordered = sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    # ---- transitions
    trans = sorted([c for c in cands
                    if c.get('prev_status') is not None and c.get('prev_status') != c.get('status')],
                   key=lambda c: c['candidate'])

    # ---- by technique
    tech = collections.defaultdict(collections.Counter)
    for c in cands:
        t = c.get('technique', '')
        tech[t][c.get('status') or 'pending'] += 1
        tech[t]['total'] += 1
    trows = sorted(tech.items(), key=lambda kv: (-kv[1]['resolves'], -kv[1]['total'], kv[0]))

    fingerprints = ann.get('fingerprints') or []
    n_unverified_prio = sum(1 for _, c, _ in prio if not state_of(c, target)[1])
    headline = ann.get('headline') or f'{len(prio)} item(s) need attention this run.'
    # Never let an unverified row masquerade as a confirmed finding.
    unverified_warning = (
        f'{n_unverified_prio} of these are **not browser-verified** — an HTTP 2xx from a '
        f'parking provider is indistinguishable from a live kit at this layer. Run '
        f'`browser_verify.js` before acting on them.' if n_unverified_prio else '')

    # =================================================================== markdown
    m = [f'# Typosquat scan: {target}\n',
         f"_Generated {mem.get('last_run', '')} — run #{mem.get('run_count', 0)}_\n",
         '## Summary\n',
         '| Metric | Count |\n|---|---:|',
         f"| Candidates tracked | {stats.get('total', 0)} |",
         f"| Resolving (registered, DNS active) | {stats.get('resolving', 0)} |",
         f"| Unregistered (NXDOMAIN — available) | {stats.get('unregistered', 0)} |",
         f"| Lookup errors (retry next run) | {stats.get('errors', 0)} |\n"]
    if stats.get('errors'):
        m.append(f"> **{stats['errors']} rows errored** — this scan is incomplete. "
                 f"Re-run at lower `-workers` before acting on it.\n")
    if verified_n:
        m.append('| Browser content state | Count |\n|---|---:|')
        for k in BROWSER_ORDER:
            if b_counts.get(k):
                m.append(f'| `{k}` | {b_counts[k]} |')
        m.append('')
        if h_counts:
            m.append(f'_{sum(h_counts.values())} resolving row(s) are **not** browser-verified; '
                     f'their state is curl-derived and may misread parking as live._\n')
    else:
        m.append('_No rows browser-verified this run — every content state below is curl-derived '
                 'and may misread parking pages as live or miss client-rendered kits entirely._\n')

    m.append('## Recommended next steps\n')
    m.append(f'**{headline}**\n' if prio else '_No resolving candidates this run — nothing to action._\n')
    if unverified_warning:
        m.append(f'> {unverified_warning}\n')
    for tag, c, reason in prio:
        st, _ = state_of(c, target)
        ev = evidence_md(c, with_state=False)
        m.append(f"- **{tag}:** `{c['candidate']}` → `{c.get('ip', '')}` "
                 f"_({c.get('technique', '')})_ {mx(c)} **`{st}`**  \n  {reason}  \n"
                 + (f'  {ev}  \n' if ev else '')
                 + f'  {links_md(c)}\n')
    rest = len(res) - len(prio_names)
    if rest > 0:
        m.append(f'_{rest} other resolving candidate(s) are registrar parking, CDN catch-alls, '
                 f'or otherwise inert — see the cluster breakdown below._\n')

    m.append('## Actionable names (plain list)\n')
    m.append('```\n' + ('\n'.join(plain) if plain else '(none)') + '\n```\n')

    if fingerprints:
        m.append('## Same-operator fingerprints\n')
        m.extend(f'- {f}\n' for f in fingerprints)

    if fp_rows:
        m.append('## Known false positives\n')
        m.append('_Recorded so later runs do not re-escalate them._\n')
        for c in fp_rows:
            m.append(f"- `{c['candidate']}` → `{c.get('ip', '')}` — "
                     f"{c.get('verdict_note', 'no note recorded')}")
        m.append('')

    m.append(f"## Resolving candidates ({len(res)})\n")
    m.append('Grouped by `/24` so parking-provider clusters collapse into a single block. '
             '`[MX]` means the name can receive email. The `https=`/`http=` line is the raw probe; '
             'the line under it is the browser verdict, which overrides it.\n')
    if not res:
        m.append('_None._\n')
    for key, group in ordered:
        if len(group) > 1:
            m.append(f'- **Cluster {key}** ({len(group)} names on shared infrastructure):')
            for c in group:
                st, _ = state_of(c, target)
                m.append(f"  - `{c['candidate']}` → `{c.get('ip', '')}` _({c.get('technique', '')})_ "
                         f"{mx(c)} **`{st}`**  \n    {probe_md(c)}  \n"
                         + (f'    {evidence_md(c)}  \n' if evidence_md(c) else '')
                         + f'    {links_md(c)}')
            m.append('')
        else:
            c = group[0]
            st, _ = state_of(c, target)
            m.append(f"- `{c['candidate']}` → `{c.get('ip', '')}` _({c.get('technique', '')})_ "
                     f"{mx(c)} **`{st}`**  \n  {probe_md(c)}  \n"
                     + (f'  {evidence_md(c)}  \n' if evidence_md(c) else '')
                     + f'  {links_md(c)}\n')

    if trans:
        m.append(f'## Status transitions this run ({len(trans)})\n')
        for c in trans:
            line = f"- `{c['candidate']}`: {c.get('prev_status') or 'new'} → **{c.get('status')}** {mx(c)}"
            if c.get('status') == 'resolves':
                st, _ = state_of(c, target)
                line += f"  **`{st}`**  \n  {probe_md(c)}  \n  {links_md(c)}"
            m.append(line)
        m.append('')

    m.append('## By technique\n')
    m.append('| Technique | Total | Resolving | Unregistered | Errors |\n|---|---:|---:|---:|---:|')
    for t, cnt in trows:
        m.append(f"| {t} | {cnt['total']} | {cnt['resolves']} | {cnt['unregistered']} | {cnt['error']} |")
    m.append('')

    m.append('## Notes\n')
    m.append('- `resolves` ≠ active squatter. Most resolving lookalikes are registrar parking or CDN '
             'catch-alls. Triage out-of-band (WHOIS, TLS cert SAN, reverse DNS, CT-log history).')
    m.append('- **An HTTP 200 is not a live site.** Rows with a browser state were rendered in real '
             'Chromium; that state overrides the status-code reading. Rows without one may misreport '
             'parking as live and miss client-rendered kits entirely.')
    m.append('- `[NO-HTTPS]` means no TLS listener on `:443`. Browsers try HTTPS first, so these names '
             'fail for real visitors even when `curl http://` returns 200.')
    m.append('- `[MX]` is a stronger phishing/mail-interception signal than HTTP-only, and is the one '
             'case where a name with no web service still deserves high priority.')
    m.append('- `cloudflare` on a row means the origin is shielded — file abuse with Cloudflare. A real '
             '`server` header with no `cf-ray` means the hosting provider is directly reachable.')
    m.append('- A squat impersonating a *different* brand is still a squat on this brand\'s typo traffic '
             'and can be repointed in minutes. It is not a false positive.')
    md_path = os.path.join(a.out_dir, f'{safe}-typosquat-report.md')
    open(md_path, 'w').write('\n'.join(m) + '\n')

    # ======================================================================= html
    tpl = open(os.path.join(a.templates, 'report_template.html')).read()

    pb = [f'<p><strong>{html.escape(headline)}</strong></p>'] if prio else \
         ['<p><em>No resolving candidates this run — nothing to action.</em></p>']
    if unverified_warning:
        pb.append('<p class="reason">' + unverified_warning.replace('**', '') + '</p>')
    if stats.get('errors'):
        pb.insert(0, f'<p><strong>{stats["errors"]} rows errored — this scan is incomplete.</strong> '
                     f'Re-run at lower <code>-workers</code> before acting on it.</p>')
    for tag, c, reason in prio:
        st, _ = state_of(c, target)
        pb.append(
            f'<div class="item"><span class="tag">{html.escape(tag)}</span> '
            f'<code>{html.escape(c["candidate"])}</code> → <code>{html.escape(c.get("ip", ""))}</code> '
            f'<span class="tech">({html.escape(c.get("technique", ""))})</span> '
            + (f'<span class="mx">{mx(c)}</span>' if c.get('mx') else '')
            + f'<span class="state-tag state-{st}">{st}</span>'
            + (' <span class="nohttps">NO-HTTPS</span>' if no_https(c) else '')
            + f'<span class="reason">{reason}</span>{links_html(c)}</div>')
    if rest > 0:
        pb.append(f'<div class="rollup">{rest} other resolving candidate(s) are registrar parking, '
                  f'CDN catch-alls, or otherwise inert — see the cluster breakdown below.</div>')

    def row_html(c):
        st, _ = state_of(c, target)
        return (f'<div class="row"><code>{html.escape(c["candidate"])}</code>'
                f'<code>{html.escape(c.get("ip", ""))}</code>'
                f'<span class="tech">{html.escape(c.get("technique", ""))}</span>'
                + (f'<span class="mx">{mx(c)}</span>' if c.get('mx') else '<span></span>')
                + f'<span class="state-tag state-{st}">{st}</span></div>'
                f'<div class="http">{probe_html(c)}</div>{evidence_html(c)}{links_html(c)}')

    rb = []
    if not res:
        rb.append('<p><em>None.</em></p>')
    for key, group in ordered:
        if len(group) > 1:
            rb.append(f'<div class="cluster"><h3>Cluster {html.escape(key)} — {len(group)} names on '
                      f'shared infrastructure</h3>' + ''.join(row_html(c) for c in group) + '</div>')
        else:
            rb.append(row_html(group[0]))

    tb = []
    for c in trans:
        st, _ = state_of(c, target)
        tb.append(f'<div class="transition"><code>{html.escape(c["candidate"])}</code>: '
                  f'{html.escape(c.get("prev_status") or "new")} <span class="arrow">→</span> '
                  f'<span class="new">{html.escape(c.get("status", ""))}</span> '
                  + (f'<span class="mx">{mx(c)}</span>' if c.get('mx') else '')
                  + (f'<span class="state-tag state-{st}">{st}</span>' if c.get('status') == 'resolves' else '')
                  + '</div>')
        if c.get('status') == 'resolves':
            tb.append(f'<div class="http">{probe_html(c)}</div>{links_html(c)}')

    tr = ''.join(f'<tr><td>{html.escape(t)}</td><td class="num">{cnt["total"]}</td>'
                 f'<td class="num">{cnt["resolves"]}</td><td class="num">{cnt["unregistered"]}</td>'
                 f'<td class="num">{cnt["error"]}</td></tr>' for t, cnt in trows)

    fb = ('<ul>' + ''.join(f'<li>{f}</li>' for f in fingerprints) + '</ul>') if fingerprints else ''
    fpb = ''.join(f'<div class="fp"><code>{html.escape(c["candidate"])}</code> → '
                  f'<code>{html.escape(c.get("ip", ""))}</code> — '
                  f'{html.escape(c.get("verdict_note", "no note recorded"))}</div>'
                  for c in fp_rows)

    state_table = ''
    if verified_n:
        state_table = ('<h2>Browser content state</h2><table>'
                       '<tr><th>State</th><th class="num">Count</th></tr>'
                       + ''.join(f'<tr><td><span class="state-tag state-{k}">{k}</span></td>'
                                 f'<td class="num">{b_counts[k]}</td></tr>'
                                 for k in BROWSER_ORDER if b_counts.get(k))
                       + '</table>')
        if h_counts:
            state_table += (f'<p><em>{sum(h_counts.values())} resolving row(s) are <strong>not</strong> '
                            f'browser-verified; their state is curl-derived and may misread parking as '
                            f'live.</em></p>')
    else:
        state_table = ('<p><em>No rows browser-verified this run — every content state below is '
                       'curl-derived and may misread parking pages as live or miss client-rendered '
                       'kits entirely.</em></p>')

    out = tpl
    for k, v in {
        '{{TARGET}}': html.escape(target),
        '{{LAST_RUN}}': html.escape(mem.get('last_run', '')),
        '{{RUN_COUNT}}': str(mem.get('run_count', 0)),
        '{{STATS_TOTAL}}': str(stats.get('total', 0)),
        '{{STATS_RESOLVING}}': str(stats.get('resolving', 0)),
        '{{STATS_UNREGISTERED}}': str(stats.get('unregistered', 0)),
        '{{STATS_ERRORS}}': str(stats.get('errors', 0)),
        '{{PRIORITY_BLOCK}}': '\n'.join(pb),
        '{{PLAIN_LIST}}': html.escape('\n'.join(plain)) if plain else '(none)',
        '{{FINGERPRINTS_BLOCK}}': fb,
        '{{FALSE_POSITIVES_BLOCK}}': fpb,
        '{{RESOLVING_BLOCK}}': '\n'.join(rb),
        '{{N_TRANSITIONS}}': str(len(trans)),
        '{{TRANSITIONS_BLOCK}}': '\n'.join(tb),
        '{{TECHNIQUE_ROWS}}': tr,
    }.items():
        out = out.replace(k, v)
    out = out.replace('<div class="priority">', state_table + '\n<div class="priority">')
    # Drop sections whose content is empty rather than leaving a bare heading.
    if not fingerprints:
        out = out.replace('<h2>Same-operator fingerprints</h2>\n', '')
    if not fp_rows:
        out = out.replace('<h2>Known false positives</h2>\n', '')
    if not trans:
        out = out.replace('<h2>Status transitions this run (0)</h2>\n', '')

    html_path = os.path.join(a.out_dir, f'{safe}-typosquat-report.html')
    open(html_path, 'w').write(out)

    left = [k for k in ('{{', '}}') if k in out]
    print(f'{md_path}\n{html_path}', file=sys.stderr)
    print(f'  {len(res)} resolving, {len(prio)} priority, {len(plain)} actionable, '
          f'{len(trans)} transitions, {verified_n} browser-verified', file=sys.stderr)
    if left:
        print('  WARNING: unsubstituted template placeholders remain', file=sys.stderr)


if __name__ == '__main__':
    main()
