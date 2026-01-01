# Severity classification

## Decision matrix

```
1. Auth required?      No -> Critical/High  |  Low-priv -> High/Medium  |  Admin-only -> Medium/Low
2. Victim interaction? No -> +1 tier
3. Impact?             RCE/full ATO/mass exfil -> Critical  |  Other-user data/admin access -> High  |  Limited -> Medium
4. Scope change?       SSRF->internal, XSS->ATO -> upgrade to Critical/High
```

## Business impact adjustment

Technical severity is the starting point. Business impact is the final word.

| Technical severity | Business impact | Final severity |
|--------------------|-----------------|----------------|
| Critical | HIGH | Critical |
| Critical | MODERATE | High |
| Critical | LOW/NONE | Medium/Low |
| High | HIGH | High |
| High | MODERATE | High |
| High | LOW/NONE | Medium/Low |
| Medium | HIGH | High |
| Medium | MODERATE | Medium |
| Medium | LOW/NONE | Low |

**Reality checks before assigning business impact:**
- Can attacker gain financially, or only affect their own account?
- Does this cause real operational disruption, or just edge-case inconsistency?
- Would users actually notice? Would it page oncall?
- Can it be automated/scripted at scale?

## Confidence levels

| Confidence | Criteria |
|------------|---------|
| **Confirmed** | Full input-to-sink trace verified, no defense neutralizes it |
| **Probable** | Path clear, but a runtime condition could block it |
| **Theoretical** | Pattern matches, needs runtime verification |

Confirmed Medium outranks Theoretical High for remediation priority.

## Common overstatements

Watch for inflated claims -- always verify with code evidence:
- "Financial loss" -- often only affects attacker's own account
- "Data breach" -- often non-sensitive metadata disclosure
- "Account takeover" -- may require unrealistic attack conditions
- "Race condition" -- may have no meaningful outcome
