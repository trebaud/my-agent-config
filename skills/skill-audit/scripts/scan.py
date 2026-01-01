#!/usr/bin/env python3
"""Static, non-executing scanner for an untrusted agent skill.

Usage: scan.py <path-to-skill-dir-or-file>

Walks every file in the target and flags mechanical red flags that a human
(or an LLM) can miss by eyeballing: invisible/hidden Unicode, bidi overrides
(Trojan Source), Unicode tag-block smuggling, homoglyphs, obfuscated payloads,
dangerous shell patterns, network exfiltration, and risky frontmatter.

This script NEVER executes, imports, or sources anything from the target.
It only reads bytes. Output is grouped by severity for a human/agent to triage.
"""
import os
import re
import sys
import unicodedata

# ---------------------------------------------------------------------------
# Hidden / invisible / dangerous Unicode codepoints
# ---------------------------------------------------------------------------

# Individually named offenders (zero-width, joiners, BOM, soft hyphen, etc.)
HIDDEN_CHARS = {
    0x00AD: "SOFT HYPHEN",
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0x2061: "FUNCTION APPLICATION",
    0x2062: "INVISIBLE TIMES",
    0x2063: "INVISIBLE SEPARATOR",
    0x2064: "INVISIBLE PLUS",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE / BOM",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
    0x115F: "HANGUL CHOSEONG FILLER",
    0x1160: "HANGUL JUNGSEONG FILLER",
    0x3164: "HANGUL FILLER",
    0xFFA0: "HALFWIDTH HANGUL FILLER",
}

# Bidirectional control characters — the "Trojan Source" class. These can make
# rendered text differ from logical byte order (hidden / reordered code).
BIDI_CHARS = {
    0x200E: "LEFT-TO-RIGHT MARK",
    0x200F: "RIGHT-TO-LEFT MARK",
    0x202A: "LEFT-TO-RIGHT EMBEDDING",
    0x202B: "RIGHT-TO-LEFT EMBEDDING",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE",
    0x202E: "RIGHT-TO-LEFT OVERRIDE",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
}

# Non-ASCII whitespace that masquerades as a normal space.
WEIRD_SPACES = {
    0x00A0: "NO-BREAK SPACE",
    0x2000: "EN QUAD", 0x2001: "EM QUAD", 0x2002: "EN SPACE", 0x2003: "EM SPACE",
    0x2004: "THREE-PER-EM SPACE", 0x2005: "FOUR-PER-EM SPACE", 0x2006: "SIX-PER-EM SPACE",
    0x2007: "FIGURE SPACE", 0x2008: "PUNCTUATION SPACE", 0x2009: "THIN SPACE",
    0x200A: "HAIR SPACE", 0x202F: "NARROW NO-BREAK SPACE", 0x205F: "MEDIUM MATHEMATICAL SPACE",
    0x3000: "IDEOGRAPHIC SPACE",
}

# Scripts whose letters are commonly used as Latin homoglyphs.
HOMOGLYPH_SCRIPTS = ("CYRILLIC", "GREEK", "ARMENIAN")

TEXT_EXT = {".md", ".txt", ".sh", ".bash", ".zsh", ".py", ".js", ".ts", ".mjs",
            ".cjs", ".go", ".rb", ".pl", ".rs", ".json", ".yaml", ".yml", ".toml",
            ".cfg", ".ini", ".env", ".html", ".css", ".sql", ".ps1", ".fish", ""}

# ---------------------------------------------------------------------------
# Suspicious source patterns. (label, severity, compiled regex)
# ---------------------------------------------------------------------------
def _p(label, sev, pattern, flags=re.I):
    return (label, sev, re.compile(pattern, flags))

