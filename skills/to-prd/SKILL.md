---
name: to-prd
description: "Convert a markdown PRD into prd.json format. Reads $PRD_INPUT and writes structured user stories to $PRD_OUTPUT."
---

# PRD Converter

Your job is to translate the markdown PRD at `$PRD_INPUT` into the JSON schema below and write the result to `$PRD_OUTPUT`. You may also, **if the user opts in**, append one refactoring story at the end of each epic.

Preserve every authored feature story exactly — **do not merge, split, reorder, or re-interpret them.** The only stories you may add are the per-epic refactoring stories described below, and only when the user asks for them; everything else is a faithful 1:1 conversion.

---

## Workflow

1. **Read** `$PRD_INPUT`.
2. **Ask** the user one question and STOP for their reply: *"Append a 'Refactor and harden' story at the end of each epic? These run quality checks (typecheck, tests, linting) on the epic's changed files so debt doesn't accumulate. (yes/no)"* Treat the answer as a yes/no flag for step 4. If they say yes, check if a `quality.json` file exists in the current working directory and collect its `checks` array — you'll turn each entry into an acceptance criterion in step 4.
3. **Convert** each authored story 1:1 (rules below), keeping epic groups in document order.
4. **Inject** one refactoring story as the last story of every epic (see "Refactoring stories") — **only if the user said yes in step 2.** If they declined, skip this step entirely.
5. **Assign `priority`** by final position in the ordered list (1-based); when refactoring stories are present, each runs right after its epic's feature stories.
6. **Write** the JSON to `$PRD_OUTPUT`.
7. **Validate**: run `bun run validate-prd.ts $PRD_OUTPUT`. If it exits non-zero, fix the JSON and re-validate. Loop until exit 0.
8. **Report** one line: `wrote N stories (F feature + R refactor across E epics), validated OK` (with `R = 0` if refactoring stories were declined).

Step 2 is the only question you ask. End the session after step 8.

---

## Output Schema

```json
{
  "project": "[Project Name]",
  "description": "[One-line feature description from PRD title/intro]",
  "userStories": [
    {
      "id": "US-001",
      "title": "[Story title]",
      "description": "As a [user], I want [feature] so that [benefit]",
      "acceptanceCriteria": ["Criterion 1", "Criterion 2", "Typecheck passes"],
      "priority": 1,
      "passes": false,
      "notes": "",
      "dependencies": [],
      "epic": "auth"
    }
  ]
}
```

Field rules enforced by `validate-prd.ts`:

- `id` matches `US-\d{3,}` (e.g. `US-001`), unique across the list.
- `priority` is a non-negative integer; lower = runs earlier.
- `passes` must be `false` in a freshly-generated PRD.
- `dependencies` (optional) must reference existing `US-###` ids with strictly lower `priority`.
- `epic` is required and non-empty.
- `acceptanceCriteria` has at least one item.

---

## Conversion Rules

### Top-level fields

- **`project`**: PRD title (strip leading `PRD:` / `# `).
- **`description`**: one-line summary from the PRD's Introduction/Overview. First sentence if multi-paragraph.

### Feature stories — preserve 1:1

For each `### US-NNN: ...` heading, emit exactly one JSON entry. Do **not** merge, split, or skip.

- **`id`**: copy from the heading. Re-number sequentially from `US-001` only if the markdown uses a non-conforming scheme.
- **`title`**: text after the `US-NNN:` prefix.
- **`description`**: the `**Description:**` line, verbatim.
- **`acceptanceCriteria`**: each `- [ ] ...` bullet under `**Acceptance Criteria:**`, prefix stripped, verbatim. Append `"Typecheck passes"` if missing.
- **`passes`**: always `false`. **`notes`**: always `""`.
- **`dependencies`**: from the `**Dependencies:**` line. `None`/missing → `[]`; comma-separated ids → array.
- **`epic`**: from the `**Epic:**` line (`EP-NNN — [Title]` → kebab-case slug of the title). No Epics section → `"main"` for every story.

