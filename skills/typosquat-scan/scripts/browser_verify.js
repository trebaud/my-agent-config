#!/usr/bin/env node
/**
 * browser_verify.js — render resolving typosquat candidates in a real browser
 * and classify what a human would actually see.
 *
 * WHY THIS EXISTS
 * An HTTP status code cannot distinguish a phishing kit from a parking page.
 * Observed failure modes that all return 200 to curl:
 *   - registrar parking ("<domain> has been recently registered with namecheap.com")
 *   - a lapsed hosting panel serving only "Your Subscription Expired."
 *   - an unprovisioned PaaS hostname ("Application not found")
 * And the inverse: a client-rendered SPA phishing kit returns an *empty* shell
 * to curl while rendering a full storefront in a browser.
 *
 * Separately, browsers try HTTPS first. A squat with no TLS listener on :443
 * fails to load for real victims even though `curl http://` returns 200 — so
 * `https_ok: false` materially downgrades a candidate's threat.
 *
 * Reads  ./<domain>-typosquat-memory.json
 * Writes the `browser` object back onto each row it verifies, and PNGs to
 * ./<domain>-typosquat-shots/.
 *
 * Usage:
 *   node browser_verify.js <domain> [--all] [--limit N] [--only substr]
 *                                   [--stale-days N] [--headed] [--concurrency N]
 *
 *   (default: verify resolving rows that have no browser verdict, or one
 *    older than --stale-days, capped at --limit)
 *
 * Requires playwright. If `require('playwright')` fails, run `npm i playwright`
 * in any directory and re-run with NODE_PATH set, or `npx playwright install
 * chromium` once. Chromium resolution falls back to scanning the local
 * playwright browser cache, so a library/browser version mismatch (a common
 * failure after `npm i playwright` pulls a newer build than the cache holds)
 * does not block the run.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// ---------------------------------------------------------------- playwright
function loadPlaywright() {
  for (const m of ['playwright', 'playwright-core']) {
    try { return require(m); } catch (_) { /* try next */ }
  }
  console.error(
    'error: playwright not found.\n' +
    '  npm i playwright   (then re-run, or set NODE_PATH=<dir>/node_modules)\n' +
    'Chromium itself is reused from the playwright cache if present.');
  process.exit(1);
}

/**
 * Resolve a chromium binary. Playwright's bundled default is tried first via
 * launch(); this is the fallback used when the installed library expects a
 * browser build the cache does not have.
 */
function findCachedChromium() {
  const roots = [
    path.join(os.homedir(), 'Library/Caches/ms-playwright'),
    path.join(os.homedir(), '.cache/ms-playwright'),
    process.env.PLAYWRIGHT_BROWSERS_PATH,
  ].filter(Boolean);
  const rels = [
    'chrome-headless-shell-mac-arm64/chrome-headless-shell',
    'chrome-headless-shell-mac-x64/chrome-headless-shell',
    'chrome-headless-shell-linux/chrome-headless-shell',
    'chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium',
    'chrome-mac/Chromium.app/Contents/MacOS/Chromium',
    'chrome-linux/chrome',
  ];
  for (const root of roots) {
    let entries = [];
    try { entries = fs.readdirSync(root); } catch (_) { continue; }
    // Highest build number first so we prefer the newest cached browser.
    entries.sort((a, b) => (parseInt(b.split('-').pop(), 10) || 0) - (parseInt(a.split('-').pop(), 10) || 0));
    for (const e of entries) {
      if (!/^chromium/.test(e)) continue;
      for (const rel of rels) {
        const p = path.join(root, e, rel);
        if (fs.existsSync(p)) return p;
      }
    }
  }
  return null;
}

// ---------------------------------------------------------------------- args
const argv = process.argv.slice(2);
const domain = argv.find(a => !a.startsWith('-'));
if (!domain) {
  console.error('usage: node browser_verify.js <domain> [--all] [--limit N] [--only substr] [--stale-days N] [--headed] [--concurrency N]');
  process.exit(2);
}
const flag = (name, dflt) => {
  const i = argv.indexOf('--' + name);
  return i === -1 ? dflt : argv[i + 1];
};
const has = name => argv.includes('--' + name);

