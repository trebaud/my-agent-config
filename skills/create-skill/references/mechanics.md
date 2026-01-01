# Skill Mechanics

Claude Code specifics that change how a skill should be written. Not a frontmatter reference — only the parts that are counterintuitive or that alter authoring decisions.

## Contents
- Content persists for the session
- allowed-tools is a grant, not a restriction
- Bundled scripts
- Directory layout and naming
- Invocation control
- Arguments
- Portability

## Content persists for the session

When a skill is invoked, the rendered SKILL.md enters the conversation as one message and stays for the rest of the session. Claude Code does not re-read the file on later turns.

Write standing instructions, not one-time steps. "Before each commit, run X" survives; "now run X" is consumed once and then sits in context as noise. Anything that must hold throughout a long task has to read as a rule, not a step.

## allowed-tools is a grant, not a restriction

`allowed-tools` pre-approves tools so they run without a permission prompt during the turn that invoked the skill. It does not limit what the skill can call — every tool stays available, and the grant clears on the next user message.

To actually remove tools, use `disallowed-tools`. Listing tools in `allowed-tools` as documentation of "what this skill uses" is harmless but misleading; either grant deliberately or omit the field.

A project skill's grant applies even in untrusted folders, so a skill checked into a repo can grant itself broad access. Review this field in skills you did not write.

## Bundled scripts

A script's code never enters context — only its output. That makes a bundled script cheaper and more reliable than instructions telling the model to write the same code each run.

Bundle a script when the operation is deterministic, repeated, and worth being identical every time: validators, extractors, formatters, anything with a pass/fail result the model should react to. Skip it when the operation varies with context.

To run without a permission prompt, use `${CLAUDE_SKILL_DIR}` in both the body and a matching Bash rule, so the granted pattern is exactly the command the body tells the model to run:

```yaml
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/validate.sh *)
```

```markdown
Run `${CLAUDE_SKILL_DIR}/scripts/validate.sh <file>` and fix what it reports.
```

Scripts handle their own error cases rather than failing and leaving the model to guess. Justify constants in a comment — an unexplained timeout of 47 is a value nobody can safely change.

The same logic extends past scripts: a validator, a test suite, or a rubric file verifies quality more reliably than prose describing what good looks like.

## Directory layout and naming

```
my-skill/
├── SKILL.md          # required entrypoint
├── references/       # loaded on demand
└── scripts/          # executed, not loaded
```

The directory name becomes the `/command`; frontmatter `name` is only a display label (in plugin skills it sets the command's last segment). Keep them identical to avoid confusion.

Locations: `~/.claude/skills/` (personal, all projects), `.claude/skills/` (project). Personal overrides project on a name collision. Skills in nested `.claude/skills/` below the start directory load only after the model touches a file in that subtree.

## Invocation control

The default is that both the user and the model can invoke a skill. Two fields narrow it, and choosing correctly matters more than any wording inside the file:

- `disable-model-invocation: true` — user-only. For anything with side effects the model should not time on its own: deploy, commit, send. The description also leaves the always-loaded context, so this costs nothing at startup.
- `user-invocable: false` — model-only. For background knowledge that is not an action a user would ask for by name.
- `context: fork` — runs the skill in its own subagent, keeping its intermediate work out of the main conversation. Suits long, self-contained jobs that return a summary.

## Arguments

`$ARGUMENTS` expands to everything typed after the skill name; `$1`, `$2` take positions. Invoking with arguments when the body has no placeholder appends `ARGUMENTS: <input>` at the end, so a skill still sees them.

Prefer one argument slot over a set of flags. Every flag is a decision the model has to make, and most invented flags are never used.

## Portability

Only `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools` are in the Agent Skills spec. claude.ai uploads and the Skills API reject anything else with an unexpected-key error, and Claude Code-only body features such as `$ARGUMENTS` do not expand there.

If the skill is meant to travel, stay inside those six fields.
