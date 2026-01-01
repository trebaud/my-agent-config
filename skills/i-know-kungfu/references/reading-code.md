# Reading code to learn a codebase

Used by the **codebase mode** of `i-know-kungfu`. As more code gets written by AI, reading code well matters
more than writing it — you spend most of your time understanding code you (or a model) didn't write. Reading
top-to-bottom, file by file, doesn't scale. These six repeatable techniques replace that with a directed,
graph-style read.

Use them to drive Phase 1 (Map the terrain) and to write the lesson pages and retrieval questions. They are
not passive reading steps — each one produces a prediction, a trace, or a one-sentence summary the learner
must generate.

---

## 1. Identify the entry point
Don't read files sequentially. Find the exact line where an external request *enters* the system — an
`app.post(...)` route, a CLI command handler, a queue consumer, a cron entry, an event listener — and follow
the logical flow outward from there, like traversing a graph.

- **How:** grep for route/handler registrations, `main`/`index`, `bin` entries, framework bootstrap, worker
  registration. Pick the one entry point that matters for the goal and start there.
- **In the lesson:** the curiosity-gap opener — "a request hits `POST /x`; predict the next three hops before
  we trace it." The concept map's left/top nodes are the entry points.

## 2. Analyze tests first
Before reading the implementation, read the **happy-path** test cases. Tests state the *contract* — what goes
in, what comes out — so you get the expected behaviour before you wrestle with how it's achieved.

- **How:** find the test file for the module, read the most representative success-case test. Note the inputs
  constructed and the assertions made. That is the spec in miniature.
- **In the lesson:** use the test's inputs/outputs as the **predict-then-reveal** material — "given this
  input, what does the test assert it returns?" Reveal the assertion.

## 3. Follow the data
Don't try to understand every function. Pick the **core variable** — the `user` object, the `order`, the
request payload — and trace its lifecycle and transformations through the system: created where, mutated
where, validated where, persisted where.

- **How:** trace one object from construction to its final sink. Note each transformation. Ignore functions
  that don't touch it.
- **In the lesson:** a "follow the data" trace is the worked example; the retrieval card asks the learner to
  list the transformations in order from memory. This is the **sequence-diagram** material.

## 4. Filter the noise
On the first pass, **ignore infrastructure** — middleware, rate limiters, logging, metrics, retry wrappers,
DI plumbing. Read only the functional flow. Bring the infra back in only if it's directly relevant to the
specific bug or feature being investigated.

- **How:** when tracing, skip over cross-cutting wrappers; note them as "infra — revisit if relevant" and
  keep following the core path.
- **In the lesson:** keep the concept map and flow at the *functional* altitude; relegate infra to the
  glossary or a "revisit later" note. This is the chunking / cognitive-load discipline applied to reading.

## 5. Inspect failure paths
Once the success flow is clear, examine **exactly one** failure path. This is where the most instructive — and
most security-relevant — behaviour hides:
- **User-enumeration bugs:** error messages that differ depending on whether a user exists.
- **Timing attacks:** response times that vary with secret-dependent work.
- **Error leakage:** stack traces, internal IDs, or differing status codes that reveal structure.

- **How:** pick one error branch (auth failure, not-found, validation error) and trace what the system returns
  and how long it takes. Ask: could an attacker learn something from the difference between success and this
  failure?
- **In the lesson:** the failure path is the **transfer / edge-case** task — "predict what `POST /login`
  returns for a non-existent user vs a wrong password; is that a leak?" Inspecting one failure path is the
  productive-difficulty step that takes the learner from "understand" to "analyze" on Bloom.

## 6. Synthesize into a sentence
If you cannot summarize the core logic of a piece of code in **one concise sentence**, your understanding is
incomplete. The act of compression forces you to extract the essential purpose and discard the incidental.

- **How:** after the trace, write one sentence: "This module \<does X\> by \<means Y\> so that \<outcome Z\>."
  If you can't, you've missed something — go back.
- **In the lesson:** this *is* the teach-back gate. The lesson page's "say it in one sentence" compression box
  holds the learner's sentence; a chunk isn't done until the sentence is clean. It's the Feynman technique in
  one line.

---

## The order, and how it maps to the loop

Apply them roughly in sequence — they build on each other:

| # | Technique | Loop step it powers | Page element |
|---|---|---|---|
| 1 | Entry point | curiosity gap | concept-map entry nodes |
| 2 | Tests first | predict-then-reveal (the contract) | predict-reveal block |
| 3 | Follow the data | worked example / retrieve | flow + sequence trace, flashcards |
| 4 | Filter the noise | chunk, don't dump | functional-altitude concept map |
| 5 | Failure path | transfer / analyze | edge-case quiz item |
| 6 | One sentence | Feynman teach-back | compression box (the gate) |

The discipline: **read outward from an entry point, learn the contract from tests, follow one object, ignore
the plumbing, probe one failure, and compress to a sentence.** A learner who can do all six on a flow
understands it — and can prove it.
