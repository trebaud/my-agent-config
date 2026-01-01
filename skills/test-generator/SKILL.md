---
name: test-generator
description: Generates unit and integration tests for modified or added code following existing project patterns. Use when new files are added without tests, modified files lack test coverage, or when the user asks to generate or write tests for a file.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Test Generator

Generate unit and integration tests for recently modified or added code by analyzing and following existing test patterns.

## When to Trigger

### Proactive (Automatic)
- **New files added without tests** - e.g., Added `src/service.ts` but no `src/service.test.ts`
- **Modified files with missing test coverage** - Functionality changed but no new tests added

**Never suggest tests for unchanged parts of the codebase.**

### Explicit User Request
- "generate tests"
- "write tests for this"
- "add test coverage"
- "test this file"

## Workflow

1. **Identify changed files** - Use git diff to find modified/added source files
2. **Check test coverage** - For each file, check if test file exists and if it covers changes
3. **Discover existing patterns** - Analyze existing tests to understand framework, structure, naming, mocking style
4. **Analyze code** - Identify exported functions/methods, what changed, dependencies
5. **Prioritize** - Focus on: public APIs, business logic, error handling, input validation
6. **Generate tests** - Happy path, error paths, edge cases (1-2 per function)
7. **Present to user** - Show what's missing before generating
8. **Write tests** - Follow existing patterns, update or create test files

## Test Generation Rules

For each function/method requiring tests:
- **Happy path** - Valid input → expected output
- **Error path** - Invalid input, thrown exceptions, error returns
- **Edge cases** - Boundary values, empty/null inputs (1-2 for critical functions)
- **Complex scenarios** - Multiple conditions, async behavior (only if complex)

Follow existing patterns for:
- Framework (Jest, Vitest, pytest, etc.)
- Test structure (describe blocks, before/after hooks)
- Assertion style (expect().toBe(), assert, etc.)
- Mocking approach (vi.mock(), jest.mock(), @patch, etc.)
- File location (co-located, separate directory, nested)
- Naming conventions

## Notes

- **Never overwrite** existing test files without user confirmation
- **Always follow** existing test patterns from the codebase
- **Focus on critical paths** - don't test trivial code
- **Use meaningful test names** that describe what and why
- **Keep tests simple** - one assertion per test when possible
- **Mock external dependencies** - tests should be isolated
- **Run tests after generation** to verify they work
- **Ask user** before overwriting existing test files