const LIMIT = parseInt(flag('limit', '40'), 10);
const STALE_DAYS = parseInt(flag('stale-days', '7'), 10);
const ONLY = flag('only', null);
const CONCURRENCY = Math.max(1, parseInt(flag('concurrency', '4'), 10));
const HEADED = has('headed');
const ALL = has('all');

const MEM = path.join(process.cwd(), domain.replace(/\./g, '_') + '-typosquat-memory.json');
const SHOTS = path.join(process.cwd(), domain.replace(/\./g, '_') + '-typosquat-shots');

if (!fs.existsSync(MEM)) {
  console.error(`error: ${MEM} not found. Run typosquat_scan first.`);
  process.exit(1);
}
fs.mkdirSync(SHOTS, { recursive: true });

// ------------------------------------------------------------ classification
// Ordered most-specific first. Each pattern was derived from real observed
// pages, not guessed — add to these lists as new provider templates show up.
// A third party (Cloudflare, Google Safe Browsing, the registrar) has already
// judged this domain malicious and is serving an interstitial instead of the
// kit. This is the STRONGEST signal in the whole pipeline — external
// confirmation of phishing — so it is tested before every other pattern.
const FLAGGED_PHISHING = /(suspected phishing|reported for (potential )?phishing|deceptive site ahead|dangerous site|malware ahead|phishing warning|this site has been blocked|suspected malware|domain has been (seized|suspended) )/i;
const PARKED = /(has been recently registered|is registered at|\bis for sale\b|domain (is )?for sale|buy this domain|this domain (is|may be) (for sale|available)|make an offer|parked (free )?(at|by)|domain parking|see all auctions|inquire about this domain|godaddy|afternic|sedo|dan\.com|spaceship\.com|namecheap\.com|hugedomains|bodis|parkingcrew|above\.com)/i;
const EXPIRED = /(subscription (has )?expired|account (has been )?suspended|service (has )?expired|hosting (has )?expired|this site is temporarily unavailable|account is on hold)/i;
const UNPROVISIONED = /(application not found|no such app|train has not arrived|has not been provisioned|deployment not found|project not found|there('| i)?s nothing here|default backend|welcome to nginx|apache2 (ubuntu )?default page|it works!|future home of something quite cool)/i;

function hostOf(u) {
  try { return new URL(u).hostname.toLowerCase(); } catch (_) { return ''; }
}

/**
 * Classify a rendered page. `target` is the brand being protected.
 * Returns one of:
 *   FLAGGED_PHISHING — an interstitial says this is phishing: externally confirmed
 *   LIVE_CLONE       — renders its own substantive content: triage as a kit
 *   PARKED           — registrar/parking template
 *   EXPIRED_HOST     — hosting account lapsed (but something WAS deployed here)
 *   UNPROVISIONED    — hostname points at a platform with nothing deployed
 *   BRAND_REDIRECT   — lands on the protected brand (often defensive reg)
 *   OFFSITE_REDIRECT — lands on an unrelated third party (skim / affiliate)
 *   BLANK            — loads but renders essentially nothing
 *   ERROR            — did not load on either scheme
 */
function classify({ candidate, target, finalUrl, title, text }) {
  const fh = hostOf(finalUrl);
  const selfHost = fh === candidate || fh === 'www.' + candidate || fh === '';
  const isTarget = fh === target || fh.endsWith('.' + target);
  const blob = `${title}\n${text}`;

  if (FLAGGED_PHISHING.test(blob)) return 'FLAGGED_PHISHING';
  if (isTarget) return 'BRAND_REDIRECT';
  // A parking template that redirects to www.<self> is still parking, so check
  // content before treating an offsite host as the deciding signal.
  if (PARKED.test(blob)) return 'PARKED';
  if (EXPIRED.test(blob)) return 'EXPIRED_HOST';
  if (UNPROVISIONED.test(blob)) return 'UNPROVISIONED';
  if (!selfHost) return 'OFFSITE_REDIRECT';
  if (text.replace(/\s/g, '').length < 20) return 'BLANK';
  return 'LIVE_CLONE';
}

// ---------------------------------------------------------------------- main
(async () => {
  const { chromium } = loadPlaywright();
  const mem = JSON.parse(fs.readFileSync(MEM, 'utf8'));
  const target = (mem.target || domain).toLowerCase();
  const brandLabel = target.split('.')[0];

  const staleBefore = Date.now() - STALE_DAYS * 864e5;
  let queue = mem.candidates.filter(c => c.status === 'resolves');
  if (ONLY) queue = queue.filter(c => c.candidate.includes(ONLY));
  if (!ALL) {
    queue = queue.filter(c => {
      if (!c.browser || !c.browser.checked) return true;
      const t = Date.parse(c.browser.checked);
      return !t || t < staleBefore;
    });
  }
  // Unverified rows first, then oldest verdict first.
  queue.sort((a, b) => (a.browser?.checked || '').localeCompare(b.browser?.checked || ''));
  const skipped = Math.max(0, queue.length - LIMIT);
  queue = queue.slice(0, LIMIT);

  if (!queue.length) {
    console.error('Nothing to verify. Use --all to re-verify every resolving row.');
    return;
  }
  console.error(`Verifying ${queue.length} resolving row(s) for ${target} in a real browser` +
    (skipped ? ` (${skipped} over --limit ${LIMIT} not verified this run)` : '') +
    ` at concurrency ${CONCURRENCY}`);

  const launchOpts = { headless: !HEADED };
  let browser;
  try {
    browser = await chromium.launch(launchOpts);
  } catch (e) {
    const exe = findCachedChromium();
    if (!exe) throw e;
    console.error(`  (bundled browser unavailable; using cached ${path.basename(path.dirname(exe))})`);
    browser = await chromium.launch({ ...launchOpts, executablePath: exe });
  }

  /** Navigate one candidate, https first then http, and capture what rendered. */
  async function verify(c) {
    const ctx = await browser.newContext({
      viewport: { width: 1280, height: 900 },
      ignoreHTTPSErrors: true, // squats routinely have bad certs; we still want the page
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
        '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    });
    const page = await ctx.newPage();
    const out = { scheme: '', status: 0, finalUrl: '', title: '', text: '', httpsOk: false, err: '' };

    for (const scheme of ['https', 'http']) {
      try {
        const resp = await page.goto(`${scheme}://${c.candidate}`,
          { waitUntil: 'domcontentloaded', timeout: 30000 });
        // Client-rendered kits need a beat to hydrate before title/text mean anything.
        await page.waitForTimeout(3500);
        out.scheme = scheme;
        out.status = resp ? resp.status() : 0;
        out.finalUrl = page.url();
        out.title = ((await page.title()) || '').trim().slice(0, 200);
        out.text = ((await page.evaluate(() => (document.body ? document.body.innerText : '')) || '')
          .replace(/\s+/g, ' ').trim().slice(0, 240));
        if (scheme === 'https') out.httpsOk = true;
        out.err = '';
        break;
      } catch (e) {
        out.err = String(e.message || e).split('\n')[0].slice(0, 140);
        // Fall through to http:// — this is the parked-domain case where :443
        // simply has no listener. Anything else is also worth one http retry.
      }
    }

    let shot = '';
    if (out.scheme) {
      shot = path.join(SHOTS, `${c.candidate}.png`);
      try { await page.screenshot({ path: shot }); } catch (_) { shot = ''; }
    }
    await ctx.close();

    const content = out.scheme
      ? classify({ candidate: c.candidate, target, finalUrl: out.finalUrl, title: out.title, text: out.text })
      : 'ERROR';

    c.browser = {
      content,
      scheme: out.scheme || undefined,
      https_ok: out.httpsOk,
      status: out.status || undefined,
      final_url: out.finalUrl || undefined,
      title: out.title || undefined,
      text: out.text || undefined,
      screenshot: shot ? path.relative(process.cwd(), shot) : undefined,
      error: out.scheme ? undefined : out.err,
      checked: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    };
    return c;
  }

  // Bounded-concurrency worker pool.
  let next = 0;
  const done = [];
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, queue.length) }, async () => {
    while (next < queue.length) {
      const c = queue[next++];
      try { done.push(await verify(c)); } catch (e) {
        c.browser = { content: 'ERROR', error: String(e.message || e).slice(0, 140),
          checked: new Date().toISOString().replace(/\.\d+Z$/, 'Z') };
        done.push(c);
      }
    }
  }));

  await browser.close();

  // Atomic write — never leave a half-written memory file behind.
  const tmp = MEM + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(mem, null, 2));
  fs.renameSync(tmp, MEM);

  // ------------------------------------------------------------- terminal out
  const order = ['FLAGGED_PHISHING', 'LIVE_CLONE', 'OFFSITE_REDIRECT', 'EXPIRED_HOST',
    'UNPROVISIONED', 'BLANK', 'BRAND_REDIRECT', 'PARKED', 'ERROR'];
  done.sort((a, b) => order.indexOf(a.browser.content) - order.indexOf(b.browser.content) ||
    a.candidate.localeCompare(b.candidate));

  // --quiet prints only the actionable names, one per line, priority-ordered —
  // the skill's output contract. Everything diagnostic goes to stderr so the
  // stdout stream stays copy-pasteable into a ticket or blocklist.
  const ACTIONABLE = new Set(['FLAGGED_PHISHING', 'LIVE_CLONE', 'OFFSITE_REDIRECT',
    'EXPIRED_HOST', 'UNPROVISIONED']);
  if (has('quiet')) {
    const names = done
      .filter(c => ACTIONABLE.has(c.browser.content) && c.verdict !== 'FALSE_POSITIVE')
      .map(c => c.candidate);
    for (const n of names) console.log(n);
    const tmpCounts = {};
    for (const c of done) tmpCounts[c.browser.content] = (tmpCounts[c.browser.content] || 0) + 1;
    console.error(`(${names.length} actionable of ${done.length} verified — ` +
      order.filter(k => tmpCounts[k]).map(k => `${k}=${tmpCounts[k]}`).join(' ') + ')');
    return;
  }

  const counts = {};
  for (const c of done) counts[c.browser.content] = (counts[c.browser.content] || 0) + 1;

  console.log(`\nBrowser verdicts for ${target} (${done.length} rows):`);
  for (const c of done) {
    const b = c.browser;
    const tls = b.https_ok ? '' : '  [NO-HTTPS]';
    // A kit that titles itself with a bare domain name — often a *sibling*
    // squat's name — is a strong one-operator-many-labels tell.
    const kit = b.title && /^[a-z0-9-]+\.[a-z]{2,}$/i.test(b.title.trim()) ? '  [TITLE=DOMAIN]' : '';
    const brand = b.text && new RegExp(brandLabel, 'i').test(b.text) ? '  [BRAND-TEXT]' : '';
    console.log(`  ${c.candidate.padEnd(26)} ${b.content.padEnd(17)} ${String(b.status || '-').padEnd(4)} ` +
      `${(c.ip || '').padEnd(16)}${tls}${kit}${brand}`);
    if (b.title) console.log(`      title: ${JSON.stringify(b.title)}`);
    if (b.text) console.log(`      text : ${JSON.stringify(b.text.slice(0, 150))}`);
    if (b.final_url && hostOf(b.final_url) !== c.candidate && hostOf(b.final_url) !== 'www.' + c.candidate) {
      console.log(`      final: ${b.final_url}`);
    }
  }
  console.log('\nSummary: ' + order.filter(k => counts[k]).map(k => `${k}=${counts[k]}`).join('  '));
  console.log(`Screenshots: ${path.relative(process.cwd(), SHOTS)}/`);
  console.log(`Wrote browser verdicts back to ${path.basename(MEM)}`);
})().catch(e => { console.error('fatal:', e); process.exit(1); });