PATTERNS = [
    # Remote-code execution / pipe-to-shell
    _p("pipe-to-shell", "CRITICAL", r"(curl|wget|fetch)\b[^\n|]*\|\s*(sudo\s+)?(ba)?sh\b"),
    _p("pipe-to-interpreter", "CRITICAL", r"(curl|wget)\b[^\n|]*\|\s*(python3?|perl|ruby|node)\b"),
    _p("eval-of-download", "CRITICAL", r"eval\s*\(?\s*\$\(\s*(curl|wget)"),
    _p("reverse-shell-devtcp", "CRITICAL", r"/dev/tcp/|/dev/udp/"),
    _p("netcat-exec", "CRITICAL", r"\bnc\b[^\n]*\s-[a-z]*e\b|\bncat\b[^\n]*--exec"),
    _p("bash-i-reverse", "CRITICAL", r"bash\s+-i\b.*>&\s*/dev/tcp"),
    # Credential / secret exfiltration
    _p("read-ssh-keys", "HIGH", r"~/?\.ssh/|id_rsa|id_ed25519|authorized_keys|known_hosts"),
    _p("read-cloud-creds", "HIGH", r"\.aws/credentials|\.aws/config|gcloud|\.kube/config|\.docker/config|\.netrc"),
    _p("read-token-file", "HIGH", r"\.npmrc|\.pypirc|\.config/gh/hosts|\.git-credentials|\.config/hub|\.cargo/credentials|\.gem/credentials"),
    _p("read-dotenv", "HIGH", r"\b\.env(\.[a-z]+)?\b"),
    _p("read-keychain", "HIGH", r"security\s+find-(generic|internet)-password|login\.keychain"),
    _p("read-browser-data", "HIGH", r"Login Data|cookies\.sqlite|Local Storage/leveldb"),
    _p("read-shell-history", "MEDIUM", r"\.(bash|zsh)_history"),
    _p("env-dump", "HIGH", r"\b(printenv|env)\b[^\n|]*\|\s*(curl|wget|nc)\b|curl[^\n]*--data[^\n]*\$\{?[A-Z_]*(TOKEN|KEY|SECRET|PASS)"),
    # Persistence
    _p("write-shell-rc", "HIGH", r">>?\s*~?/?\.(bashrc|zshrc|bash_profile|profile|zprofile)\b"),
    _p("crontab-install", "HIGH", r"\bcrontab\b|/etc/cron|launchctl\s+load|LaunchAgents|LaunchDaemons"),
    _p("ssh-authorized-write", "CRITICAL", r">>?\s*~?/?\.ssh/authorized_keys"),
    # Obfuscation / encoded execution
    _p("base64-decode-exec", "HIGH", r"base64\s+(-d|--decode|-D)\b[^\n|]*\|\s*(ba)?sh|atob\s*\("),
    _p("hex-decode-exec", "MEDIUM", r"xxd\s+-r|\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}"),
    _p("python-exec-eval", "MEDIUM", r"\b(exec|eval)\s*\(\s*(base64|bytes\.fromhex|codecs\.decode|__import__)"),
    _p("rot13-or-tr-obfusc", "LOW", r"\btr\s+['\"]?[A-Za-z]-[A-Za-z]"),
    # Destructive
    _p("rm-rf-root", "CRITICAL", r"rm\s+-[rf]{1,2}\s+(--no-preserve-root\s+)?(/|~|\$HOME)\s*($|[^\w/.])"),
    _p("dd-disk", "HIGH", r"\bdd\s+if=.*of=/dev/(disk|sd|nvme|rdisk)"),
    _p("disable-history", "MEDIUM", r"unset\s+HISTFILE|set\s+\+o\s+history|HISTSIZE=0"),
    # Network indicators
    _p("raw-ip-url", "MEDIUM", r"https?://\d{1,3}(\.\d{1,3}){3}"),
    _p("suspicious-host", "MEDIUM", r"\b(pastebin\.com|ngrok\.io|ngrok-free\.app|trycloudflare\.com|webhook\.site|requestbin|burpcollaborator|interact\.sh|oast\.|transfer\.sh|0x0\.st|termbin\.com|bit\.ly|tinyurl)\b"),
    _p("discord-telegram-webhook", "HIGH", r"discord(app)?\.com/api/webhooks|api\.telegram\.org/bot"),
    # Package supply chain (AST02)
    _p("install-from-url", "MEDIUM", r"(pip|pip3)\s+install[^\n]*https?://|npm\s+install[^\n]*(https?://|git\+)"),
    _p("curl-to-tmp-run", "HIGH", r"(curl|wget)[^\n]*-o\s+/tmp/[^\n]*&&[^\n]*chmod[^\n]*\+x"),
    # Unsafe deserialization (AST05) — payloads that execute during config/skill loading
    _p("yaml-python-tag", "CRITICAL", r"!!python/(object|module|name)"),
    _p("yaml-unsafe-load", "HIGH", r"yaml\.(unsafe_)?load\s*\((?![^)]*(Safe|CSafe)Loader)|yaml\.full_load\b|Loader\s*=\s*(yaml\.)?(Loader|FullLoader|UnsafeLoader)\b"),
    _p("pickle-load", "HIGH", r"\b(c?[pP]ickle|dill)\.(loads?|Unpickler)\b|\bmarshal\.loads?\b|\b__reduce__\b"),
    _p("prototype-pollution", "HIGH", r"__proto__|constructor\s*\.\s*prototype|\[\s*['\"]__proto__['\"]\s*\]"),
    _p("toml-namespace-inject", "LOW", r"toml\.loads?\b|tomllib\.loads?\b"),
    # Identity-file / agent-memory poisoning (AST01, AST03) — persistent behavioral backdoors
    _p("agent-identity-write", "HIGH", r"(>>?|tee|cat\s*>|cp\b|mv\b|echo[^\n]*>)[^\n]*\b(SOUL|MEMORY|CLAUDE|AGENTS|GEMINI|\.cursorrules|\.clauderc)\b|\.md\b[^\n]*(append|overwrite)"),
    _p("agent-identity-ref", "LOW", r"\b(SOUL\.md|MEMORY\.md|CLAUDE\.md|AGENTS\.md|\.cursorrules)\b"),
    # Config-file / MCP / hooks hijacking that can trigger on project open (AST02, AST06)
    _p("mcp-config-write", "MEDIUM", r"mcpServers|\.mcp\.json|claude_desktop_config|\.claude/settings|\.cursor/mcp|\.vscode/settings\.json"),
    # Update drift / unpinned + auto-update + hot-reload (AST07)
    _p("install-unpinned", "LOW", r"@(latest|main|master|HEAD)\b|(pip|pip3)\s+install[^\n]*(--upgrade|-U)\b|npm\s+(i|install)[^\n]*@latest"),
    _p("auto-update", "MEDIUM", r"auto[-_ ]?updat|self[-_ ]?updat|hot[-_ ]?reload"),
    # Localhost services / WebSocket C2 (AST01, AST06)
    _p("websocket-channel", "MEDIUM", r"\bwss?://|new\s+WebSocket\s*\(|websockets?\.(connect|client|serve)|WebSocketApp"),
]

