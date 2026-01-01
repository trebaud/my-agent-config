# Severity classification

## Decision matrix

```
1. Auth required?    No → Critical/High  |  Low-priv → High/Medium  |  Admin-only → Medium/Low
2. Victim interaction? No → +1 tier
3. Impact?           RCE/full ATO/mass exfil → Critical  |  Other-user data/admin access → High  |  Limited → Medium
4. Scope change?     SSRF→internal, XSS→ATO → upgrade to Critical/High
```

## Severity thresholds

| Severity | Threshold |
|----------|-----------|
| **Critical** | Unauthenticated attacker achieves full compromise, no interaction required |
| **High** | Serious unauthorized access, but authentication or social engineering required |
| **Medium** | Exploitable, but limited scope/impact or requires victim interaction |
| **Low** | Not reported unless chains to Medium+ |

## Confidence levels

| Confidence | Criteria |
|------------|---------|
| **Confirmed** | Full input-to-sink trace verified, no defense neutralizes it |
| **Probable** | Path clear, but a runtime condition could block it |
| **Theoretical** | Pattern matches, needs runtime verification |

Confirmed Medium outranks Theoretical High for remediation priority.
