---
name: debug
description: Test-first bug debugging system. Use when a user reports a bug, something doesn't work, or a regression is found. Creates reproducing tests first, then uses subagents to implement fixes proven by passing tests. Never attempts fixes without test coverage.
allowed-tools: Read, Grep, Glob, Bash, Agent, Write, Edit
---

# Debug - Test-First Bug Resolution

A systematic debugging approach that prioritizes test reproduction before attempting fixes, then uses specialized subagents to implement solutions proven by passing tests.

## Core Philosophy

> "Tests first, fixes second. A bug isn't fixed until the test passes."

Instead of jumping to solutions, this skill ensures:
1. **Reproducibility**: Create a failing test that captures the bug
2. **Isolation**: Understand the exact conditions that trigger the issue
3. **Proof**: Any fix must make the test pass
4. **Validation**: No regressions introduced by the fix

## When to Use

Invoke this skill when:
- User reports a bug or unexpected behavior
- Something "doesn't work" but the root cause is unclear
- Complex issues that need systematic investigation
- Regression bugs in existing functionality

## Workflow

### Phase 1: Bug Report Analysis

**Step 1: Gather Bug Details**

Use AskUserQuestion to collect:
1. **What happened**: Expected vs actual behavior
2. **How to reproduce**: Exact steps, inputs, environment
3. **When it occurs**: Specific conditions, timing, frequency
4. **Impact**: Severity, affected users, business impact

**Step 2: Initial Investigation**

1. Locate relevant code using Grep/Glob
2. Read related files to understand current implementation
3. Identify potential root cause areas
4. Check existing tests for similar scenarios

### Phase 2: Test-First Reproduction

**Step 3: Create Reproducing Test**

```markdown
## Bug Reproduction Test

**File**: `path/to/test/file.test.js`
**Description**: Test that reproduces [bug description]

```javascript
describe('[Bug Name]', () => {
  it('should reproduce the reported bug', async () => {
    // Arrange: Set up the conditions that trigger the bug
    const input = [specific input that causes bug];
    
    // Act: Execute the problematic code
    const result = await problematicFunction(input);
    
    // Assert: This assertion should currently FAIL
    expect(result).toBe([expected correct behavior]);
  });
});
```
```

**Step 4: Verify Test Fails**

Run the new test to confirm (detect the project's test runner from lockfiles/config):
```bash
[test-runner] -- --testNamePattern="should reproduce the reported bug"
```

Expected: Test fails with the exact bug behavior reported

### Phase 3: Subagent Coordination

**Step 5: Launch Analysis Subagent**

```bash
Task:
Analyze the failing test and identify the root cause in the codebase.

Focus on:
- Why the test fails (trace execution path)
- Where the logic diverges from expected behavior
- What specific code change is needed
- Potential side effects of the fix

Return: Specific location and nature of the fix needed.
```

**Step 6: Launch Fix Subagent**

```bash
Task:
Implement the minimal fix needed to make the test pass.

Constraints:
- Only change what's necessary for the test to pass
- Don't introduce new abstractions or patterns
- Follow existing code style and patterns
- Run tests after each change
- If tests fail, rollback and try a different approach

Return: The specific code changes made and confirmation the test passes.
```

**Step 7: Launch Validation Subagent**

```bash
Task:
Verify the fix doesn't break anything else.

Tasks:
- Run the full test suite
- Check for performance regressions
- Verify edge cases still work
- Look for related functionality that might be affected

Return: Confirmation that all tests pass and no regressions introduced.
```

### Phase 4: Final Verification

**Step 8: Complete Test Suite**

Run all tests to ensure no regressions (detect the project's test runner from lockfiles/config).

**Step 9: Manual Verification (Optional)**

If the bug had a user interface component:
- Manually test the original reproduction steps
- Confirm the expected behavior now occurs
- Check related functionality wasn't affected

## Output Format

```markdown
## Bug Resolution Summary

### Bug Report
- **Issue**: [Brief description]
- **Reporter**: [User who reported it]
- **Impact**: [Severity/affected areas]

### Reproduction Test
- **Test File**: `path/to/test/file.test.js`
- **Test Name**: `[descriptive test name]`
- **Status**: ✅ Created and confirmed failing

### Root Cause Analysis
- **Location**: `file:line` 
- **Issue**: [What was wrong]
- **Analysis Subagent**: [Findings]

### Fix Implementation
- **Changes Made**: [Summary of code changes]
- **Fix Subagent**: [Implementation details]
- **Test Result**: ✅ Now passes

### Validation
- **Full Test Suite**: ✅ All tests pass
- **Regression Check**: ✅ No regressions found
- **Manual Test**: ✅ Original issue resolved

### Files Modified
- `src/...` - [What was changed]
- `tests/...` - [Added test coverage]
```

## Subagent Templates

See @references/subagent-templates.md for analysis and fix implementation subagent prompt templates.

## Best Practices

### Test Writing Guidelines
- **Be specific**: Test exact conditions from bug report
- **Isolate variables**: Don't test multiple things at once
- **Clear assertions**: Expected vs actual should be obvious
- **Descriptive names**: Test name should explain the bug

### Fix Implementation Guidelines
- **Minimal changes**: Change only what's necessary
- **No overengineering**: Don't introduce patterns for one-off fixes
- **Consistent style**: Match existing code exactly
- **Immediate testing**: Run tests after each change

## Error Handling

| Situation | Action |
|-----------|--------|
| Test doesn't reproduce bug | Refine test with more specific conditions |
| Multiple possible causes | Narrow down with additional tests |
| Fix breaks other tests | Rollback and try different approach |
| Bug is in external dependency | Create workaround or update dependency |

## Notes

- Never skip the reproduction test phase
- Always verify the test fails before attempting fixes
- Use subagents for specialized tasks (analysis, implementation, validation)
- Keep fixes minimal and focused
- Document the complete resolution process for future reference