# Semgrep triage -- false positive elimination

## Triage decision tree

Walk top-to-bottom. First match wins.

```
Alert received
  |
  +--> Tests, fixtures, mocks, or dev-only paths?
  |      YES --> DISCARD (not production code)
  |
  +--> Dead/unreachable code? (no route, no caller, feature-flagged off)
  |      YES --> DISCARD
  |
  +--> Framework auto-protects this class? Using the safe API?
  |      YES, safe API --> DISCARD (framework-protected)
  |      YES, unsafe API --> NEEDS REVIEW (opted out of protection)
  |
  +--> Input actually attacker-controlled?
  |      NO  --> DISCARD (server-generated, hardcoded, internal-only)
  |      YES --> Continue
  |
  +--> Sanitization between source and sink? (read 30+ lines)
  |      YES, not bypassable --> DISCARD
  |      YES, bypassable    --> NEEDS REVIEW
  |      NO                 --> Continue
  |
  +--> Exploitation requires unrealistic conditions? (admin, MitM, physical)
  |      YES --> DISCARD
  |
  +--> TRUE POSITIVE -- proceed to validation
```

## Triage output

| # | Rule ID | File:Line | Verdict | Reason |
|---|---------|-----------|---------|--------|

Verdicts: `TRUE POSITIVE` | `FALSE POSITIVE` | `NEEDS REVIEW`

Every FALSE POSITIVE must have a one-line reason.