# Social-engineering / ClickFix prose aimed at the *user* (AST01) — scanned in .md only.
SOCIAL_PATTERNS = [
    _p("clickfix-prereq", "MEDIUM", r"(paste|copy)[^\n]{0,40}(terminal|shell|command line|iex|powershell)|run\s+(this|the following)\s+command\s+(in|to|before)|before\s+(using|installing)[^\n]{0,40}\brun\b"),
    _p("manual-chmod-run", "MEDIUM", r"chmod\s+\+x[^\n]*&&[^\n]*\./|please\s+run\s+|sudo\s+(bash|sh)\s"),
]

# Prompt-injection phrasing aimed at the *auditing/host* LLM, not the user.
INJECTION_PATTERNS = [
    _p("ignore-instructions", "HIGH", r"ignore\s+(all\s+)?(previous|prior|above|the\s+system)\s+(instructions|prompts?|rules)"),
    _p("override-system-prompt", "HIGH", r"disregard\s+(your|the)\s+(system|safety|guidelines)|you\s+are\s+now\s+(a|an|in)\b"),
    _p("exfil-instruction", "HIGH", r"(send|post|upload|exfiltrate|leak)\s+(the\s+)?(contents?|env|secrets?|keys?|tokens?|files?)\s+to\b"),
    _p("do-not-tell-user", "HIGH", r"do\s+not\s+(tell|inform|mention|show|notify)\s+(the\s+)?user|without\s+(the\s+)?user'?s?\s+(knowledge|consent|awareness)"),
    _p("silently", "MEDIUM", r"\bsilently\b|\bquietly\b|in\s+the\s+background\s+without"),
    _p("auto-approve", "MEDIUM", r"auto[-\s]?approve|skip\s+confirmation|bypass\s+(the\s+)?(permission|approval|sandbox)"),
]

# Risky frontmatter keys in SKILL.md
BROAD_TOOLS = {"bash", "*", "all"}