### Priority

Assign `priority` by **final position** in the ordered list: walk the epics in document order and number `1, 2, 3, …` down the whole list. When refactoring stories were requested, emit each epic's feature stories then its refactoring story before moving to the next epic — this guarantees an epic's refactoring story has a higher priority number than (i.e. runs after) every feature story in that epic. When they were declined, just number the feature stories in document order.

---

## Refactoring stories

**Only if the user opted in at step 2.** Append **one** refactoring story as the last story of every epic. These keep debt from accumulating as the agent loop adds code — the quality checks live directly in these stories' acceptance criteria, so the builder runs them and the verifier confirms them like any other story.

The acceptance criteria are built from the `checks` array you read in step 2. **Turn each check into one acceptance criterion** of the form `Run the \`<name>\` check on the files changed in this epic: <guidance>`. Then append `"Typecheck passes"` and `"The full test suite passes"`. If `quality.json` defines **no** checks (or the file doesn't exist), fall back to a single generic criterion: `"Run the project linter on the files changed in this epic and resolve every finding"` plus the typecheck and test criteria.

For an epic with slug `<epic>` and feature stories `US-A … US-Z`, given checks `lint` and `arch`:

```json
{
  "id": "US-<next-free-number>",
  "title": "Refactor and harden: <Epic title>",
  "description": "As a maintainer, I want the code added in the <Epic title> epic to stay clean and architecturally sound, so that technical debt and structural drift do not accumulate as later epics build on it.",
  "acceptanceCriteria": [
    "Run the `lint` check on the files changed in this epic: <guidance from the lint check>",
    "Run the `arch` check on the files changed in this epic: <guidance from the arch check>",
    "Code added in this epic follows the project's established coding conventions.",
    "Typecheck passes",
    "The full test suite passes"
  ],
  "priority": "<final position>",
  "passes": false,
  "notes": "",
  "dependencies": ["US-A", "…", "US-Z"],
  "epic": "<epic>"
}
```

Rules for the injected story:

- **`acceptanceCriteria`**: one criterion per configured sensor (verbatim `guidance`), then typecheck and tests. No sensors configured → the generic fallback above.
- **`id`**: continue the `US-NNN` sequence past the highest id already used (one per epic, all unique). Zero-pad to at least 3 digits.
- **`dependencies`**: list every feature story id in the same epic (they all precede it, so they have lower priority — valid).
- **`epic`**: the same slug as the epic it closes.
- Scope all checks to **files changed in the epic**, not the whole repo — brownfield code outside the epic is left alone.
- If a project has a single implicit epic (`"main"`), still append exactly one refactoring story at the very end.

---

## Example

This example shows the output **when the user opted in** to refactoring stories, with `quality.json` defining two checks — `lint` (guidance: "Run `bun run lint` and clear every finding") and `arch` (guidance: "Run `bun run depcruise` and fix any layer violation or cycle"). If the user declined, the `US-003` and `US-004` "Refactor and harden" entries below would simply be absent and the feature stories renumbered accordingly.

**Input PRD excerpt:**
```markdown
# PRD: Task Status Feature

## Introduction
Add ability to mark tasks with different statuses.

## Epics
- **EP-001: Data model** — Persist status on tasks.
- **EP-002: Task UI** — Show and edit status inline.

## User Stories

### US-001: Task status schema and server actions
**Epic:** EP-001 — Data model
**Dependencies:** None
**Description:** As a developer, I need status stored in the DB and exposed via server actions.
**Acceptance Criteria:**
- [ ] Add status column: 'pending' | 'in_progress' | 'done' (default 'pending')
- [ ] Server action updateTaskStatus(id, status) persists change
- [ ] Typecheck passes

### US-002: Status badge and inline toggle on task list
**Epic:** EP-002 — Task UI
**Dependencies:** US-001
**Description:** As a user, I want to see and change task status from the list.
**Acceptance Criteria:**
- [ ] Each task row shows a colored status badge
- [ ] Inline dropdown saves immediately via server action
- [ ] Verify in browser using dev-browser skill
```

**Output prd.json:**
```json
{
  "project": "Task Status Feature",
  "description": "Add ability to mark tasks with different statuses.",
  "userStories": [
    {
      "id": "US-001",
      "title": "Task status schema and server actions",
      "description": "As a developer, I need status stored in the DB and exposed via server actions.",
      "acceptanceCriteria": [
        "Add status column: 'pending' | 'in_progress' | 'done' (default 'pending')",
        "Server action updateTaskStatus(id, status) persists change",
        "Typecheck passes"
      ],
      "priority": 1,
      "passes": false,
      "notes": "",
      "dependencies": [],
      "epic": "data-model"
    },
    {
      "id": "US-003",
      "title": "Refactor and harden: Data model",
      "description": "As a maintainer, I want the code added in the Data model epic to stay clean and architecturally sound, so that technical debt and structural drift do not accumulate as later epics build on it.",
      "acceptanceCriteria": [
        "Run the `lint` check on the files changed in this epic: Run `bun run lint` and clear every finding.",
        "Run the `arch` check on the files changed in this epic: Run `bun run depcruise` and fix any layer violation or cycle.",
        "Code added in this epic follows the project's established coding conventions.",
        "Typecheck passes",
        "The full test suite passes"
      ],
      "priority": 2,
      "passes": false,
      "notes": "",
      "dependencies": ["US-001"],
      "epic": "data-model"
    },
    {
      "id": "US-002",
      "title": "Status badge and inline toggle on task list",
      "description": "As a user, I want to see and change task status from the list.",
      "acceptanceCriteria": [
        "Each task row shows a colored status badge",
        "Inline dropdown saves immediately via server action",
        "Verify in browser using dev-browser skill",
        "Typecheck passes"
      ],
      "priority": 3,
      "passes": false,
      "notes": "",
      "dependencies": ["US-001"],
      "epic": "task-ui"
    },
    {
      "id": "US-004",
      "title": "Refactor and harden: Task UI",
      "description": "As a maintainer, I want the code added in the Task UI epic to stay clean and architecturally sound, so that technical debt and structural drift do not accumulate as later epics build on it.",
      "acceptanceCriteria": [
        "Run the `lint` check on the files changed in this epic: Run `bun run lint` and clear every finding.",
        "Run the `arch` check on the files changed in this epic: Run `bun run depcruise` and fix any layer violation or cycle.",
        "Code added in this epic follows the project's established coding conventions.",
        "Typecheck passes",
        "The full test suite passes"
      ],
      "priority": 4,
      "passes": false,
      "notes": "",
      "dependencies": ["US-002"],
      "epic": "task-ui"
    }
  ]
}
```

Note how `US-003` (Data model refactor) slots in at priority 2 — right after its epic's only feature story and before the Task UI epic begins.

---

## Pre-write checklist

- [ ] One JSON story per markdown story (no merging, splitting, or dropping feature stories).
- [ ] The user was asked once whether to append refactoring stories, and their answer was honored.
- [ ] If opted in: exactly one refactoring story appended at the end of each epic, IDs continue the `US-NNN` sequence and are unique, each depends on its epic's feature stories and shares their epic slug. If declined: no refactoring stories were added.
- [ ] Feature story IDs preserved from markdown.
- [ ] `priority` assigned by final position; when refactoring stories are present, each runs after its epic's feature stories.
- [ ] `dependencies` parsed from the `**Dependencies:**` line; `None` → `[]`.
- [ ] `epic` parsed and slugified; `"main"` if no Epics section.
- [ ] Every story has `passes: false`, `notes: ""`, and "Typecheck passes" in its acceptance criteria.
- [ ] Validator passes.
