# Clean Architecture Guide

## Core Principle

The **Domain layer** is the center of your application. All other layers depend on it, not the reverse.

## Layer Structure (Inside -> Out)

### 1. Domain Layer (Core)
- Business entities, value objects, domain events
- Business rules and invariants
- Repository interfaces (abstractions only, no implementations)
- **Zero external dependencies** — knows nothing about other layers

### 2. Application Layer
- Use cases / application services that orchestrate domain logic
- Defines interfaces for infrastructure needs (ports)
- References Domain only
- Contains DTOs, commands, queries, validators

### 3. Infrastructure Layer (Outer)
- Implements interfaces defined in Domain/Application (adapters)
- Database access, file I/O, external APIs, email, messaging
- Framework-specific code, ORM configurations
- **Depends inward** on Application and Domain

### 4. Presentation Layer (Outer)
- Controllers, API endpoints, CLI handlers, UI
- Maps external requests to application commands/queries
- **Depends inward** on Application and Domain

## Dependency Rule

Dependencies flow **inward only**:

```
Presentation -> Application -> Domain
Infrastructure -> Application -> Domain
```

Never: Domain -> Application, Domain -> Infrastructure, Application -> Infrastructure

## Key Patterns

| Pattern | Purpose |
|---|---|
| **Repository interfaces** | Domain defines the contract; Infrastructure implements persistence |
| **Dependency Injection** | Outer layers inject concrete implementations into inner layer abstractions |
| **DTOs / Mappers** | Each layer boundary uses its own data shapes — no leaking ORM models into domain |
| **CQRS (optional)** | Separate read/write paths through Application layer |

## Violations to Detect

- Domain importing infrastructure packages (ORMs, HTTP libs, framework types)
- Business logic living in controllers or infrastructure services
- Direct database/API calls without an abstraction boundary
- Entities shaped by persistence concerns (ORM annotations in domain, DB column names as field names)
- Application layer returning infrastructure types (DB models, HTTP responses)
- Circular dependencies between layers

## Practical Benefits

- Swap databases, frameworks, or APIs without touching business logic
- Domain doesn't know how it's stored or presented
- Domain and application logic are testable without infrastructure
- Business rules stay stable when peripheral tech changes