# Map each mechanical check to the OWASP Agentic Skills Top 10 risk it evidences.
# https://owasp.org/www-project-agentic-skills-top-10/
AST_MAP = {
    # AST01 Malicious Skills
    "pipe-to-shell": "AST01", "pipe-to-interpreter": "AST01", "eval-of-download": "AST01",
    "reverse-shell-devtcp": "AST01", "netcat-exec": "AST01", "bash-i-reverse": "AST01",
    "read-ssh-keys": "AST01", "read-cloud-creds": "AST01", "read-token-file": "AST01",
    "read-dotenv": "AST01",
    "read-keychain": "AST01", "read-browser-data": "AST01", "read-shell-history": "AST01",
    "env-dump": "AST01", "write-shell-rc": "AST01", "crontab-install": "AST01",
    "ssh-authorized-write": "AST01", "rm-rf-root": "AST01", "dd-disk": "AST01",
    "disable-history": "AST01", "raw-ip-url": "AST01", "suspicious-host": "AST01",
    "discord-telegram-webhook": "AST01", "clickfix-prereq": "AST01", "manual-chmod-run": "AST01",
    "exfil-instruction": "AST01",
    # AST02 Supply Chain Compromise
    "install-from-url": "AST02", "curl-to-tmp-run": "AST02", "mcp-config-write": "AST02",
    # AST03 Over-Privileged Skills
    "broad-tools": "AST03", "agent-identity-write": "AST03", "agent-identity-ref": "AST03",
    # AST04 Insecure Metadata (steganographic injection / impersonation)
    "hidden-unicode": "AST04", "bidi-control": "AST04", "weird-space": "AST04",
    "private-use": "AST04", "control-char": "AST04", "homoglyph": "AST04",
    "tag-smuggling": "AST04", "variation-selector-smuggling": "AST04",
    # AST05 Unsafe Deserialization
    "yaml-python-tag": "AST05", "yaml-unsafe-load": "AST05", "pickle-load": "AST05",
    "prototype-pollution": "AST05", "toml-namespace-inject": "AST05", "frontmatter-hook": "AST05",
    # AST06 Weak Isolation
    "symlink": "AST06", "websocket-channel": "AST06",
    # AST07 Update Drift
    "install-unpinned": "AST07", "auto-update": "AST07",
    # AST08 Poor Scanning (obfuscation that defeats pattern matching; opaque blobs)
    "base64-decode-exec": "AST08", "hex-decode-exec": "AST08", "python-exec-eval": "AST08",
    "rot13-or-tr-obfusc": "AST08", "long-base64-blob": "AST08", "long-hex-blob": "AST08",
    "binary-file": "AST08",
    # Host-model prompt injection (cross-cuts AST01/AST04/AST08)
    "ignore-instructions": "AST01", "override-system-prompt": "AST01",
    "do-not-tell-user": "AST01", "silently": "AST01", "auto-approve": "AST01",
}


def severity_rank(s):
    return {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}.get(s, 5)


def iter_files(root):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            yield os.path.join(dirpath, name)


def _decode_tag_run(cps):
    """Decode a run of Unicode Tag chars back to the ASCII they mirror.
    U+E0020..U+E007E map to printable ASCII 0x20..0x7E (ASCII smuggling)."""
    out = []
    for cp in cps:
        if 0xE0020 <= cp <= 0xE007E:
            out.append(chr(cp - 0xE0000))
        elif cp == 0xE0001:
            out.append("␂")  # LANGUAGE TAG marker
        elif cp == 0xE007F:
            out.append("␃")  # CANCEL TAG marker
        else:
            out.append("�")
    return "".join(out)


def _decode_varsel_run(cps):
    """Decode a run of variation selectors back to the byte stream they smuggle.
    U+FE00..FE0F -> 0x00..0x0F ; U+E0100..E01EF -> 0x10..0xFF (Butler technique)."""
    data = bytearray()
    for cp in cps:
        if 0xFE00 <= cp <= 0xFE0F:
            data.append(cp - 0xFE00)
        elif 0xE0100 <= cp <= 0xE01EF:
            data.append(cp - 0xE0100 + 16)
    printable = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in data)
    return data.hex(), printable


