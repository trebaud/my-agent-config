# Skills

A collection of agent skills I use day to day.

## Installation

```bash
mkdir -p ~/.agents
git clone https://github.com/trebaud/skills.git ~/.agents
```

Then create symbolic links to make skills available to your agents:

```bash
ln -s ~/.agents/skills ~/.claude/skills
ln -s ~/.agents/skills ~/.opencode/skills
```

## Skills in the SDLC

```
   ┌────────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────────┐
   │ Understand │──▶│   Plan    │──▶│  Design   │──▶│  Develop  │──▶│   Test    │──▶│ Review & Ship │
   └────────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────────┘
         ▲                                                                                    │
         └───────────────────────────────────── iterate ──────────────────────────────────────┘

   Understand:     repo-visualizer · pr-visualizer · i-know-kungfu
   Plan:           prd · specs-generator · rfc-generator · interview
   Design:         arch-diagram · kiss-check · threat-model
   Develop:        janitor · refactor
   Test:           test-generator · debug
   Review & Ship:  pr-walkthrough · code-reviewer · security-analysis · semgrep-audit
                   gha-audit · audit-fix · create-pr · releaser
```

- **Understand** -- `repo-visualizer` to map a whole codebase, `pr-visualizer` to explain a diff — both as shareable, dependency-free HTML pages; `i-know-kungfu` to actually *learn* a concept/codebase/paper via an evidence-based active-learning loop
- **Plan** -- `prd` for product requirements, `specs-generator` for feature specs, `rfc-generator` for proposals, `interview` to validate plans
- **Design** -- `arch-diagram` to visualize the system, `kiss-check` to challenge complexity, `threat-model` to map what an attacker does with it
- **Develop** -- `janitor` for architecture and code quality, `refactor` for safe simplification
- **Test** -- `test-generator` for coverage, `debug` for test-first bug fixing
- **Review & Ship** -- `pr-walkthrough` for a guided-review HTML page that walks a human through a PR in call order, `code-reviewer` + `security-analysis` + `semgrep-audit` for code review, `gha-audit` for CI security, `audit-fix` for dependency vulnerabilities, `create-pr` to open the PR, `releaser` to cut a release

| Skill | Description |
|-------|-------------|
| [arch-diagram](skills/arch-diagram/SKILL.md) | Generates Mermaid.js architecture diagrams. Keeps visual docs in sync with code. |
| [audit-fix](skills/audit-fix/SKILL.md) | Audits prod dependencies and fixes vulnerabilities by tracing to root parents, using recursive updates, parent bumps, or replacements. |
| [code-reviewer](skills/code-reviewer/SKILL.md) | Comprehensive code review covering quality, security, and maintainability. |
| [create-pr](skills/create-pr/SKILL.md) | Creates pull requests with auto-generated title and description. |
| [debug](skills/debug/SKILL.md) | Test-first debugging. Creates reproducing tests, then uses subagents to implement fixes. |
| [gha-audit](skills/gha-audit/SKILL.md) | Audits GitHub Actions workflows for security issues — dangerous triggers, script injection, unpinned actions, over-permissioned tokens. |
| [i-know-kungfu](skills/i-know-kungfu/SKILL.md) | Tutors a human to genuine fluency in a concept/codebase/paper using a cognitive-science active-learning loop (retrieval, predict-reveal, spacing, Feynman teach-back). Main deliverable is a set of linked self-contained HTML pages — an overview hub with a concept-map graph, one active-recall lesson page per chunk, flashcards, a self-quiz, and a spaced-review plan. |
| [interview](skills/interview/SKILL.md) | Asks non-obvious technical questions about implementation plans, tradeoffs, and constraints. |
| [janitor](skills/janitor/SKILL.md) | Refactors code toward Clean Architecture and Clean Code principles. Fixes dependency violations, separates concerns, improves code quality. |
| [kiss-check](skills/kiss-check/SKILL.md) | Forces justification for complex solutions. Must explain why simpler won't work. |
| [pr-visualizer](skills/pr-visualizer/SKILL.md) | Generates a self-contained HTML page explaining a PR/branch/diff at a glance — interactive SVG graphs, file-change cards, decisions timeline, before/after toggle. |
| [prd](skills/prd/SKILL.md) | Generates Product Requirements Documents with clarifying questions, user stories, and acceptance criteria. |
| [pr-walkthrough](skills/pr-walkthrough/SKILL.md) | Generates a self-contained HTML page that walks a reviewer through a PR as a guided journey — trust-flow map, numbered stops ordered by call depth from entry points/trust boundaries down into business logic, per-stop trust-tagged review questions, and live progress tracking. |
| [refactor](skills/refactor/SKILL.md) | Safe refactoring with automated test verification after each step. |
| [repo-visualizer](skills/repo-visualizer/SKILL.md) | Generates a self-contained HTML page mapping an entire codebase — dependency graph, directory tree, runtime flows, module cards, and a "where to start" onboarding checklist. |
| [releaser](skills/releaser/SKILL.md) | Cuts a new release of a bun package: bumps version, runs typecheck and tests, pushes the git tag, creates a GitHub release with curated changelog. |
| [rfc-generator](skills/rfc-generator/SKILL.md) | Creates RFC documents for new features through interactive questioning. |
| [security-analysis](skills/security-analysis/SKILL.md) | Identifies security vulnerabilities and analyzes security reports. |
| [semgrep-audit](skills/semgrep-audit/SKILL.md) | White-box security auditor with semgrep integration. Triages scan results and proposes concrete fixes. |
| [specs-generator](skills/specs-generator/SKILL.md) | Creates SPECS.md files for new features and design documentation. |
| [test-generator](skills/test-generator/SKILL.md) | Generates unit and integration tests following existing patterns. |
| [threat-model](skills/threat-model/SKILL.md) | Builds a threat model into THREAT_MODEL.md — trust-boundary diagram, STRIDE pass over every boundary crossing, likelihood x impact scoring, and a disposition plus code-verified control for every threat. Reference covers where boundaries actually sit and the failure modes that make a threat model look complete while being wrong. |

