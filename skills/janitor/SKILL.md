---
name: janitor
description: >-
  Refactor a codebase using Clean Architecture and Clean Code principles — fix
  dependency violations, separate concerns, improve code quality, push
  infrastructure outward. Use when: the user asks to "janitor" code, refactor,
  reorganize layers, fix dependency violations, separate concerns, clean up
  code, or decouple business logic from infrastructure.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, Agent
---

# Janitor

Read **`references/clean-architecture-guide.md`** and **`references/clean-code-guide.md`** before starting.

## Workflow

### 1. Audit

- Map where entities, business logic, persistence, and presentation code live
- Trace import directions, list dependency rule violations
- Flag clean code issues: long functions/files, deep nesting, mixed concerns, generic naming, duplicated logic, custom code that should be a library
- Present a **ranked list** (highest-impact first) with `file:line` references

### 2. Plan

- For each finding: what moves where, what gets extracted, split, renamed, or replaced
- Flag breaking changes and get user sign-off before executing

### 3. Execute (incremental, tests between each step)

1. Fix dependency direction violations: extract interfaces, inject dependencies, move code to the correct layer
2. Separate mixed concerns: pull business logic out of controllers/UI, pull DB queries out of business logic
3. Clean up code quality: decompose long functions/files, flatten deep nesting, replace generic names with business-specific ones, deduplicate, swap custom code for libraries where appropriate

Run tests after each step.

### 4. Verify

- No circular or outward-pointing dependencies remain
- Linter/build passes, all existing tests still green

## Hard Rules

- One boundary at a time, run tests between each move
- Never delete or break existing tests
- Don't rename public APIs unless it's the only way to fix a violation
- Only extract interfaces when there's a concrete need, not speculatively
- Keep existing folder names. Don't rename folders to Clean Architecture jargon (`domain/`, `ports/`, `adapters/`, etc.). Fix dependency directions within the project's existing conventions. Only create new folders when there's no reasonable existing location.
- Get user sign-off on the plan before executing