def scan_unicode(text, findings, relpath):
    for lineno, line in enumerate(text.splitlines(), 1):
        tag_cps, varsel_cps = [], []
        for col, ch in enumerate(line, 1):
            cp = ord(ch)
            if cp < 0x80:
                continue
            if cp in HIDDEN_CHARS:
                findings.append(("CRITICAL", "hidden-unicode", relpath, lineno,
                                 f"U+{cp:04X} {HIDDEN_CHARS[cp]} (invisible)"))
            elif cp in BIDI_CHARS:
                findings.append(("CRITICAL", "bidi-control", relpath, lineno,
                                 f"U+{cp:04X} {BIDI_CHARS[cp]} (Trojan Source / text reordering)"))
            elif 0xE0000 <= cp <= 0xE007F:
                tag_cps.append(cp)            # decode the whole run after the line
            elif cp in WEIRD_SPACES:
                findings.append(("MEDIUM", "weird-space", relpath, lineno,
                                 f"U+{cp:04X} {WEIRD_SPACES[cp]} (non-ASCII space)"))
            elif 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
                varsel_cps.append(cp)         # decode the whole run after the line
            elif 0xE000 <= cp <= 0xF8FF or 0xF0000 <= cp <= 0xFFFFD:
                findings.append(("MEDIUM", "private-use", relpath, lineno,
                                 f"U+{cp:04X} PRIVATE USE AREA char"))
            elif unicodedata.category(ch) in ("Cc", "Cf") and cp not in (0x09, 0x0A, 0x0D):
                findings.append(("HIGH", "control-char", relpath, lineno,
                                 f"U+{cp:04X} control/format char"))
            else:
                try:
                    name = unicodedata.name(ch)
                except ValueError:
                    continue
                for script in HOMOGLYPH_SCRIPTS:
                    if name.startswith(script) and ("LETTER" in name):
                        # Only flag when embedded in an otherwise-ASCII line (mixed script)
                        if any(ord(c) < 0x80 and c.isalpha() for c in line):
                            findings.append(("HIGH", "homoglyph", relpath, lineno,
                                             f"U+{cp:04X} {name} mixed with Latin (lookalike)"))
                        break
        if tag_cps:
            decoded = _decode_tag_run(tag_cps)
            findings.append(("CRITICAL", "tag-smuggling", relpath, lineno,
                             f"{len(tag_cps)} invisible Unicode TAG char(s) (ASCII smuggling) "
                             f"-> decodes to: {decoded!r}"))
        if varsel_cps:
            hexstr, printable = _decode_varsel_run(varsel_cps)
            findings.append(("HIGH", "variation-selector-smuggling", relpath, lineno,
                             f"{len(varsel_cps)} variation selector(s) hiding {len(varsel_cps)} byte(s) "
                             f"-> hex={hexstr} ascii={printable!r}"))


def scan_patterns(text, findings, relpath, patterns):
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, sev, rx in patterns:
            if rx.search(line):
                snippet = line.strip()[:120]
                findings.append((sev, label, relpath, lineno, snippet))


def scan_encoded_blobs(text, findings, relpath):
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"[A-Za-z0-9+/]{120,}={0,2}", line):
            findings.append(("MEDIUM", "long-base64-blob", relpath, lineno,
                             f"{len(m.group(0))}-char base64-like blob (possible hidden payload)"))
        for m in re.finditer(r"(?:\\x[0-9a-fA-F]{2}){20,}|0x[0-9a-fA-F]{40,}", line):
            findings.append(("MEDIUM", "long-hex-blob", relpath, lineno,
                             f"{len(m.group(0))}-char hex blob (possible hidden payload)"))


def scan_frontmatter(text, findings, relpath):
    if not text.startswith("---"):
        return
    end = text.find("\n---", 3)
    if end == -1:
        return
    fm = text[3:end]
    for key in ("hooks", "hook", "PreToolUse", "PostToolUse", "lifecycle", "on_install", "postinstall"):
        if re.search(rf"^\s*{re.escape(key)}\s*:", fm, re.M):
            findings.append(("HIGH", "frontmatter-hook", relpath, 1,
                             f"frontmatter declares '{key}' — may auto-execute on load/install"))
    m = re.search(r"^\s*(allowed-tools|tools)\s*:\s*(.+)$", fm, re.M)
    if m:
        tools = {t.strip().lower() for t in re.split(r"[,\s]+", m.group(2)) if t.strip()}
        if tools & BROAD_TOOLS:
            findings.append(("INFO", "broad-tools", relpath, 1,
                             f"declares broad tool access: {m.group(2).strip()}"))


