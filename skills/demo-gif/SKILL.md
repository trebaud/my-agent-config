---
name: demo-gif
description: >
  Record polished demo GIFs of any app — terminal programs (TUI/CLI) via
  VHS-scripted .tape files, and browser/web/editor-plugin demos via a
  Playwright-recorded Chromium session (including side-by-side terminal +
  browser stages with ttyd). Every recording is scripted, deterministic, and
  verified frame-by-frame before shipping. Use when the user asks to create a
  demo GIF/recording/screencast, "record a demo", showcase a plugin or web app
  in the README, or produce asciinema/VHS-style animations.
allowed-tools: Bash Read Write Edit
---

# Record demo GIFs

Produce a small set of deterministic, scripted GIFs of an app. Every GIF comes
from a script (a VHS `.tape` or a Playwright `record.mjs`) replayed against a
fixed setup, so it is reproducible and survives UI changes — never hand-recorded.

**Core loop (all strategies):** drive the app → capture key beats → `Read` the
screenshots/extracted frames → adjust the script → regenerate. Never ship a GIF
you have not visually inspected.

## 0. Pick a strategy

| What's being demoed | Strategy |
| --- | --- |
| CLI / TUI, terminal-only | **A — VHS tape** |
| Web app / anything rendered in a browser | **B — Playwright recording** |
| Editor/IDE plugin with a browser counterpart (live preview, hot reload, dev server) | **B, side-by-side variant** — real editor in a ttyd pane + the app's page, one stage |

Notes on tool choice:

- If the user hints at "the Playwright MCP", check whether one is actually
  connected. Even when it is, prefer the **Playwright npm library** for demos —
  MCP servers can't record video; the library does (`recordVideo`), which is
  exactly what a GIF needs.
- Run Playwright with **node, not bun** — the driver is unreliable under bun.

Whatever the strategy, script a **narrative arc** (~15–25s): opening state →
trigger the feature → the payoff on camera (the "money shot", held ~3s) → one
flourish (e.g. a theme toggle) → end on a 2s hold, never mid-motion.

## 1. Install the toolchain — skip what's already present

- Strategy A: `vhs` + `ttyd` + `ffmpeg`.
- Strategy B: `node` + `ffmpeg`; `ttyd` only for the side-by-side variant; then
  in a scratch dir: `npm i playwright && npx playwright install chromium`.

On macOS: `brew install ffmpeg ttyd` (+ `vhs` for Strategy A). On Linux without
sudo, run the bundled installer (idempotent, installs to `~/.local/vhs-tools/bin`):

```bash
bash scripts/setup-tools.sh
export PATH="$HOME/.local/vhs-tools/bin:$PATH"   # use the line it prints
```

## 2. Know the app and prepare its input (all strategies)

- Make the binary/plugin runnable — build it, put it on `PATH`, or reference it
  by absolute path.
- Read its `--help` / key bindings / commands so the script sends the right keys.
- **Set the stage so the demo looks good.** Whatever the app needs to render
  something worth showing — sample files, a config, seed data, fixtures — prepare
  it *reproducibly* (script the setup) and keep it **outside the app's repo**
  (`/tmp/demo` or a sibling dir). Avoid on-screen timestamps or random content.
- **Plan for repeat takes.** If the demo mutates state (edits a file, writes a
  DB), keep a pristine copy and reset it + `pkill` stray spawned servers between
  takes. The first take is never the last.

## Strategy A — terminal app via VHS

### A1. Calibrate sizing once

Render one throwaway tape that launches the app and takes a `Screenshot`. Read
the PNG and adjust until the layout is readable and fills the frame. Good
starting point: `FontSize 15`, `Width 1320`, `Height 820`, `Padding 14`.

### A2. Author the tapes

One tape per coherent story (aim for **2–4 GIFs**, ~12–25s each). Group related
features; do not cram everything into one.

```tape
Output "/abs/path/to/assets/demo.gif"   # paths MUST be quoted

Set Shell bash
Set FontSize 15
Set Width 1320
Set Height 820
Set Padding 14
Set TypingSpeed 70ms
# Optional custom theme so the padding matches the app's canvas color (avoids a
# border seam). Set "background" to the app's actual background.
Set Theme { "name": "app-dark", "background": "#0d1117", "foreground": "#c9d1d9", "cursor": "#c9d1d9" }

# Hide setup keystrokes (cd + PATH) from the recording.
Hide
Type 'export PATH="$HOME/.local/vhs-tools/bin:$PATH"; cd "$HOME/path/to/fixture"; clear'
Enter
Sleep 800ms
Show

Type "myapp"
Enter
Sleep 2s

# ── drive features; each key is sent as a real keypress ──
Type "s"          # single-key TUI binding
Sleep 1500ms
Type "jj"         # navigation
Ctrl+d            # special keys: Enter, Tab, Escape, Ctrl+x, Up/Down/Left/Right, Space
Sleep 1800ms

# Verification screenshot at each beat (PNG only — does NOT add gif frames):
Screenshot "/tmp/beat1.png"
```

Authoring rules / gotchas:

- **Quote every path** after `Output` and `Screenshot` — unquoted `/tmp/x.gif`
  fails the parser ("Invalid command: tmp").
- **`Type` with embedded double quotes** (e.g. `"$VAR"` in a shell command): wrap
  the VHS string in **single quotes** — `Type 'export PATH="..."'`.
