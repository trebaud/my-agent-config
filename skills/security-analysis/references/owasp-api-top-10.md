# OWASP API Security Top 10 (2023) -- Quick Reference

## Classification table

| ID | Vulnerability | Key signal in code |
|----|---------------|--------------------|
| API1 | Broken Object Level Authorization | Object ID from request used without ownership check |
| API2 | Broken Authentication | Weak secrets, no rate limit on login, token mismanagement |
| API3 | Broken Property Level Authorization | `req.body` spread into DB update, sensitive fields in response |
| API4 | Unrestricted Resource Consumption | Unbounded queries, no pagination, no rate limit |
| API5 | Broken Function Level Authorization | Missing role/RBAC check on privileged endpoints |
| API6 | Unrestricted Business Flows | Financial ops without velocity limits, race conditions |
| API7 | SSRF | User input in outbound URL construction |
| API8 | Security Misconfiguration | `CORS: *`, verbose errors, debug mode, creds in logs |
| API9 | Improper Inventory Management | Deprecated/undocumented/test endpoints still live |
| API10 | Unsafe API Consumption | External API response trusted without validation |

## Triage questions per class

**API1 (BOLA):** Does the endpoint verify the authenticated user owns the requested object? Can changing the ID return another user's data?

**API2 (Auth):** Rate limited? Passwords hashed (bcrypt/argon2)? JWT secret strong + rotated? Tokens expire?

**API3 (Property-level authz):** Are writable fields explicitly allowlisted? Are responses filtered to exclude internal fields (roles, hashes, internal IDs)?

**API4 (Resource consumption):** Are list endpoints paginated with a max limit? Are expensive operations throttled?

**API5 (Function-level authz):** Is RBAC enforced consistently across all admin/privileged routes? Any endpoint missing middleware?

**API6 (Business flows):** Are financial operations atomic (transactions)? Velocity/fraud checks in place? Idempotency keys used?

**API7 (SSRF):** Is user input used to construct URLs? Is there an allowlist for outbound hosts? Are internal IPs blocked?

**API8 (Misconfig):** Does CORS restrict origins on sensitive endpoints? Are stack traces suppressed in production? Credentials in plaintext logs?

**API9 (Inventory):** Are deprecated endpoints removed or gated? Any `/debug`, `/test`, `/internal` routes reachable?

**API10 (Unsafe consumption):** Are external API responses validated against a schema before use? Are amounts/statuses cross-checked against internal records?
