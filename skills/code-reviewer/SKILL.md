---
name: code-reviewer
description: Comprehensive code review combining quality, security, and maintainability checks. Use when reviewing code before a pull request, after completing a feature, after fixing bugs, or when the user asks for a code review.
allowed-tools: Read, Grep, Glob, Bash
---

# Code Reviewer

Perform comprehensive code reviews covering quality, security, performance, and maintainability.

## When to Use

Invoke this skill:
- After completing a feature implementation
- Before creating a pull request
- When refactoring existing code
- After fixing bugs to ensure no regressions

## Review Process

### Step 1: Gather Context

1. Identify files changed using `git diff --name-only HEAD~1` or `git diff --staged --name-only` or `git diff master...HEAD`
2. Read each changed file to understand the modifications
3. Understand the purpose of the changes

### Step 2: Security Analysis

**CRITICAL**: Check for security vulnerabilities in the changed code:
- Injection flaws (SQL, NoSQL, command, LDAP)
- Authentication/authorization issues
- Sensitive data exposure
- Security misconfigurations
- Known vulnerable dependencies

### Step 3: Code Quality Review

Check for these quality issues:

#### Logic & Correctness
- [ ] Edge cases handled
- [ ] Null/undefined checks where needed
- [ ] Error handling is appropriate
- [ ] No obvious bugs or logical errors

#### Style & Consistency
- [ ] Follows existing codebase patterns
- [ ] Consistent naming conventions
- [ ] No magic numbers/strings
- [ ] Appropriate use of TypeScript types

#### Performance
- [ ] No N+1 query issues
- [ ] No unnecessary loops or iterations
- [ ] Appropriate caching considerations
- [ ] No memory leaks (event listeners, timers)

#### Maintainability
- [ ] Code is self-documenting
- [ ] Complex logic has comments explaining "why"
- [ ] Functions have single responsibility
- [ ] No deep nesting (max 3 levels)

### Step 4: Test Coverage

1. Check if tests exist for the changes
2. Verify tests cover:
   - Happy path
   - Error cases
   - Edge cases
3. Run tests if available (detect the project's test runner from lockfiles/config)

### Step 5: Dependencies Check

If new dependencies were added:
- Check for known vulnerabilities using the project's package manager audit command
- Verify the package is actively maintained
- Check bundle size impact

## Output Format

```markdown
## Code Review Summary

### Files Reviewed
- `path/to/file1.ts`
- `path/to/file2.ts`

### Security Findings
[Security vulnerabilities and concerns found during review]

### Quality Issues

#### Critical
- [ ] **[file:line]** - [Issue description]
  - **Impact**: [Why this matters]
  - **Fix**: [How to resolve]

#### Warnings
- [ ] **[file:line]** - [Issue description]
  - **Suggestion**: [Improvement recommendation]

#### Suggestions
- [ ] **[file:line]** - [Minor improvement]

### Test Coverage
- Status: [Covered/Partial/Missing]
- [Notes on test quality]

### Overall Assessment
[Brief summary: Ready to merge / Needs changes / Major concerns]
```

## Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| Critical | Security vuln, data loss, crash | Must fix before merge |
| Warning | Bugs, performance, bad practices | Should fix |
| Suggestion | Style, minor improvements | Optional |


## Notes

- Focus on significant issues, not nitpicking
- Provide actionable feedback with solutions
- Acknowledge good patterns and improvements
- Be constructive, not critical