- `Type "s"` sends the `s` key (capitals send shift); use named commands for
  non-printing keys.
- Pace with explicit `Sleep`s — 1.5–2.5s on a beat you want read.
- Use `Hide`/`Show` to keep `cd`/`export`/`clear` out of frame.
- `vhs validate tape.tape` catches parse errors fast.

### A3. Generate

`vhs assets/tapes/demo.tape`, then verify per §3. VHS outputs the GIF directly —
skip §4's conversion unless you need to re-encode for size.

## Strategy B — browser demos via Playwright

Templates in `assets/side-by-side/` (copy into the scratch dir, e.g. `/tmp/demo`):
`frame.html` (the stage), `record.mjs` (the harness), `demo_init.lua` (example
editor config for the nvim case).

### B1. Build the stage

- **Plain web app:** point the recorded page straight at the app URL; no
  frame.html needed unless you want window chrome.
- **Side-by-side (editor + browser):** use `frame.html` — a dark page with two
  window-chrome panes, each an iframe. Left: a **real terminal** served by ttyd
  running the real editor. Right: the app's page. Nothing is mocked, so the
  reload/update on camera is genuine. Start ttyd like:

  ```bash
  ttyd -p 7681 -W -t fontSize=17 -t 'fontFamily=SF Mono, Menlo, monospace' \
    -t 'theme={"background":"#14161b","foreground":"#c8ccd4"}' -t cursorBlink=true \
    zsh -lc 'cd /tmp/demo && nvim -u demo_init.lua doc.md' >/tmp/demo/ttyd.log 2>&1 &
  ```

  ttyd takes ~1.5s to bind; don't panic at one failed curl. It spawns a fresh
  process per browser connection, so every take gets a clean editor.

### B2. Harness rules (encoded in `record.mjs`)

- `recordVideo` size = viewport size; **`deviceScaleFactor: 2`** so text stays
  crisp after the gif downscale. Record at ~1400×800, downscale later.
- To type into the terminal: click `.xterm-screen` inside the ttyd iframe once,
  then `page.keyboard.type(..., { delay: 45–120 })` — keystrokes land in the
  real app. Vary the delay: slower for commands the viewer should read.
- **Stub side effects that escape the recording.** If the app opens a system
  browser (e.g. nvim's `vim.ui.open`, `open`/`xdg-open`), override it in the
  demo config to write the URL to a file; the harness polls that file and sets
  the iframe `src`. A real browser window popping up ruins the take.
- **Determinism in the editor:** disable swapfile, auto-bullets/auto-indent
  (`formatoptions -= r o c t`), intro screens. Scripted keystrokes must mean
  the same thing every take.
- **Cross-origin iframes:** the `file://` stage page's own JS cannot reach into
  an `http://127.0.0.1` iframe — but Playwright can: parent-page JS may only set
  `iframe.src`; for clicks/scrolls *inside* the pane use
  `page.frames().find(f => f.url().startsWith(url))`.
- Keep the not-yet-loaded pane's background **dark** — a white placeholder
  flashes hard against a dark stage.
- `await context.close()` before grabbing the `.webm` — that's what flushes it.

### B3. Record

Reset state (pristine input file, `pkill` stray servers, remove the URL marker
file), then `node record.mjs`.

## 3. Verify by reading frames (all strategies)

For VHS: `Read` every `Screenshot` PNG. For Playwright: extract frames at the
expected beats and `Read` them:

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 demo.webm
ffmpeg -v error -ss 6 -i demo.webm -frames:v 1 -y beat1.png   # one per beat
```

Confirm each beat landed: right view open, payoff visible, nothing clipped at a
pane edge, theme/animation captured (a 150ms transition is easy to straddle —
check a frame on either side). The recorded duration is often shorter than the
sum of scripted waits; probe it before picking timestamps. Fix timing/keys and
regenerate until every beat is correct. **This visual check is the heart of the
skill.**

## 4. Convert to GIF (Playwright path)

```bash
ffmpeg -i demo.webm -vf "fps=12,scale=1100:-1:flags=lanczos,split[a][b];\
[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" demo.gif
```

- `stats_mode=diff` + `diff_mode=rectangle` exploit mostly-static frames —
  a 17s 1100px-wide side-by-side lands ≈3 MB. Budget **<6 MB** for a README
  (GitHub renders up to 10 MB).
- Scale to ~1000–1100px: READMEs display at ~830px, so this keeps retina
  crispness without bloat. If too big: drop to `fps=10` or `scale=960`.
- After converting, extract a frame or two **from the gif itself** and `Read`
  them — bayer dithering can get grainy on light backgrounds.

## 5. Finalize — GIFs are the only deliverable

- Move verified GIFs to a conventional dir (`assets/` or `docs/`) and link near
  the top of the README with meaningful alt text:
  `![Editing markdown in Neovim while the browser preview live-reloads on save](assets/demo.gif)`
- Delete the scaffolding: tapes / harness scratch dir (`/tmp/demo`), screenshot
  PNGs, fixtures. Kill leftover processes: `pkill -f ttyd`, the app's dev
  server, the editor. If the harness may be wanted for re-recording after UI
  changes, tell the user where it lived before deleting — or offer to keep it.
- **Do NOT delete installed toolchains** (vhs/ttyd/ffmpeg, the Playwright
  browser cache) — they make the next run instant.
- Confirm with `git status` that nothing but the new `*.gif` (and README edit)
  remains. Do not commit unless asked.
