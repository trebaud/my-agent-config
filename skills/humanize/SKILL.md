---
name: humanize
description: Strip LLM writing tics from prose so it reads like a person wrote it. Use whenever the user asks to humanize, de-slop, de-AI, or naturalize text, says something "sounds like AI" or "sounds like ChatGPT/Claude", or asks for an editing pass on emails, docs, blog posts, READMEs, commit messages, or code comments. Also apply as a final pass on any longform prose Claude writes, even if the user didn't explicitly ask.
---

# Humanize

An edit pass that removes stock LLM phrasing ("slop"). Preserve meaning and the author's voice; change only how it's said.

## Workflow

1. **Get the text.** Draft it first if asked to write, or take the user's text as-is.
2. **Scan.** Run `python scripts/slopcheck.py <file>` (or pipe text via stdin) to flag phrase-level tics deterministically, then read for the structural tics below — the script can't catch those.
3. **Rewrite** every hit using the rules below. Edit sentences, don't paraphrase whole paragraphs.
4. **Verify.** Re-run the script until it reports zero hits, then reread once: if any sentence sounds like a keynote or LinkedIn post, redo it.

## Phrase-level tics

**Delete on sight** (stock phrases): you're absolutely right · that's a great/excellent question · let me be clear · it's worth noting · it bears mentioning · that said · at the end of the day · in conclusion · in other words · here's the thing · here's the kicker · here's where it gets interesting · the key insight · load-bearing · seam · honest take · smoking gun · belt-and-suspenders · now I have the full picture · testament to · delve · crucially · game-changer · despite these/its challenges · imagine a world where · think of it as

**Cut filler intensifiers** (they add nothing): actually, genuinely, really, simply, clearly, honestly, quite, truly, significantly, deeply, quietly, fundamentally, remarkably, arguably, certainly

**Verbose → plain:**
- utilize / leverage / harness / streamline → use / simplify
- in order to → to
- due to the fact that → because
- the majority of → most
- a large number of → many
- prior to → before
- the fact that X is → X is
- in terms of X → restructure the sentence
- serves as / stands as / represents (as a copula dodge) → is / are

**Hype adjectives & grandiose nouns** (seamless, robust, nuanced, intricate, elegant, comprehensive, powerful, tapestry, landscape, paradigm, synergy, ecosystem): keep at most one per passage, only if earned by evidence in the text. Never stack two.

**Name the source.** "Experts argue," "industry reports suggest," "observers have noted" — if you can't name who, cut the claim or the attribution.

## Structural tics

- "It's not just X — it's Y" contrast scaffolding, including "Not X. Not Y. Just Z." countdowns. State the point directly.
- Self-posed rhetorical Q&A ("The result? Devastating."). Just state the result.
- Rule-of-three everywhere ("fast, simple, and reliable"), including back-to-back tricolons and anaphora (repeating the same sentence opener). Break the pattern or pick the one that matters.
- Em-dash overuse. Max one per paragraph; prefer a period or comma.
- Unicode decoration — smart/curly quotes, → arrows. Use straight quotes and -> if you need the symbol at all.
- Openers that restate the question; closers that summarize what was just said. Cut both.
- Bold-label bullets that restate their own sentence, or a numbered list dressed as prose ("The first... The second..."). Merge into prose or drop the label.
- Uniform paragraph and sentence length. Vary it: one short sentence after two long ones.
- Gerund fragments tacked on for false significance ("...highlighting its importance") or standing alone as sentences ("Fixing bugs. Shipping features."). Cut or fold into the main clause.
- False ranges ("from X to Y") where there's no real spectrum between them. Name the two things plainly.
- Invented compound labels ("the supervision paradox," "workload creep") standing in for an actual argument. Explain the mechanism instead of naming it.
- One metaphor beaten across the whole piece, the same point restated in five different framings, or a paragraph repeated verbatim. Say it once and move on.

## Rewrite principles

- Short declarative sentences by default; vary rhythm after that.
- Concrete over abstract: name the thing, not its category.
- If a word survives deletion with no loss of meaning, delete it.
- Aim for roughly Flesch-Kincaid 60–70 readability unless the register demands otherwise (legal, academic).
- When editing someone else's text, match their voice. Don't impose a new one.

## Example

Before: "Honestly, that's a great question — the parser is actually quite robust. We utilize the tokenizer in order to handle the majority of edge cases, which is a testament to the seamless architecture."

After: "The parser holds up. The tokenizer handles most edge cases."
