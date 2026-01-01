---
name: refactor
description: Performs safe refactoring with automated test verification. Use when simplifying overengineered code, removing unnecessary abstractions, eliminating duplication, or cleaning up hard-to-understand code. Makes incremental changes with test runs after each step.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Refactor

Simplify code while maintaining functionality and test coverage. Before refactoring, evaluate whether existing patterns are warranted by checking if the complexity serves a genuine purpose (reused 3+ times, concrete bug risk, measurable performance need, or consistency with established codebase patterns).

## When to Use

- KISS violations detected
- Overengineered patterns
- Duplicate code
- Hard-to-understand code

## Process

### 1. Analyze

Read code, identify complexity:
- Unnecessary patterns (Factory, Strategy with single impl)
- Abstract classes with single implementation
- Complex inheritance
- Overly generic functions
- Unnecessary indirection

### 2. Propose

Explain:
- What's complex
- Simpler version
- Why safe to refactor
- Tests that verify correctness

### 3. Implement

- Small incremental changes
- Run tests after each change
- Rollback if tests fail
- Continue until complete

### 4. Verify

- Run full test suite
- Check no behavior changes
- Verify performance not degraded
- Log changes

## Strategies

### Flatten Inheritance to Functions

**Before**:
```typescript
abstract class BaseService {
  protected async fetch(url: string): Promise<any> { }
}
class UserService extends BaseService {
  async getUser(id: string): Promise<User> {
    return this.fetch(`/api/users/${id}`);
  }
}
```

**After**:
```typescript
async function getUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

### Inline Unnecessary Wrappers

**Before**:
```typescript
class ConfigManager {
  private config: Record<string, string> = {};
  get(key: string): string { return this.config[key]; }
  set(key: string, value: string): void { this.config[key] = value; }
}
// Used in exactly one place
const configManager = new ConfigManager();
```

**After**:
```typescript
const config: Record<string, string> = {};
```

## Safety Rules

1. Always run tests after changes
2. Never change behavior, only implementation
3. Rollback immediately if tests fail
4. Document why refactor is simpler
5. Only refactor if tests exist

## Output

```
## Refactoring Analysis
File: [path] (Lines: X-Y)

Issue: [Description]

Simplification: [Brief description]

Changes:
- [Change 1]
- [Change 2]

Verification:
- Tests: ✅/❌
- Behavior: ✅/❌
- Performance: ✅/⚠️/❌
```

## Notes

- Delete code > clever code
- Three similar lines > premature abstraction
- If unsure, don't refactor
- Always ask: "Is this simpler?"
