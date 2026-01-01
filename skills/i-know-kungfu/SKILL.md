---
name: i-know-kungfu
description: >-
  Helps a human actually learn something — a concept, a codebase, a paper, a topic — using an
  evidence-based active-learning loop (retrieval practice, predict-then-reveal, spaced repetition,
  Feynman teach-back, desirable difficulty) drawn from cognitive science. Runs as a live tutor in the
  session AND leaves behind a study kit whose main deliverable is a set of linked, self-contained HTML
  pages (a small learning site): an overview hub with a concept-map graph and Bloom progress, one
  active-recall lesson page per concept chunk, a flashcards page, a predict-then-reveal self-quiz, and a
  spaced-review plan — plus a portable mental-model brief. Use when the user wants to learn, understand deeply,
  study, master, or be onboarded to something — not just get an answer. Triggers: "teach me X",
  "help me learn/understand/master X", "I want to really get X", "quiz me on X", "tutor me through
  this paper/codebase/concept", "make me a study plan for X", "I know kung fu".
---

# I Know Kung Fu

Help a human retain something — a concept, a codebase, a paper, a topic. People remember what they recall,
generate, and revisit; reading it once doesn't stick. So run an evidence-based learning loop instead of
explaining at the learner, and leave behind a study kit. Learner-facing sibling of `repo-visualizer`; reuses
its HTML component library for the pages.

## The creed (these are what make it learning, not info-dumping)

1. **Test before you tell.** Open every chunk with a question or prediction, never the answer.
2. **Make them generate.** The learner produces the explanation; you correct it.
3. **Never accept "I get it."** Prove it with retrieval — demand a teach-back.
4. **Keep it desirably hard.** Difficulty at the edge of ability: a struggle that almost succeeds.
5. **Connect before you add.** Anchor each chunk to something they already know.
6. **Chunk, don't dump.** 5–9 ideas at a time; compress the rest into the map.
7. **Interleave and space.** Mix concepts; push reviews into the future.
8. **Surface, then close gaps.** Use teach-back to find what's broken, then target only that.
9. **Calibrate honestly.** Predict performance, then show the gap between felt and real mastery.
10. **End on transfer.** Not done until the idea is applied to a novel problem.

Why each rule works + how to apply it: [references/cognitive-science.md](references/cognitive-science.md). Read it before a session.

## Modes

- **Concept / topic** — "teach me how a bloom filter works."
- **Codebase** — "onboard me to this repo." Compose with `repo-visualizer` for the structural map, then teach
  from it using the six code-reading techniques in [references/reading-code.md](references/reading-code.md):
  (1) start at the entry point, follow the flow outward; (2) read happy-path tests for the contract; (3) follow
  the core data object; (4) ignore infra noise on the first pass; (5) inspect one failure path (where security
  bugs hide); (6) compress the logic to one sentence — that sentence is the teach-back gate.
- **Paper** — "tutor me through this paper" + a file/link. Extract claim / method / evidence / limitations.
- **Review session** — "quiz me on X" (re-invoked later). Skip straight to retrieval + spacing on prior material.

If the subject or goal is ambiguous, ask one question first. Never open by explaining.

## Workflow

**0. Calibrate.** Pin the subject, goal, and target Bloom level (recall? understand? apply/build?), current
level, and time budget. Then offer a pretest — don't force it: *"Want 5 quick guesses first (best for
retention), or skip and I'll just build it?"* Guessing before learning improves encoding even when wrong. If
skipped, take a one-line self-rating ("new / some exposure / rusty") and move on. The pretest is never a gate
to the deliverable.

**1. Map the terrain.** Read the real source (never infer from a title). Extract the core mental model (one
paragraph), the 5–9 key chunks, and the prerequisite graph. Anchor each chunk to prior knowledge by analogy.
Flag the **linchpin** — the idea everything hangs on. This becomes the concept map.

