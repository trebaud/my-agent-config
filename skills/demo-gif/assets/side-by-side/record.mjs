// Playwright recording harness for side-by-side (terminal + browser) demos.
// Adapt the CONFIG block and the scripted beats; the plumbing rarely changes.
// Run with node (not bun — Playwright's driver is unreliable under bun).
import { chromium } from "playwright";
import fs from "node:fs";

// ── CONFIG ──────────────────────────────────────────────────────────────
const WORKDIR = "/tmp/demo";              // frame.html, url.txt, output live here
const VW = 1400, VH = 800;                // record large, downscale in the gif step
const OUT = `${WORKDIR}/out`;
const URL_FILE = `${WORKDIR}/url.txt`;    // written by the stubbed browser-opener
// ────────────────────────────────────────────────────────────────────────

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: VW, height: VH },
  deviceScaleFactor: 2,                   // crisp text when the gif is downscaled
  recordVideo: { dir: OUT, size: { width: VW, height: VH } },
});
const page = await context.newPage();
await page.goto(`file://${WORKDIR}/frame.html`);

// Click the xterm screen inside the ttyd iframe — after this, page.keyboard
// keystrokes land in the real terminal app.
const term = page.frameLocator("#term");
await term.locator(".xterm-screen").click();
await page.waitForTimeout(1800); // let the TUI draw

const type = (s, delay = 60) => page.keyboard.type(s, { delay });
const enter = () => page.keyboard.press("Enter");

// ── Beat 1: trigger the feature that starts the web side ────────────────
await type(":MarkdownPreview", 75);
await enter();

// The app under demo must NOT open a real system browser; stub its opener so
// it writes the URL to URL_FILE instead, then poll for it here.
let url;
for (let i = 0; i < 100 && !url; i++) {
  try { url = fs.readFileSync(URL_FILE, "utf8").trim(); }
  catch { await page.waitForTimeout(100); }
}
if (!url) throw new Error("app URL never appeared — is the opener stubbed?");

await page.waitForTimeout(600);
// frame.html is file:// so its JS can't touch the cross-origin iframe content,
// but it CAN set the iframe src; Playwright can reach inside (see Beat 3).
await page.evaluate((u) => {
  document.getElementById("preview").src = u;
  document.getElementById("addr").textContent = u.replace(/^http:\/\//, "");
}, url);
await page.waitForTimeout(2500); // hold: let the viewer read the rendered page

// ── Beat 2: live edit → save → on-camera reaction ───────────────────────
await type("Go", 120);
await enter();
await type("## Todo", 55);
await enter(); await enter();
await type("- [x] live reload on save", 45);
await enter();
await type("- [ ] world domination", 45);
await page.keyboard.press("Escape");
await page.waitForTimeout(700);
await type(":w", 110);
await enter();
await page.waitForTimeout(3000); // hold on the money shot

// ── Beat 3: a flourish inside the app pane ──────────────────────────────
// Playwright frames work across origins even though page JS can't.
const pframe = page.frames().find((f) => f.url().startsWith(url));
await pframe.locator("#theme").click();
await page.waitForTimeout(1700);
await pframe.locator("#theme").click();
await page.waitForTimeout(2200); // end on a hold, not mid-motion

await context.close(); // flushes the video
const video = fs.readdirSync(OUT).find((f) => f.endsWith(".webm"));
fs.renameSync(`${OUT}/${video}`, `${OUT}/demo.webm`);
await browser.close();
console.log("done:", `${OUT}/demo.webm`);
