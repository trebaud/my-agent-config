---
name: semgrep-audit
description: "White-box source code security auditor with semgrep integration. Runs semgrep scans, triages results to eliminate false positives, validates true positives via input-to-sink tracing, and proposes concrete remediations. Use when: auditing a local codebase for vulnerabilities, performing white-box security review, source code audit, semgrep triage, reviewing semgrep output, or when the user says 'audit this code', 'security review', 'source code review', 'run semgrep', 'find vulnerabilities in this repo', 'white-box audit'. Covers OWASP Top 10 and custom semgrep rules across all languages."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Agent, AskUserQuestion
license: Apache-2.0
metadata:
  version: 0.1.0
  author: trebaud
---

# Semgrep security audit

Run semgrep, triage every alert manually, and report only what's actually exploitable with a working code fix.

## Workflow

### Phase 1 -- Scan

```bash
bash scripts/scan.sh /path/to/target/repo
```

| # | Rule ID | Severity | File:Line | Matched snippet |
|---|---------|----------|-----------|-----------------|

### Phase 2 -- Triage

See `references/semgrep-triage.md`. Apply gates in order, discard with reason at each:

1. **Framework defense** -- auto-protected? Safe API already in use?
2. **Reachability** -- user-facing route? Input actually attacker-controlled?
3. **Context** -- read 30+ lines; sanitization semgrep missed? Dead code / tests?
4. **Severity gate** -- Medium+ if confirmed? Discard Low/Info unless chains up.

| # | Rule ID | File:Line | Verdict | Reason |
|---|---------|-----------|---------|--------|

### Phase 3 -- Validate

For each TRUE POSITIVE / NEEDS REVIEW:

1. Trace full data flow: entry point → transforms → dangerous sink (name every function)
2. Identify trust boundaries crossed
3. Test defense bypass (encoding tricks, type confusion, null bytes)
4. Assess concrete impact
5. Assign confidence: **Confirmed** | **Probable** | **Theoretical**

### Phase 4 -- Remediate

For each Confirmed/Probable: provide vulnerable snippet, fixed code, why it works. Prioritize by severity.

### Phase 5 -- Report

```
## [SEV] Finding #N: Title
**Source**: rule-id | manual  **Severity**: Critical/High/Medium  **Confidence**: ...
**CWE**: CWE-XXX  **File**: path:LINE  **Attack prerequisites**: ...

### Vulnerable code
[snippet with line numbers]

### Attack path
1. Attacker sends [input] to [endpoint]
2. Reaches [sink] at [file:line] without sanitization
3. Impact: [concrete impact]

### Remediation
[before/after code fix]
```

```
# Source code audit report
Repo: [name] | Stack: [lang/framework] | Config: semgrep p/owasp-top-ten + p/[language]

| Severity | Count |   Semgrep triage: N alerts, N TP, N FP, N needs-review
|----------|-------|
| Critical | N     |
| High     | N     |
| Medium   | N     |

[Findings]
Priority: Critical → High → Medium
```

---

## Hard rules

- Never triage without reading 30+ lines of context.
- No scanner-only findings — every reported vuln must survive manual triage.
- No Low/Info unless they chain to Medium+. No missing-header-only findings.
- Every finding must include a concrete code fix.
- If nothing survives triage: "No exploitable vulnerabilities identified. N alerts triaged as FP: [reasons]."
- Disclose triage reasoning for every discarded alert.

---

## Navigation

| Need | File |
|------|------|
| Triage decision tree | `references/semgrep-triage.md` |
| Severity classification | `references/severity-guide.md` |