**2. Sequence.** Order chunks by prerequisite and by ZPD (just beyond current ability). Novice →
worked-example-first; advanced → productive-failure-first (struggle, then instruct). Defer the tail to a later
spaced session; don't cram.

**3. Run the loop (per chunk, in order).**
1. **Curiosity gap** — pose the question before any explanation.
2. **Predict** — learner commits a guess; wait for it (the gap is where encoding happens).
3. **Reveal** — show the answer; for a procedure, a fully worked example.
4. **Fade** — partial example, then a solo problem.
5. **Retrieve** — quiz notes-closed; produce, don't pick.
6. **Elaborate** — "why does it hold? where does it break? how does it link to [earlier chunk]?"
7. **Teach-back** — they explain it simply; loop back to only the broken parts.
8. **Interleave** — pull a question from an earlier chunk.

Stay per-chunk until the teach-back is clean.

**4. Spaced reinforcement.** Generate retrieval cards (Q/A that force production, not facts to re-read) and a
spacing schedule (day 1, 3, 7, 16; one review after sleep). Surface both in the brief and `review.html`. No
Anki export — the learner re-invokes in review mode.

**5. Transfer & calibrate.** Apply the idea to a novel/own problem. Have the learner predict their mastery,
take a mixed quiz across all chunks, and compare predicted vs actual. Schedule the gaps; don't paper over them.

## Deliverable: a set of linked HTML pages

A small static learning site built from `assets/template.html` — dark-theme, offline, dependency-free. The
pages **run the loop** so the learner self-tutors; they are not passive reference. Scale to the subject (a tiny
topic may be one page):

1. **`index.html`** — hub: core model, the **concept map** (hover-to-isolate prerequisites, linchpin amber),
   Bloom progress ladder, and a table-of-contents to the other pages.
2. **`lesson-N.html`** (one per chunk) — runs the loop statically: curiosity question → predict-then-reveal →
   worked example → flashcards → teach-back + "say it in one sentence" box. Prev/next pager in prerequisite order.
3. **`flashcards.html`** — full interleaved flip-card deck.
4. **`quiz.html`** — mixed predict-then-reveal self-quiz (the calibration check).
5. **`review.html`** — forgetting-curve + spacing schedule and "where you are / what's next."

Also output a short **mental-model brief (markdown)**: core model, chunk list, prerequisite graph, analogies,
cards, schedule.

**Building:** copy `template.html` per page; mark the current nav link `class="link on"`. The
`<!-- COMPONENTS LIBRARY -->` comment holds copy-paste markup for every component (concept map, Bloom ladder,
flip cards, predict-reveal quiz, forgetting curve, glossary, table-of-contents, pager, compression box). Link
pages with relative hrefs. Every concept-map node/edge must map to a real idea. Keep each page 100%
self-contained — hand-built inline SVG, no Mermaid/D3/CDN/fonts; opens by double-click.

**Output:** a folder beside the subject (repo root or `./local/<subject>-learn/`). Write `index.html` + the
set, `open index.html`, and tell the user the path and how to run a review.

## Quality bar
- **Effortful.** If a summary would give the same value, it failed. Every chunk gated by retrieval/generation.
- **Grounded.** Model, map, and cards trace to the real source. A map that doesn't match is worse than none.
- **Honest calibration.** Surface the felt-vs-actual gap; don't congratulate.
- **Right altitude.** 5–9 chunks; defer the rest.
- **Adaptive.** Worked examples for novices, productive failure for the advanced.
- **Self-contained.** Offline, no external deps, responsive, dark theme.

## Anti-patterns
- ❌ Info-dumping a summary and asking "make sense?" — the canonical failure.
- ❌ Letting the learner re-read instead of retrieve.
- ❌ Accepting "I get it" without a teach-back or closed-notes quiz.
- ❌ Frictionless = no durable learning.
- ❌ Facts taught in isolation, unconnected to prior knowledge.
- ❌ One session, no spacing.
- ❌ Revealing before the learner has predicted.
- ❌ A concept map that doesn't match the source, or any CDN dependency.
