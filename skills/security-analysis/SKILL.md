---
name: security-analysis
description: "Manual white-box API security reviewer using OWASP API Top 10. Maps attack surface, traces data flows from entry points to sensitive sinks, triages for exploitability, and reports only confirmed vulnerabilities with code fixes. Use when: reviewing PRs for security, performing vulnerability assessments, analyzing bug bounty reports against the codebase, manual API security audit, or when the user says 'security review this API', 'check for auth bugs', 'review this endpoint'. Covers OWASP API Security Top 10 2023."
allowed-tools: Read, Grep, Glob, Bash, Agent, WebFetch, AskUserQuestion
license: Apache-2.0
metadata:
  version: 0.2.0
  author: trebaud
---

# API security analysis

Trace data flows by hand. Only report what's actually exploitable, with a code fix.

## Workflow

### Phase 1 -- Reconnaissance

Identify stack, framework, auth scheme, and scope.

1. Read entry points: routes, controllers, middleware, API gateway config
2. Identify auth mechanism (JWT, session, API key) and where it's enforced
3. Map sensitive operations: payments, user data, admin functions, external API calls
4. Note framework-provided defenses (CSRF tokens, ORM parameterization, auto-escaping)

Output:
```
Stack: [lang/framework] | Auth: [mechanism] | Scope: [endpoints/files reviewed]
```

### Phase 2 -- Attack surface mapping

For each endpoint in scope, classify by OWASP API Top 10 risk. See `references/owasp-api-top-10.md`.

| Endpoint | Method | Auth | OWASP risk | Notes |
|----------|--------|------|------------|-------|

Prioritize: unauthenticated endpoints, endpoints handling object IDs, endpoints accepting user-controlled URLs or file paths, financial/admin operations.

### Phase 3 -- Triage

For each candidate finding, apply gates in order. Discard with reason at each:

1. **Framework defense** -- auto-protected? Safe API already in use?
2. **Reachability** -- user-facing route? Input actually attacker-controlled?
3. **Context** -- read 30+ lines; sanitization missed by pattern match? Dead code / tests?
4. **Exploitability** -- requires unrealistic conditions? (admin-only, physical, MitM)
5. **Severity gate** -- Medium+ if confirmed? Discard Low unless it chains to Medium+.

Use `references/owasp-api-top-10.md` triage questions for class-specific checks.

For each surviving finding:
1. Trace full data flow: entry point -> transforms -> dangerous sink (name every function)
2. Identify trust boundaries crossed
3. Test defense bypass (encoding tricks, type confusion, null bytes)
4. Assess concrete impact -- what can the attacker actually DO?
5. Assign confidence: **Confirmed** | **Probable** | **Theoretical**

| # | Endpoint | OWASP ID | Verdict | Reason |
|---|----------|----------|---------|--------|

### Phase 4 -- Remediate

For each Confirmed/Probable: provide vulnerable snippet, fixed code, why it works. Prioritize by severity. See `references/severity-guide.md` for classification.

### Phase 5 -- Report

```
# API security analysis report
Repo: [name] | Stack: [lang/framework] | Scope: [N endpoints reviewed]

| Severity | Count |
|----------|-------|
| Critical | N     |
| High     | N     |
| Medium   | N     |

## [SEV] Finding #N: Title
**OWASP**: API[1-10]  **Severity**: Critical/High/Medium  **Confidence**: Confirmed/Probable/Theoretical
**CWE**: CWE-XXX  **File**: path:LINE  **Attack prerequisites**: ...

### Vulnerable code
[snippet with line numbers]

### Attack path
1. Attacker sends [input] to [endpoint]
2. Reaches [sink] at [file:line] without sanitization
3. Impact: [concrete impact -- what does the attacker gain?]

### Remediation
[before/after code fix]

Priority: Critical -> High -> Medium
```

---

## Hard rules

- Never triage without reading 30+ lines of context.
- No pattern-match-only findings -- every reported vuln must survive manual triage.
- No Low unless it chains to Medium+. No missing-header-only findings.
- Every finding must include a concrete code fix.
- Business impact over technical severity -- high CVSS with zero business damage = LOW.
- If nothing survives triage: "No exploitable vulnerabilities identified. N candidates triaged as FP: [reasons]."
- Disclose triage reasoning for every discarded candidate.

