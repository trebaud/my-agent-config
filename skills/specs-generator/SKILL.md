---
name: specs-generator
description: Creates comprehensive SPECS.md specification files for new features. Use when the user wants to create specs, specifications, feature documentation, or design documents. Helps flesh out scope, implementation details, and design choices through interactive questioning.
allowed-tools: Read, Grep, Glob, Write, AskUserQuestion
---

# Feature Specification Generator

Generate comprehensive SPECS.md files for features by gathering requirements through structured questioning.

## Instructions

When this skill is invoked, follow these steps:

### Step 1: Initial Context Gathering

Use the AskUserQuestion tool to understand the feature at a high level:

1. **Feature Name & Summary**: Ask for a brief description of the feature
2. **Problem Statement**: What problem does this feature solve?
3. **Target Users**: Who will use this feature?

### Step 2: Scope Definition

Use AskUserQuestion to clarify scope:

1. **Core Requirements**: What are the must-have functionalities?
2. **Out of Scope**: What should explicitly NOT be included?
3. **Dependencies**: What existing systems/features does this depend on?

### Step 3: Implementation Details

Gather technical details:

1. **Technical Approach**: Preferred implementation strategy
2. **Data Model Changes**: Any database/schema changes needed?
3. **API Changes**: New endpoints or modifications to existing ones?
4. **Integration Points**: External services or internal systems to integrate with

### Step 4: Design Choices

Explore design decisions:

1. **Trade-offs**: Ask about any known trade-offs (performance vs simplicity, etc.)
2. **Alternatives Considered**: What other approaches were considered?
3. **Constraints**: Any technical or business constraints to consider?

### Step 5: Edge Cases & Error Handling

1. **Edge Cases**: What edge cases should be handled?
2. **Error Scenarios**: How should errors be handled?
3. **Rollback Strategy**: What happens if something goes wrong?

### Step 6: Testing & Validation

1. **Acceptance Criteria**: How do we know the feature is complete?
2. **Testing Strategy**: Unit tests, integration tests, manual testing?

### Step 7: Generate SPECS.md

After gathering all information, generate a SPECS.md file using the template below.

## SPECS.md Template

```markdown
# Feature: [Feature Name]

## Overview

### Summary
[Brief description of the feature]

### Problem Statement
[What problem does this feature solve?]

### Target Users
[Who will use this feature?]

## Scope

### In Scope
- [Core requirement 1]
- [Core requirement 2]
- ...

### Out of Scope
- [Explicitly excluded item 1]
- [Explicitly excluded item 2]
- ...

### Dependencies
- [Dependency 1]
- [Dependency 2]
- ...

## Technical Design

### Architecture Overview
[High-level description of the technical approach]

### Data Model Changes
[Database/schema changes, if any]

### API Changes
[New or modified endpoints]

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | /api/... | ... |

### Integration Points
[External services or internal systems]

## Design Decisions

### Trade-offs
[Known trade-offs and why they were made]

### Alternatives Considered
[Other approaches that were considered and why they were rejected]

### Constraints
[Technical or business constraints]

## Edge Cases & Error Handling

### Edge Cases
- [Edge case 1]: [How it's handled]
- [Edge case 2]: [How it's handled]

### Error Scenarios
- [Error 1]: [How it's handled]
- [Error 2]: [How it's handled]

### Rollback Strategy
[What happens if deployment fails or feature needs to be disabled]

## Testing Strategy

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- ...

### Testing Approach
- **Unit Tests**: [What will be unit tested]
- **Integration Tests**: [What will be integration tested]
- **Manual Testing**: [What requires manual verification]

## Implementation Plan

### Phase 1: [Phase Name]
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Phase Name]
- [ ] Task 1
- [ ] Task 2

## Open Questions
- [Any unresolved questions that need answers]

## References
- [Link to related docs, PRs, or discussions]
```

## Guidelines for Questioning

1. **Be Adaptive**: Skip questions that aren't relevant based on previous answers
2. **Suggest Options**: When asking about technical choices, provide common options as suggestions
3. **Iterate**: If answers are vague, ask follow-up questions for clarity
4. **Keep Context**: Reference previous answers to build a coherent spec
5. **Limit Questions**: Group related questions together (max 4 questions per AskUserQuestion call)
6. **Provide Defaults**: Suggest sensible defaults when the user might not have strong preferences

## Example Question Flow

First question batch:
- "What is the feature name and a brief summary?"
- "What problem does this feature solve for users?"

Second question batch:
- "What are the must-have requirements? (List the core functionality)"
- "What should be explicitly out of scope for this version?"

Continue based on the feature type and user responses...

## Output

After gathering all necessary information, write the SPECS.md file to the current working directory (or a location specified by the user). Confirm with the user before writing if there's an existing SPECS.md file.
