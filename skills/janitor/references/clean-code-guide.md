# Clean Code Guide

## General Principles

- **Early return pattern**: Use early returns over nested conditions
- Avoid duplication — create reusable functions and modules
- Decompose long functions (>80 LOC) and files (>200 LOC)
- Max 3 levels of nesting; functions under 50 lines

## Library-First Approach

- Search for existing libraries before writing custom code
- Custom code is justified for: unique business logic, performance-critical paths, security-sensitive code, or when external deps are overkill
- Every line of custom code is a liability

## Naming & Design

- **Avoid** generic names: `utils`, `helpers`, `common`, `shared`
- **Use** business-specific names: `OrderCalculator`, `UserAuthenticator`
- Each module should have a single, clear purpose
- Separate business models from technical concerns
- Keep business logic independent of frameworks

## Anti-Patterns

- Mixing business logic with UI components
- Database queries directly in controllers
- `utils.js` with 50 unrelated functions
- Building custom solutions when established libraries exist (auth, state management, validation)

## Code Quality

- Proper error handling with typed catch blocks
- Break complex logic into smaller, reusable functions
- Keep files focused and under 200 lines
