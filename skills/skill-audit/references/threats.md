# Skill threat catalog — OWASP Agentic Skills Top 10

- **AST01 — Malicious skills.** Hidden malicious code (RCE, reverse shells,
  credential/secret theft, exfil channels, persistence, C2, destructive ops), prompt
  injection aimed at the host model, ClickFix steps telling the *user* to run something
  dangerous, identity/memory poisoning (writes to `CLAUDE.md`/`MEMORY.md`/`SOUL.md`/`AGENTS.md`),
  and impersonation/typosquatting of trusted skills.
- **AST02 — Supply-chain compromise.** Benign skill, malicious payload: runtime-fetched
  second stages, malice in a transitive dep (`requirements.txt`/`package.json`/lockfiles),
  or config files that execute on project open (`.mcp.json`, `.claude/settings`,
  `.vscode/settings.json`, hooks). Treat config files as executable.
- **AST03 — Over-privileged skills.** More access than the purpose needs: `allowed-tools:
  ["*"]`, broad shell/DB, identity-file writes, open network egress. Risk is amplification
  — a downstream injection weaponizes the excess.
- **AST04 — Insecure metadata.** Unsigned metadata that lies: description↔behaviour
  mismatch (highest-value check), understated permissions, spoofed risk tier, and
  steganographic injection in text — zero-width chars (`U+200B`–`200D`, `FEFF`),
  bidi/Trojan-Source (`U+202A`–`202E`, `2066`–`2069`), tag-block smuggling
  (`U+E0000`–`E007F`), variation selectors, homoglyphs, non-ASCII spaces.
- **AST05 — Unsafe deserialization** (runs on load, before invocation): YAML object tags
  (`!!python/...`), unsafe loaders (`yaml.load` without `SafeLoader`), pickle/marshal,
  JS prototype pollution (`__proto__`), and auto-run frontmatter (`hooks`, `on_install`,
  `postinstall`).
- **AST06 — Weak isolation.** Behaviour that assumes full host access: persistence
  (cron/LaunchAgents/shell-rc), network pivot/C2, an unauthenticated local control
  interface, skill shadowing of built-ins, symlinks pointing outside the skill dir.
- **AST07 — Update drift.** Safe now, malicious on next pull: unpinned deps
  (`@latest`/`@main`, `pip install -U`), silent auto-update/hot-reload, rollback to
  known-vulnerable versions.
- **AST08 — Poor scanning.** Why the semantic review is mandatory: malice can live in
  plain prose, in runtime-decoded encodings (base64/hex/`exec`), in context-gated triggers
  (date/target/env var), or in opaque binaries — none caught reliably by a regex.
- **AST09 — No governance.** Track an inventory entry (name, version, content hash, source,
  verdict); prefer an approval workflow over ad-hoc installs; no revocation unless tracked.
- **AST10 — Cross-platform reuse.** Ported skills lose security metadata in transit;
  popularity/stars/install counts are not safety evidence; re-validate from scratch.
