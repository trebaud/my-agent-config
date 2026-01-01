---
name: rfc-generator
description: Creates comprehensive RFC (Request for Comments) documents for new features. Use when the user wants to write an RFC, propose a new feature for team review, or document a technical decision. Guides the user through interactive questioning to flesh out the document.
allowed-tools: Read, Grep, Glob, Write, AskUserQuestion
---

# RFC Document Generator

Generate comprehensive RFC documents for features by gathering requirements through structured questioning.

## Instructions

When this skill is invoked, follow these steps:

### Step 1: Executive Summary & Authorship

Use the AskUserQuestion tool to understand the feature at a high level:

1. **RFC Title**: What is the title of this RFC?
2. **Authors**: Who are the authors? (GitHub usernames with @)
3. **Executive Summary**: Provide a brief 1-2 sentence summary of what you're proposing

### Step 2: Motivation & Problem Definition

Use AskUserQuestion to understand the motivation:

1. **Problem Statement**: What specific problem are you trying to solve?
2. **Current State**: How does the system currently handle this? What are the pain points?
3. **Why Now**: Why is this important to solve now? What's the impact of not solving it?
4. **Who Benefits**: Who are the stakeholders that will benefit from this change?

### Step 3: Proposed Implementation

Gather technical implementation details:

1. **High-Level Approach**: What is the proposed solution at a high level?
2. **Key Components**: What are the main components or modules involved?
3. **Data Model Changes**: Any database/schema changes needed?
4. **API Changes**: New endpoints or modifications to existing ones?
5. **Code Examples**: Are there any interface contracts or code examples to include?

If the user seems uncertain, offer to explore the codebase to suggest implementation approaches.

### Step 4: Metrics & Dashboards

Ask about measurability:

1. **Success Metrics**: How will you measure if this implementation is successful?
2. **Key Metrics**: What metrics should be tracked? (latency, throughput, error rates, etc.)
3. **Monitoring**: What dashboards or alerts should be created?

### Step 5: Alternatives Analysis

Explore alternative approaches:

1. **Alternative 1**: What is another way to achieve the same outcome?
2. **Alternative 2**: Any other approaches considered?
3. **Comparison**: Why is the proposed solution better than the alternatives?

Offer options like:
- "Do nothing" - Keep the current state
- "Simpler approach" - A less comprehensive but faster solution
- "More comprehensive" - A fuller solution that takes more effort

### Step 6: Drawbacks & Risks

Identify potential issues:

1. **Technical Drawbacks**: What are the technical downsides of this approach?
2. **Operational Risks**: What could go wrong in production?
3. **Migration Risks**: Are there data migration concerns?
4. **Reversibility**: How easy is it to roll back if something goes wrong?

### Step 7: Security Implications

**CRITICAL SECTION** - Ask specifically about security:

1. **Attack Vectors**: Could this feature be exploited by malicious actors? How?
2. **Data Sensitivity**: Does this involve sensitive data (PII, financial, credentials)?
3. **Authentication/Authorization**: Are there any auth changes? Who can access this?
4. **Input Validation**: What user inputs need validation?
5. **Compliance**: Are there any compliance implications (GDPR, PCI, etc.)?

If the user is unsure, suggest common security considerations:
- SQL/NoSQL injection risks
- XSS vulnerabilities
- Rate limiting needs
- Audit logging requirements
- Encryption at rest/in transit

### Step 8: Potential Impact & Dependencies

Explore broader implications:

1. **Affected Systems**: What other systems or services will be affected?
2. **Team Dependencies**: Which teams need to be consulted or involved?
3. **External Dependencies**: Any third-party services or libraries involved?
4. **Breaking Changes**: Will this introduce any breaking changes?
5. **Performance Impact**: Could this affect system performance? How?

### Step 9: Unresolved Questions

1. **Open Questions**: What parts of this proposal still need to be figured out?
2. **Decisions Needed**: What decisions are pending from other stakeholders?
3. **Unknowns**: What are the known unknowns?

### Step 10: Conclusion

1. **Summary**: Why is this the right decision to make now?
2. **Next Steps**: What are the immediate next steps after RFC approval?

### Step 11: Generate RFC Document

After gathering all information, generate the RFC document using the template in @references/RFC_TEMPLATE.md


## Guidelines for Questioning

1. **Be Adaptive**: Skip questions that aren't relevant based on previous answers
2. **Suggest Options**: When asking about technical or design choices, provide common options as suggestions
3. **Security First**: Always probe security implications even if the user doesn't mention them
4. **Challenge Assumptions**: Ask "why" to help the user think through their reasoning
5. **Limit Questions**: Group related questions together (max 4 questions per AskUserQuestion call)
6. **Iterate**: If answers are vague, ask follow-up questions for clarity
7. **Provide Examples**: When discussing alternatives or risks, suggest examples from common patterns
8. **Keep Context**: Reference previous answers to build a coherent RFC

## Example Question Flow

**First batch:**
- "What is the title of this RFC?"
- "Who are the authors? (Please provide GitHub usernames with @)"
- "In 1-2 sentences, what are you proposing?"

**Second batch:**
- "What specific problem does this feature solve?"
- "How does the system currently handle this? What are the pain points?"

**Third batch:**
- "What is your proposed solution at a high level?"
- "What are the main components or modules that will be affected?"

Continue based on the feature type and user responses...

## Output

After gathering all necessary information:

1. Confirm the output location with the user (default: `./RFC-{title}.md` in current directory)
2. Check if a file already exists at that location
3. Write the RFC document
4. Summarize what was created and suggest next steps (e.g., share with team for review, create implementation tasks)