def main():
    if len(sys.argv) != 2:
        print("usage: scan.py <path-to-skill>", file=sys.stderr)
        return 2
    root = os.path.abspath(sys.argv[1])
    if not os.path.exists(root):
        print(f"error: {root} does not exist", file=sys.stderr)
        return 2

    findings = []
    inventory = []

    for path in sorted(iter_files(root)):
        rel = os.path.relpath(path, root if os.path.isdir(root) else os.path.dirname(root))
        # Symlinks: never follow; flag them.
        if os.path.islink(path):
            findings.append(("HIGH", "symlink", rel, 0, f"-> {os.readlink(path)}"))
            inventory.append((rel, "symlink"))
            continue
        st = os.stat(path)
        execbit = bool(st.st_mode & 0o111)
        ext = os.path.splitext(path)[1].lower()
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as e:
            findings.append(("INFO", "unreadable", rel, 0, str(e)))
            continue

        is_binary = b"\x00" in raw[:4096]
        kind = "binary" if is_binary else ("script" if execbit or ext in {".sh", ".py", ".js", ".rb", ".pl"} else "text")
        inventory.append((rel, kind + ("/exec" if execbit and not is_binary else "")))

        if is_binary:
            findings.append(("HIGH", "binary-file", rel, 0,
                             f"{len(raw)} bytes binary — cannot review; treat as opaque payload"))
            continue
        if ext and ext not in TEXT_EXT and not execbit:
            findings.append(("INFO", "unexpected-ext", rel, 0, f"unusual file type {ext}"))

        text = raw.decode("utf-8", errors="replace")
        scan_unicode(text, findings, rel)
        scan_patterns(text, findings, rel, PATTERNS)
        scan_encoded_blobs(text, findings, rel)
        if rel.endswith(".md"):
            scan_patterns(text, findings, rel, INJECTION_PATTERNS)
            scan_patterns(text, findings, rel, SOCIAL_PATTERNS)
        if os.path.basename(path).upper().startswith("SKILL.MD") or os.path.basename(path) == "SKILL.md":
            scan_frontmatter(text, findings, rel)
        if execbit:
            findings.append(("INFO", "executable", rel, 0, "file has the executable bit set"))

    # ---- Report ----
    print(f"# Static scan: {root}\n")
    print(f"## Inventory ({len(inventory)} files)\n")
    for rel, kind in inventory:
        print(f"  - [{kind}] {rel}")
    print()

    findings.sort(key=lambda f: (severity_rank(f[0]), f[2], f[3]))
    if not findings:
        print("## Findings\n\nNo mechanical red flags detected. Still perform the semantic review.")
        return 0

    counts = {}
    for sev, *_ in findings:
        counts[sev] = counts.get(sev, 0) + 1
    summary = " ".join(f"{counts[s]} {s}" for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO") if s in counts)
    print(f"## Findings ({len(findings)} — {summary})\n")
    print("| Severity | OWASP | Check | File | Line | Detail |")
    print("|----------|-------|-------|------|------|--------|")
    for sev, label, rel, line, detail in findings:
        detail = detail.replace("|", "\\|")
        ast = AST_MAP.get(label, "-")
        print(f"| {sev} | {ast} | {label} | {rel} | {line or '-'} | {detail} |")

    # Which OWASP Agentic Skills Top 10 risks have at least one candidate.
    seen = sorted({AST_MAP.get(f[1]) for f in findings} - {None, "-"})
    if seen:
        print(f"\nOWASP risks with candidates: {', '.join(seen)} "
              "(see references/threats.md for AST01–AST10).")
    print("\n> Mechanical findings only. Pattern matches are CANDIDATES — confirm intent in the semantic review before reporting. Pattern matching alone misses natural-language / context-dependent attacks (AST08), so the semantic review is mandatory even when this table is empty. CRITICAL/HIGH hidden-unicode, bidi, tag-smuggling, deserialization, and exfil findings are almost never legitimate in a skill.")
    return 1 if any(severity_rank(f[0]) <= 1 for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
