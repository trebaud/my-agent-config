---
name: create-skill
description: Writes or revises an agent skill — SKILL.md plus reference files — targeting what the model gets wrong rather than restating what it already knows. Use when the user wants to create a new skill, turn a repeated workflow or article into a skill, revise an existing skill, fix one that does not trigger, or trim one that has grown bloated. Triggers like "make this a skill", "create a skill for X", "improve this skill", "my skill isn't triggering", "turn this article into a skill".
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch, AskUserQuestion
metadata:
  version: 1.0.0
---

# Create Skill

A skill is a correction to default behavior, not a tutorial. The model is already competent; a skill exists to supply the judgment, conventions, and failure modes it cannot derive from the task alone.

Newer models need far less scaffolding than older prompting habits assume — Anthropic cut over 80% of Claude Code's system prompt with no measured loss. Write accordingly: state the objective and the quality bar, then trust the model on execution.

## 1. Find the gap

Before writing anything, establish what actually goes wrong without the skill. Either run the task bare and watch the output, or ask the user what they keep having to correct.

Name three specific failures. If you cannot, there is no skill here — the model already handles it, and the file will be pure token cost.

Sources like an article or doc give you the *topic*, never the gap. Such a source teaches its subject's standard framework, which the model already has; the gap is in how the model applies that framework badly. Extract the gap, not the summary.

## 2. Draft the workflow

Write the minimum that closes those three gaps. Steps state what to achieve and what "done" looks like, not keystrokes.

Set freedom to match fragility: prose for tasks with many valid paths, an exact command for operations that break when varied. Most steps want prose.

## 3. Cut

The pass that decides quality. Apply every test in [references/cutting-tests.md](references/cutting-tests.md) — the model knows more than the draft assumes, and half of a first draft is usually restatement.

Expect to remove 30–50%. If nothing was cut, the pass was not run.

## 4. Structure

A skill is a directory: SKILL.md plus whatever it loads on demand — reference docs, templates, example outputs, scripts.

- **SKILL.md under 500 lines**; well under, for most skills. Split when it grows, not preemptively.
- **References one level deep.** SKILL.md links to every reference file directly. Nested links get partially read.
- **Name reference files by content**, not by the well-known term inside them. The filename should say what the reader gets; the framework's acronym rarely is the point.
- **A reference file over 100 lines needs a contents list** at the top.
- **Bundle a script instead of describing code to write** when the operation is deterministic and repeated — a script's code never enters context, only its output. Say which you mean: "run `x.py`" versus "see `x.py` for the algorithm".
- **Prefer a checkable artifact over prose about quality** — a validator, a test suite, a rubric file, an example of correct output. Prose describing what good looks like is the weakest form.

[references/mechanics.md](references/mechanics.md) covers the Claude Code specifics that change these decisions: script invocation without permission prompts, layout, and what travels to other surfaces.

## 5. Set the interface

Two choices outrank anything written in the body:

- **Who can invoke it.** Side-effecting workflows should be user-only; background knowledge should be model-only; most skills are both. See [invocation control](references/mechanics.md#invocation-control).
- **What it takes as input.** One argument slot beats a set of flags.

Then the description — the one field that decides whether the skill ever loads. Third person, both halves — what it does and when to use it — plus the literal phrases a user would type.

```
description: <what it does, concretely>. Use when <situations>. Triggers like "<phrase>", "<phrase>".
```

Then check it against the sibling skills in the same collection: if two descriptions overlap, the wrong one will fire. Make the boundary explicit in whichever is narrower.

## 6. Verify

- Frontmatter: `name` ≤64 chars, lowercase/numbers/hyphens, no `claude` or `anthropic`; `description` ≤1024 chars. Note `allowed-tools` grants permission rather than restricting it — do not use it to document which tools the skill happens to call.
- Instructions that must hold for a whole task are written as standing rules. The file is read once and stays in context; it is not re-read per turn.
- Every file link resolves; all paths use forward slashes; bundled scripts are executable and run from a clean checkout.
- Match the collection: naming pattern, frontmatter keys, section shape, prose voice. A skill that reads differently from its neighbors is harder to maintain.
- Register it wherever the collection indexes skills (README table, index file).
- Run it fresh on a real task. Watch what the model skips, re-reads, or ignores — an unread reference file is a signal to delete or promote it, not to add emphasis.

## Anti-patterns

- **Restating public knowledge.** The most common way a skill wastes its budget.
- **Inventing authority.** A threshold or policy you did not get from the user or the codebase reads as though the team set it. Ask, or have the skill surface it as an assumption.
- **Illustrative examples.** An example that shows syntax the model knows narrows its exploration for nothing. Keep only examples that define a contract — an output schema, a required format.
- **Parameters nobody uses.** Every flag is a decision the model must make. Ship two, not six.
- **Saying it twice.** One authoritative location per instruction. Duplication between SKILL.md and a reference means the model follows whichever it read last.
- **Dated content.** No "as of 2026", no "the new API". Put superseded material under a collapsed *Old patterns* heading or drop it.
