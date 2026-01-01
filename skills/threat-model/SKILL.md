---
name: threat-model
description: Builds a threat model for a system, feature, or codebase — diagrams it with trust boundaries, identifies what can go wrong via STRIDE, assigns mitigations, and validates coverage into a THREAT_MODEL.md. Use when the user asks to threat model something, map an attack surface, run a security design review, apply STRIDE, or asks "what could go wrong with this design". Triggers like "threat model this service", "STRIDE analysis", "security review of this architecture".
allowed-tools: Bash, Read, Grep, Glob, Write, AskUserQuestion
metadata:
  version: 1.0.0
---

# Threat Model

Four questions, in order: **What are we building? What can go wrong? What do we do about it? Did we do it?**

Output is one file, `THREAT_MODEL.md`, in the target directory.

**Parameters** — `<target>`: path, service, or feature (default: current repo). `--scope <boundary>`: limit to one component, e.g. `api/auth`.

## 1. Scope

Settle with the user, and state at the top of the model: what is in scope and what is explicitly out; which assets matter (data, funds, credentials, availability); who the threat agents are (anonymous internet, authenticated user, insider, compromised dependency, cloud operator).

An unbounded scope produces nothing actionable. Narrow it before continuing.

## 2. Model the system

Read the code — entry points, data stores, external dependencies, privilege levels. Draw a Mermaid data-flow diagram with **trust boundaries as subgraphs**, and annotate each flow with what crosses it: authn method, data classification, direction.

Every arrow crossing a boundary is where threats live, so placing the boundaries is the step that decides whether the model is worth anything. See [where boundaries actually sit](references/threat-analysis.md#where-trust-boundaries-actually-are) — they follow privilege changes, not network topology.

## 3. Identify threats

Two passes over the boundary crossings: a mechanical STRIDE pass over every flow, store, process, and external entity, then a creative pass for what the checklist cannot see — business-logic abuse, chained low-severity issues, the deploy path.

Read [references/threat-analysis.md](references/threat-analysis.md) first for the failure modes that make a threat model look complete while being wrong.

## 4. Prioritize

Score likelihood and impact per [references/threat-analysis.md](references/threat-analysis.md#scoring). Rank by severity, and ask the user where the release-blocking line sits rather than assuming one.

## 5. Mitigate

Give every threat a disposition — **mitigate**, **eliminate** (drop the feature/flow), **transfer**, or **accept** — plus a named owner and, for mitigations, the file or config where the control lives. "Accepted" with no owner is not a decision.

## 6. Validate

Before writing the file, confirm: every boundary crossing was considered; every threat has a disposition and owner; every claimed mitigation exists at a file and line you read; the diagram matches the code as it is, not as intended. Re-check the model against the failure modes in [references/threat-analysis.md](references/threat-analysis.md#failure-modes) — particularly whether the threat distribution is suspiciously even. State any gap you could not close.

## Output

```markdown
# Threat Model — <system>
Date · Scope · Out of scope · Assets · Threat agents

## System model
<mermaid diagram>
| Flow | Crosses | Authn | Data |

## Threats
| ID | Flow | STRIDE | Threat (attacker goal) | Likelihood | Impact | Severity | Disposition | Control | Owner |
| T1 | U→API | S | Attacker forges session cookie to act as another user | Med | High | High | Mitigate | Signed cookies, `auth/session.ts:42` | @team |

## Traceability
Attacker goal → control → where enforced → how tested

## Gaps and accepted risk
```

A threat you cannot tie to a specific flow does not go in the table. Every row names a file, a control, and an owner — never "consider security best practices". Flag anything you inferred without reading the code.
