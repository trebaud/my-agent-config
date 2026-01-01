# The Cutting Pass

Run every test against every section of the draft. Each one either survives with a reason or gets deleted.

## Contents
- Does the model already know this?
- Does this example earn its place?
- Is this the only place that says it?
- Is this instruction or decoration?
- Is this authority real?
- Would a competent colleague need this?
- What to keep

## Does the model already know this?

The default answer is yes. Definitions of well-known frameworks, standard library usage, what a design pattern is, why testing matters, the meaning of an acronym in wide use — all of it is already in the weights.

What survives is the delta: how the model *misapplies* the known thing. Not the framework's categories, but the way it fills every category to look thorough until the padding destroys the signal. Not "write good commit messages", but the fact that it describes the diff instead of the reason.

Test: delete the section and imagine the output. If nothing changes, it was decoration.

## Does this example earn its place?

Detailed examples constrain exploration. That is the point when you need a specific shape, and a defect otherwise.

- **Keep**: output schemas, table formats, a required file layout, an input→output pair where style is the deliverable. These define a contract.
- **Cut**: syntax demonstrations of any widely used language, library, or diagram format. The model writes these fluently, and your version becomes a ceiling on what it produces.

## Is this the only place that says it?

Duplication is worse than absence. When SKILL.md and a reference both cover scoring, the model follows whichever it read last, and edits drift the two apart.

Pick the authoritative location — detail lives in the reference, the pointer lives in SKILL.md — and delete the other copy outright rather than compressing it.

## Is this instruction or decoration?

Cut on sight: motivational framing ("this is critical for success"), restated headings, transitions, summaries of what the section just said, and enumerations of options you are not recommending. Give one default with an escape hatch, never a menu.

## Is this authority real?

Any threshold, policy, or convention you did not get from the user or the codebase is invented. Invented policy reads as authoritative and quietly overrides the team's actual rules.

Either strike it, ask the user, or mark it plainly as an assumption the output must surface.

## Would a competent colleague need this?

The audience is a strong engineer new to *this* context — not to the field. They need your conventions, your gotchas, your file layout, the thing that bit you last quarter. They do not need the field's textbook.

## What to keep

After the cuts, a skill should be roughly:

- **Workflow** — the sequence and what done looks like at each step
- **Conventions** — the choices your team has already made, so they are not relitigated
- **Failure modes** — how this specific task goes wrong, stated as self-checks
- **Contracts** — output schemas and formats that must be exact
- **Gotchas** — what the codebase or domain does that surprises people

Anything that is not one of these is a candidate for deletion.
