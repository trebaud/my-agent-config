---
name: dont-reinvent-the-wheel
description: >-
  Find existing modules, utils, and patterns in the codebase that satisfy a
  SPEC/PRD/RFC's needs, then interview on reuse vs. build. Triggers: don't
  reinvent, reuse check, what to reuse.
argument-hint: [spec-path] [wiki-path]
user-invocable: true
---

# Don't Reinvent

Map a spec's requirements to code the codebase already has, so you reuse instead of
rebuild. Plan only — don't implement.

If an LLM wiki is present (e.g. an AI-generated codebase overview), read it first to
understand the codebase before searching. Check the optional `[wiki-path]` arg;
otherwise look for common locations (e.g. `.wiki/`, `docs/wiki/`, `DeepWiki`).

1. **Extract.** Read the SPEC/PRD/RFC (ask for the path if missing). List its ~5-15
   concrete, searchable capabilities (e.g. "rate limiting", "retry with backoff").

2. **Find prior art.** Grep/Glob the codebase per capability — modules/services owning
   the responsibility, util functions, patterns to copy, installed deps. Mark each:
   - ✅ **Exists** — `path:line`, what it does, fit.
   - 🟡 **Partial** — exists but needs extending; note the gap.
   - ❌ **None** — build new.

   Cite real `path:line` you've read; never claim an unopened match.

3. **Interview** (AskUserQuestion, batch related). For each ✅/🟡: reuse as-is, extend,
   or build alongside? Off-limits (deprecated, another team's, being rewritten)? Skip ❌.

4. **Output** a table `| Capability | Status | Existing code (path:line) | Decision |`,
   then short Reuse / Extend / Build-new lists. Prefer extending over duplicating.