## Misc

Skills that live outside the SDLC loop — situational tools for security monitoring, PR triage, writing, and skill authoring itself.

| Skill | Description |
|-------|-------------|
| [condense](skills/condense/SKILL.md) | Cuts text down to size — concise prose, tighter sentences, filler removed, meaning intact. Filler-word, wordy-phrase, and weak-construction patterns plus a substitution table. |
| [create-skill](skills/create-skill/SKILL.md) | Writes or revises agent skills — finds what the model actually gets wrong, drafts the minimum that fixes it, then runs a cutting pass that deletes everything the model already knows. Follows Anthropic's [new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models): judgment over rules, interface design over examples, progressive disclosure, one authoritative source. |
| [demo-gif](skills/demo-gif/SKILL.md) | Records polished demo GIFs of any terminal app (TUI or CLI) from a given set of instructions — VHS-scripted `.tape` files verified frame-by-frame with screenshots. |
| [gh-feed](skills/gh-feed/SKILL.md) | Shows a rich feed of active open pull requests across all GitHub repos — links, review status, CI, comments, and latest activity. |
| [humanize](skills/humanize/SKILL.md) | Strips LLM writing tics from prose — a `slopcheck.py` script flags phrase-level tics deterministically, then a manual pass fixes structural ones (em-dash overuse, contrast scaffolding, uniform rhythm). |
| [macos-security-audit](skills/macos-security-audit/SKILL.md) | Runs a comprehensive security audit on macOS: processes, network, persistence, hardening, and more. |
| [plain](skills/plain/SKILL.md) | Answers and rewrites text in ASD-STE100 Simplified Technical English — short sentences, active voice, one meaning per word, approved vocabulary. |
| [skill-auditor](skills/skill-auditor/SKILL.md) | Statically audits an untrusted agent skill before installing it — catches malware, prompt injection, credential exfiltration, hidden/invisible Unicode (zero-width, bidi/Trojan-Source, tag-block smuggling, homoglyphs), obfuscated payloads, reverse shells, and auto-run hooks. Never executes the candidate. |
| [todo](skills/todo/SKILL.md) | Tracks personal todo tasks through a simple single-page web app backed by SQLite — add, complete, and remove tasks. One Bun script, no dependencies. |
| [typosquat-scan](skills/typosquat-scan/SKILL.md) | Generates lookalike-domain candidates for a domain, resolves them via DNS, and probes HTTP/HTTPS to surface phishing impersonators and brand-protection registrations. |
| [unslop](skills/unslop/SKILL.md) | Rewrites text to remove AI tropes and cliches, making it sound more natural and human. |
| [vuln-feed-scan](skills/vuln-feed-scan/SKILL.md) | Scans security feeds for recent high-signal vulnerabilities affecting a configured stack, then cross-checks each finding against the repos in the working directory. |

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/install-skill.sh <skill-name>` | Copies one skill from `skills/` into `~/.agents/skills`, then symlinks it into `~/.claude/skills` and `~/.opencode/skills`. |
| `scripts/claude-worktree.sh` | Creates a git worktree under `.claude/worktrees/<branch>`, installs deps, and launches Claude Code. |

## Evals

Some skills are tested with [Anthropic's `skill-creator`](https://github.com/anthropics/skills) eval harness. Each test case runs the prompt twice — once with the skill, once without — then grades both against assertions to measure what the skill actually adds. Test definitions live in `skills/<name>/evals/evals.json`; generated run outputs, gradings, and benchmarks land in a `skills/<name>-workspace/` folder that is gitignored.
