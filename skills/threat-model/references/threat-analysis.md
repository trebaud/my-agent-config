# Threat Identification — Failure Modes and Boundaries

You know STRIDE. This file covers what goes wrong when applying it, and where the boundaries actually sit.

## Where trust boundaries actually are

A trust boundary is where the *set of things you can assume* changes. Not where the network changes.

- **Same process, different privilege is a boundary.** In a monolith, the boundary sits at the middleware that attaches the session — everything upstream is attacker-controlled, everything downstream assumes an authenticated principal. Draw it there, not at the load balancer.
- **Two services inside one VPC with no mTLS share one boundary, not two.** If service A can impersonate service B by sending a packet, they are the same trust zone. Modeling them separately invents controls that do not exist.
- **The database is a boundary only if something else can write to it.** A store only your service touches is inside your zone. A store an ETL job, an admin console, or a replica writes to is a separate zone.
- **The deploy path is a boundary you will forget.** CI credentials, a dependency's postinstall, and a container base image all cross into production without touching a request path.

## Failure modes

These are how threat models come out wrong. Check yourself against each before writing the file.

**Threats that are really missing controls.** "No rate limiting" is not a threat; it is the absence of a mitigation for one. The threat is "an attacker enumerates valid coupon codes at 10k/min". If you cannot name who benefits and what they get, it is not a threat row.

**The OWASP dump.** A table of SQLi, XSS, CSRF, SSRF generated without reading the code, one per category, evenly distributed. Real systems have lumpy threat distributions — six threats on the payment callback and none on the health endpoint. If every component has a similar number of threats, the model was generated, not derived.

**Every cell must be filled.** The applicability matrix bounds what is *possible*, not what is *required*. An element with no plausible threat in a category gets no row. Padding to look thorough destroys the signal in the table.

**Mitigations asserted from the design, not the code.** "Mitigated by input validation" where the validator runs on a different route, or the middleware is registered after the handler, or the check is client-side. Every control claim needs a file and line you actually read.

**Boundaries drawn around the code you were shown.** The model covers the service in the repo and silently treats every dependency, queue consumer, and cron job as trusted. State them as out of scope explicitly, or model them.

**Single-step thinking.** Real incidents chain: an info-disclosure that leaks an internal ID, plus an IDOR that accepts it, plus a webhook with no replay protection. Each is Low alone. Look for pairs before finalizing severities.

**Stale diagram.** The model describes the intended architecture. The code has a second entry point added last quarter. Enumerate routes and handlers mechanically rather than trusting a README.

## Applicability bounds

Only to stop impossible rows — a data flow cannot repudiate, an external entity cannot be privilege-escalated in your system.

| Element | S | T | R | I | D | E |
|---------|---|---|---|---|---|---|
| External entity | ✓ | | ✓ | | | |
| Process | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Data store | | ✓ | ✓ | ✓ | ✓ | |
| Data flow | | ✓ | | ✓ | ✓ | |

## Scoring

Likelihood × impact, both Low/Med/High. High×High is Critical; Low×Low is Low; the rest fall out.

Score likelihood on **attacker cost**, not on "has it happened here" — a system that has never been attacked scores the same as one that has. Score impact on **blast radius and recoverability**, not on the sensitivity of the component. A leak of one user's email from the auth service is lower impact than a leak of every user's balance from a reporting endpoint.

The release-blocking threshold is the team's call, not this skill's. Ask, or state the assumption in the model.

## Beyond STRIDE

STRIDE covers technical categories, not business logic. After the checklist pass:

- What does this system do that is worth money, and how would you get it for free?
- What ordering, timing, or concurrency assumption does the code make that an attacker controls? (double-submit, TOCTOU, retry storms, webhook replay)
- On partial failure, is state left half-committed in an exploitable way?
- Which two Low findings chain into a High?
- What does a compromised dependency, CI runner, or employee laptop get you?

MITRE ATT&CK for realistic technique chains; CAPEC for attack patterns per weakness.
